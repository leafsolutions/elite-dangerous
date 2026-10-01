import random
from pathlib import Path

import pytest

from majordomo.companion import Companion, VirtualClock, replay
from majordomo.director import Director
from majordomo.events import GameEvent, Priority, parse_timestamp
from majordomo.normaliser import Mode, Normaliser
from majordomo.persona import Persona, Renderer, fact_guard
from majordomo.sources import JournalWatcher, read_recording
from majordomo.status import Flags, StatusTracker
from majordomo.voice import ConsoleVoice

ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ROOT / "prototypes" / "majordomo" / "personas"
SAMPLE = ROOT / "samples" / "sample_session.log"


class FakeClock:
    def __init__(self, t: float = 1000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def ev(kind, p=Priority.P1, **facts):
    return GameEvent(kind, p, facts)


# ------------------------------------------------------------------ status flags
def test_status_first_snapshot_is_baseline_then_edges():
    tr = StatusTracker()
    assert tr.update({"Flags": int(Flags.SUPERCRUISE)}) == []
    changes = tr.update({"Flags": int(Flags.SUPERCRUISE | Flags.LOW_FUEL)})
    assert [(c.flag, c.rising) for c in changes] == [(Flags.LOW_FUEL, True)]
    changes = tr.update({"Flags": 0})
    assert {(c.flag, c.rising) for c in changes} == {
        (Flags.SUPERCRUISE, False), (Flags.LOW_FUEL, False)}


# ------------------------------------------------------------------- normaliser
def test_fsd_jump_is_normalised():
    n = Normaliser()
    [e] = n.process({"event": "FSDJump", "StarSystem": "Deciat", "JumpDist": 14.531,
                     "timestamp": "2026-09-27T20:00:00Z"})
    assert e.kind == "fsd_jump" and e.facts == {"system": "Deciat", "distance_ly": 14.5}
    assert n.state.system == "Deciat"


def test_hull_damage_announces_each_threshold_once_until_repaired():
    n = Normaliser()
    hits = lambda h: n.process({"event": "HullDamage", "Health": h, "PlayerPilot": True})
    assert [e.facts["hull_pct"] for e in hits(0.70)] == [70]
    assert hits(0.69) == []
    assert [e.facts["hull_pct"] for e in hits(0.20)] == [20]  # crosses 50 and 25: one line
    n.process({"event": "RepairAll"})
    assert len(hits(0.70)) == 1


def test_combat_mode_from_music_emits_start_and_end():
    n = Normaliser()
    kinds = [e.kind for e in n.process({"event": "Music", "MusicTrack": "Combat_Dogfight"})]
    assert kinds == ["combat_start"] and n.state.mode == Mode.COMBAT
    kinds = [e.kind for e in n.process({"event": "Music", "MusicTrack": "Exploration"})]
    assert kinds == ["combat_end"]


def test_combat_lasts_from_interdiction_until_danger_clears():
    n = Normaliser()
    n.process({"event": "Status", "Flags": int(Flags.SUPERCRUISE)})
    n.process({"event": "Status", "Flags": int(Flags.SUPERCRUISE | Flags.BEING_INTERDICTED
                                               | Flags.IN_DANGER)})
    assert n.state.mode == Mode.COMBAT
    # pulled out: the interdiction flag drops, but we are still in danger
    kinds = [e.kind for e in n.process({"event": "Status", "Flags": int(Flags.IN_DANGER)})]
    assert "combat_end" not in kinds and n.state.mode == Mode.COMBAT
    kinds = [e.kind for e in n.process({"event": "Status", "Flags": 0})]
    assert kinds == ["combat_end"]


def test_renderer_does_not_repeat_until_all_lines_used():
    p = Persona(id="x", name="X", archetype="t", lines={"idle": ["a", "b", "c"]})
    r = Renderer(p, random.Random(3))
    said = [r.render(ev("idle", Priority.P2), Mode.SUPERCRUISE) for _ in range(9)]
    assert all(x != y for x, y in zip(said, said[1:]))
    assert sorted(said[:3]) == ["a", "b", "c"]


# --------------------------------------------------------------------- director
def test_priority_order_and_cooldown():
    clock = FakeClock()
    d = Director(clock=clock)
    d.offer(ev("fsd_jump", system="A"), Mode.SUPERCRUISE)
    d.offer(ev("hull_damage", Priority.P0, hull_pct=40), Mode.SUPERCRUISE)
    first = d.next(Mode.SUPERCRUISE)
    assert first.kind == "hull_damage"
    d.mark_spoken(first)
    jump = d.next(Mode.SUPERCRUISE)
    d.mark_spoken(jump)
    assert d.offer(ev("fsd_jump", system="B"), Mode.SUPERCRUISE).reason == "cooldown"
    clock.t += 60
    assert d.offer(ev("fsd_jump", system="C"), Mode.SUPERCRUISE).accepted


def test_combat_drops_chatter_and_nonessentials_but_not_critical():
    d = Director(clock=FakeClock())
    assert not d.offer(ev("idle", Priority.P2), Mode.COMBAT).accepted
    assert not d.offer(ev("docked", station="X"), Mode.COMBAT).accepted
    assert d.offer(ev("shields_down", Priority.P0), Mode.COMBAT).accepted


def test_stale_lines_are_dropped():
    clock = FakeClock()
    d = Director(clock=clock)
    d.offer(ev("docked", station="X"), Mode.NORMAL)
    clock.t += 30
    assert d.next(Mode.NORMAL) is None


def test_mute_keeps_critical():
    d = Director(clock=FakeClock())
    d.mute(300)
    assert d.offer(ev("fsd_jump", system="A"), Mode.SUPERCRUISE).reason == "muted"
    assert d.offer(ev("low_fuel", Priority.P0), Mode.SUPERCRUISE).accepted


def test_chatter_needs_quiet_mode_silence_and_budget():
    clock = FakeClock()
    d = Director(chattiness=0.5, clock=clock, min_silence_before_chatter=25)
    assert not d.chatter_slot(Mode.SUPERCRUISE)  # not silent long enough
    clock.t += 30
    assert not d.chatter_slot(Mode.SUPERCRUISE)  # budget starts at chattiness (0.5)
    clock.t += 70
    assert not d.chatter_slot(Mode.DOCKED)  # not a quiet window
    assert d.chatter_slot(Mode.SUPERCRUISE)
    d.mark_spoken(ev("idle", Priority.P2))
    clock.t += 30
    assert not d.chatter_slot(Mode.SUPERCRUISE)  # budget spent, refills slowly
    clock.t += 200
    assert d.chatter_slot(Mode.SUPERCRUISE)


def test_preemption_signal():
    d = Director(clock=FakeClock())
    d.offer(ev("overheating", Priority.P0), Mode.NORMAL)
    assert d.should_preempt(Priority.P2)
    assert not d.should_preempt(Priority.P0)


# ---------------------------------------------------------------------- persona
@pytest.mark.parametrize("path", sorted(PERSONAS.glob("*.yaml")), ids=lambda p: p.stem)
def test_bundled_personas_are_valid(path):
    assert Persona.load(path).validate() == []


def test_validation_catches_missing_required_fact():
    p = Persona(id="x", name="X", archetype="t", lines={"hull_damage": ["We're hit!"]})
    assert any("hull_pct" in problem for problem in p.validate())


def test_renderer_keeps_facts_and_skips_lines_with_missing_optional_facts():
    p = Persona(id="x", name="X", archetype="t", lines={
        "session_start": ["Welcome aboard the {ship}."],
        "hull_damage": ["Ouch. Hull {hull_pct}%."],
    })
    r = Renderer(p, random.Random(1))
    assert r.render(ev("hull_damage", Priority.P0, hull_pct=42), Mode.NORMAL) == "Ouch. Hull 42%."
    # no ship name in this LoadGame: fall back to the neutral line instead of "{ship}"
    assert r.render(ev("session_start"), Mode.NORMAL) == "Systems online, Commander."


def test_combat_lines_override_in_combat():
    pip = Persona.load(PERSONAS / "pip.yaml")
    r = Renderer(pip, random.Random(0))
    calm = r.render(ev("hull_damage", Priority.P0, hull_pct=46), Mode.NORMAL)
    cold = r.render(ev("hull_damage", Priority.P0, hull_pct=46), Mode.COMBAT)
    assert "Is that bad" in calm and "Is that bad" not in cold and "46" in cold


def test_fact_guard():
    e = ev("fsd_jump", system="Deciat")
    assert fact_guard("Welcome to Deciat.", e)
    assert not fact_guard("Welcome to Sol.", e)


# ------------------------------------------------------------ end-to-end replay
@pytest.mark.parametrize("persona", ["ashford", "pip", "kage"])
def test_replay_sample_session(persona):
    entries = list(read_recording(SAMPLE))
    clock = VirtualClock(parse_timestamp(entries[0]["timestamp"]).timestamp())
    voice = ConsoleVoice("t", colour=False)
    c = Companion(Persona.load(PERSONAS / f"{persona}.yaml"), voice, clock, random.Random(7))
    replay(c, clock, entries)
    said = [text for _, text in voice.log]
    prios = [p for p, _ in voice.log]
    joined = "\n".join(said)
    assert "Deciat" in joined and "Wolf 397" in joined
    assert "46" in joined  # hull 46% announced
    assert "12" in joined  # landing pad
    assert Priority.P0 in prios
    # overheating arrives twice (Journal + Status flag) but is said once
    heat_lines = [t for t in said if "heat" in t.lower() or "warm" in t.lower()]
    assert len(heat_lines) == 1
    if persona != "kage":
        assert Priority.P2 in prios  # idle chatter during the long supercruise


def test_watcher_catches_up_silently_then_follows(tmp_path):
    j = tmp_path / "Journal.2026-09-27T200000.01.log"
    j.write_text('{"event":"LoadGame","Commander":"Vanni"}\n', encoding="utf-8")
    w = JournalWatcher(tmp_path)
    assert [live for _, live in w.poll()] == [False]
    with j.open("a", encoding="utf-8") as fh:
        fh.write('{"event":"FSDJump","StarSystem":"Sol"}\n{"event":"Doc')  # partial line
    got = w.poll()
    assert [(e["event"], live) for e, live in got] == [("FSDJump", True)]
    with j.open("a", encoding="utf-8") as fh:
        fh.write('ked","StationName":"Abraham Lincoln"}\n')
    assert [e["event"] for e, _ in w.poll()] == ["Docked"]
