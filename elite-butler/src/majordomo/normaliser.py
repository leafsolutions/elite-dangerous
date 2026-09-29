"""Turns raw Journal / Status entries into typed GameEvents and keeps a small game-state model.

Adding support for a new Journal event usually means adding one method named
``_on_<EventName>`` below. Nothing else needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .events import GameEvent, Priority, parse_timestamp
from .status import FlagChange, Flags, StatusTracker

HULL_THRESHOLDS = (0.75, 0.50, 0.25)

DOCKING_DENIED_REASONS = {
    "NoSpace": "no free landing pads",
    "TooLarge": "the ship is too large for their pads",
    "Hostile": "they consider us hostile",
    "Offences": "of outstanding offences",
    "Distance": "we are too far away",
    "ActiveFighter": "a fighter is still deployed",
    "NoReason": "no reason given",
}


class Mode:
    DOCKED = "docked"
    NORMAL = "normal"
    SUPERCRUISE = "supercruise"
    JUMPING = "jumping"
    COMBAT = "combat"


QUIET_MODES = {Mode.SUPERCRUISE, Mode.JUMPING}


@dataclass
class GameState:
    commander: str | None = None
    ship: str | None = None
    system: str | None = None
    station: str | None = None
    music_track: str | None = None
    jumping: bool = False
    mode: str = Mode.NORMAL


class Normaliser:
    def __init__(self) -> None:
        self.state = GameState()
        self.status = StatusTracker()
        self._hull_announced: set[float] = set()

    # ------------------------------------------------------------------ public
    def process(self, entry: dict[str, Any]) -> list[GameEvent]:
        name = entry.get("event", "")
        handler: Callable[[dict[str, Any]], list[GameEvent]] | None = getattr(
            self, f"_on_{name}", None
        )
        events = handler(entry) if handler else []
        events.extend(self._update_mode(entry))
        return events

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _ev(kind: str, priority: Priority, entry: dict[str, Any], **facts: Any) -> GameEvent:
        return GameEvent(
            kind=kind,
            priority=priority,
            facts={k: v for k, v in facts.items() if v is not None},
            timestamp=parse_timestamp(entry.get("timestamp")),
            source=f"journal:{entry.get('event')}",
        )

    def _compute_mode(self) -> str:
        track = (self.state.music_track or "").lower()
        if (track.startswith("combat") or track == "interdiction"
                or self.status.has(Flags.BEING_INTERDICTED)
                or self.status.has(Flags.IN_DANGER)):
            return Mode.COMBAT
        if self.state.jumping or self.status.has(Flags.FSD_JUMP):
            return Mode.JUMPING
        if self.status.has(Flags.DOCKED):
            return Mode.DOCKED
        if self.status.has(Flags.SUPERCRUISE):
            return Mode.SUPERCRUISE
        return Mode.NORMAL

    def _update_mode(self, entry: dict[str, Any]) -> list[GameEvent]:
        old, new = self.state.mode, self._compute_mode()
        if old == new:
            return []
        self.state.mode = new
        if new == Mode.COMBAT:
            return [self._ev("combat_start", Priority.P1, entry)]
        if old == Mode.COMBAT:
            return [self._ev("combat_end", Priority.P1, entry)]
        return []

    # ---------------------------------------------------------- journal events
    def _on_Commander(self, e: dict[str, Any]) -> list[GameEvent]:
        self.state.commander = e.get("Name")
        return []

    def _on_LoadGame(self, e: dict[str, Any]) -> list[GameEvent]:
        self.state.commander = e.get("Commander", self.state.commander)
        self.state.ship = e.get("ShipName") or e.get("Ship_Localised") or e.get("Ship")
        return [self._ev("session_start", Priority.P1, e,
                         commander=self.state.commander, ship=self.state.ship)]

    def _on_Location(self, e: dict[str, Any]) -> list[GameEvent]:
        self.state.system = e.get("StarSystem")
        self.state.station = e.get("StationName") if e.get("Docked") else None
        return []

    def _on_Music(self, e: dict[str, Any]) -> list[GameEvent]:
        self.state.music_track = e.get("MusicTrack")
        return []

    def _on_StartJump(self, e: dict[str, Any]) -> list[GameEvent]:
        if e.get("JumpType") == "Hyperspace":
            self.state.jumping = True
        return []

    def _on_FSDJump(self, e: dict[str, Any]) -> list[GameEvent]:
        self.state.jumping = False
        self.state.system = e.get("StarSystem")
        dist = e.get("JumpDist")
        return [self._ev("fsd_jump", Priority.P1, e,
                         system=self.state.system,
                         distance_ly=round(dist, 1) if dist is not None else None)]

    def _on_DockingGranted(self, e: dict[str, Any]) -> list[GameEvent]:
        return [self._ev("docking_granted", Priority.P1, e,
                         station=e.get("StationName"), pad=e.get("LandingPad"))]

    def _on_DockingDenied(self, e: dict[str, Any]) -> list[GameEvent]:
        reason = e.get("Reason", "NoReason")
        return [self._ev("docking_denied", Priority.P1, e, station=e.get("StationName"),
                         reason=DOCKING_DENIED_REASONS.get(reason, reason))]

    def _on_Docked(self, e: dict[str, Any]) -> list[GameEvent]:
        self.state.station = e.get("StationName")
        self.state.system = e.get("StarSystem", self.state.system)
        return [self._ev("docked", Priority.P1, e, station=self.state.station)]

    def _on_Undocked(self, e: dict[str, Any]) -> list[GameEvent]:
        station, self.state.station = e.get("StationName"), None
        return [self._ev("undocked", Priority.P1, e, station=station)]

    def _on_Interdicted(self, e: dict[str, Any]) -> list[GameEvent]:
        who = e.get("Interdictor_Localised") or e.get("Interdictor")
        return [self._ev("interdicted", Priority.P1, e, interdictor=who,
                         submitted=bool(e.get("Submitted")))]

    def _on_EscapeInterdiction(self, e: dict[str, Any]) -> list[GameEvent]:
        return [self._ev("interdiction_escaped", Priority.P1, e,
                         interdictor=e.get("Interdictor_Localised") or e.get("Interdictor"))]

    def _on_ShieldState(self, e: dict[str, Any]) -> list[GameEvent]:
        if e.get("ShieldsUp"):
            return [self._ev("shields_up", Priority.P1, e)]
        return [self._ev("shields_down", Priority.P0, e)]

    def _on_HullDamage(self, e: dict[str, Any]) -> list[GameEvent]:
        if e.get("PlayerPilot") is False or e.get("Fighter"):
            return []
        health = float(e.get("Health", 1.0))
        crossed = [t for t in HULL_THRESHOLDS if health < t and t not in self._hull_announced]
        if not crossed:
            return []
        self._hull_announced.update(crossed)
        return [self._ev("hull_damage", Priority.P0, e, hull_pct=round(health * 100))]

    def _reset_hull(self, e: dict[str, Any]) -> list[GameEvent]:
        self._hull_announced.clear()
        return []

    _on_RepairAll = _reset_hull
    _on_Repair = _reset_hull
    _on_Resurrect = _reset_hull

    def _on_HeatWarning(self, e: dict[str, Any]) -> list[GameEvent]:
        return [self._ev("overheating", Priority.P0, e)]

    def _on_MissionCompleted(self, e: dict[str, Any]) -> list[GameEvent]:
        return [self._ev("mission_completed", Priority.P1, e,
                         mission=e.get("LocalisedName") or e.get("Name"),
                         reward=e.get("Reward"))]

    def _on_Died(self, e: dict[str, Any]) -> list[GameEvent]:
        self._hull_announced.clear()
        return [self._ev("died", Priority.P0, e, killer=e.get("KillerName"))]

    # ------------------------------------------------------------- Status.json
    def _on_Status(self, e: dict[str, Any]) -> list[GameEvent]:
        events: list[GameEvent] = []
        for change in self.status.update(e):
            events.extend(self._on_flag_change(change, e))
        return events

    def _on_flag_change(self, c: FlagChange, e: dict[str, Any]) -> list[GameEvent]:
        fuel = (e.get("Fuel") or {}).get("FuelMain")
        fuel_t = round(fuel, 1) if isinstance(fuel, (int, float)) else None
        if c.rising and c.flag == Flags.BEING_INTERDICTED:
            return [self._ev("interdiction", Priority.P0, e)]
        if c.rising and c.flag == Flags.OVERHEATING:
            return [self._ev("overheating", Priority.P0, e)]
        if c.rising and c.flag == Flags.LOW_FUEL:
            return [self._ev("low_fuel", Priority.P0, e, fuel_t=fuel_t)]
        if not c.rising and c.flag == Flags.SCOOPING_FUEL:
            return [self._ev("fuel_scoop_done", Priority.P1, e, fuel_t=fuel_t)]
        return []
