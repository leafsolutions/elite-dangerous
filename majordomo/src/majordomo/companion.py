"""Wires the pipeline together: entries in, spoken lines out."""

from __future__ import annotations

import random
import time
from typing import Any, Callable, Iterable

from .director import Director
from .events import GameEvent, Priority, parse_timestamp
from .normaliser import Normaliser
from .persona import Persona, Renderer
from .voice import Voice


class Companion:
    def __init__(self, persona: Persona, voice: Voice,
                 clock: Callable[[], float] = time.monotonic,
                 rng: random.Random | None = None) -> None:
        self.persona = persona
        self.voice = voice
        self.normaliser = Normaliser()
        self.director = Director(chattiness=persona.chattiness,
                                 cooldowns=persona.cooldowns, clock=clock)
        self.renderer = Renderer(persona, rng)

    @property
    def mode(self) -> str:
        return self.normaliser.state.mode

    def feed(self, entry: dict[str, Any], live: bool = True) -> None:
        events = self.normaliser.process(entry)
        if live:
            for ev in events:
                self.director.offer(ev, self.mode)

    def tick(self) -> int:
        """Speak whatever the Director allows right now. Returns the number of lines said."""
        said = 0
        while (ev := self.director.next(self.mode)) is not None:
            said += self._speak(ev)
        if self.director.chatter_slot(self.mode):
            said += self._speak(GameEvent("idle", Priority.P2))
        return said

    def _speak(self, ev: GameEvent) -> int:
        text = self.renderer.render(ev, self.mode)
        self.director.mark_spoken(ev)
        if not text:
            return 0
        self.voice.say(text, ev.priority)
        return 1


class VirtualClock:
    """A clock driven by Journal timestamps, so replays honour cooldowns and idle time."""

    def __init__(self, start: float) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


def replay(companion: Companion, clock: VirtualClock, entries: Iterable[dict[str, Any]],
           speed: float = 0.0, step: float = 1.0) -> None:
    """Feed a recording through the companion. ``speed`` 0 = as fast as possible,
    60 = one real second per in-game minute."""
    for entry in entries:
        ts = entry.get("timestamp")
        target = parse_timestamp(ts).timestamp() if ts else clock.now
        while clock.now + step < target:
            clock.now += step
            companion.tick()
            if speed > 0:
                time.sleep(step / speed)
        clock.now = max(clock.now, target)
        companion.feed(entry)
        companion.tick()
