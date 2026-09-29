"""The Director decides whether and when the companion speaks.

It keeps the companion talkative without becoming tiring:

* a priority queue, so critical events jump ahead;
* cooldowns per event kind, so the same remark isn't repeated every few seconds;
* a chatter budget (a "token bucket": a counter that refills slowly and is spent
  by every chatter line), whose refill speed is the persona's chattiness;
* modes: in combat chatter is dropped; supercruise and jumps are quiet windows
  where chatter is welcome;
* staleness: a line that could not be said in time is dropped, not said late;
* a mute command that silences everything except critical events.

Time comes from an injectable clock so the whole class is testable without sleeping.
"""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from typing import Callable

from .events import GameEvent, Priority
from .normaliser import QUIET_MODES, Mode

DEFAULT_COOLDOWNS: dict[str, float] = {
    "fsd_jump": 20,
    "docked": 10,
    "undocked": 10,
    "hull_damage": 3,
    "shields_down": 5,
    "shields_up": 20,
    "overheating": 15,
    "low_fuel": 60,
    "interdiction": 10,
    "fuel_scoop_done": 30,
    "combat_start": 30,
    "combat_end": 30,
}

TTL_SECONDS: dict[Priority, float] = {
    Priority.P0: 4,
    Priority.REPLY: 30,
    Priority.P1: 8,
    Priority.P2: 10,
}

# In combat only the essentials of P1 survive.
COMBAT_P1_ALLOWED = {"combat_start", "combat_end", "interdicted", "interdiction_escaped",
                     "shields_up", "fsd_jump"}


@dataclass(order=True)
class _Queued:
    sort_key: tuple[int, int]
    event: GameEvent = field(compare=False)
    enqueued_at: float = field(compare=False)


@dataclass
class Decision:
    accepted: bool
    reason: str


class Director:
    def __init__(
        self,
        chattiness: float = 0.5,
        cooldowns: dict[str, float] | None = None,
        clock: Callable[[], float] = time.monotonic,
        min_silence_before_chatter: float = 25.0,
        chatter_capacity: float = 2.0,
    ) -> None:
        self.clock = clock
        self.cooldowns = {**DEFAULT_COOLDOWNS, **(cooldowns or {})}
        self.chattiness = max(0.0, min(1.0, chattiness))
        self.min_silence = min_silence_before_chatter
        self.capacity = chatter_capacity
        self._tokens = self.chattiness  # quiet personas don't open with small talk
        self._last_refill = clock()
        self._queue: list[_Queued] = []
        self._seq = itertools.count()
        self._last_said: dict[str, float] = {}
        self._last_speech = clock()
        self._muted_until = 0.0

    # ----------------------------------------------------------------- control
    def mute(self, seconds: float) -> None:
        """Silence P1 and P2 for a while. Critical events are never muted."""
        self._muted_until = self.clock() + seconds

    def unmute(self) -> None:
        self._muted_until = 0.0

    @property
    def muted(self) -> bool:
        return self.clock() < self._muted_until

    # ------------------------------------------------------------------ intake
    def offer(self, event: GameEvent, mode: str) -> Decision:
        now = self.clock()
        p = event.priority
        if p in (Priority.P1, Priority.P2) and self.muted:
            return Decision(False, "muted")
        if mode == Mode.COMBAT:
            if p == Priority.P2:
                return Decision(False, "combat: no chatter")
            if p == Priority.P1 and event.kind not in COMBAT_P1_ALLOWED:
                return Decision(False, "combat: non-essential")
        if p != Priority.REPLY:
            last = self._last_said.get(event.kind)
            if last is not None and now - last < self.cooldowns.get(event.kind, 0):
                return Decision(False, "cooldown")
        heapq.heappush(self._queue, _Queued((int(p), next(self._seq)), event, now))
        return Decision(True, "queued")

    def should_preempt(self, speaking: Priority | None) -> bool:
        """True if a queued event is critical enough to interrupt the current line."""
        if not self._queue or speaking is None:
            return False
        return self._queue[0].event.priority == Priority.P0 and speaking > Priority.P0

    # ----------------------------------------------------------------- output
    def next(self, mode: str) -> GameEvent | None:
        """Pop the most urgent event that is still fresh, or None."""
        now = self.clock()
        while self._queue:
            item = heapq.heappop(self._queue)
            ev = item.event
            if now - item.enqueued_at > TTL_SECONDS[ev.priority]:
                continue  # stale: better silent than late
            if mode == Mode.COMBAT and ev.priority == Priority.P2:
                continue  # combat started while it was waiting
            if ev.priority != Priority.REPLY:
                last = self._last_said.get(ev.kind)
                if last is not None and now - last < self.cooldowns.get(ev.kind, 0):
                    continue  # a sibling was spoken while this one waited
            return ev
        return None

    def mark_spoken(self, event: GameEvent) -> None:
        now = self.clock()
        self._last_said[event.kind] = now
        self._last_speech = now
        if event.priority == Priority.P2:
            self._tokens -= 1.0

    # ---------------------------------------------------------------- chatter
    def _refill(self) -> None:
        now = self.clock()
        # chattiness 1.0 = one chatter token every 90 s; 0.1 = one every 15 min.
        rate = self.chattiness / 90.0
        self._tokens = min(self.capacity, self._tokens + (now - self._last_refill) * rate)
        self._last_refill = now

    def chatter_slot(self, mode: str) -> bool:
        """True when the companion may volunteer an idle remark right now."""
        self._refill()
        if self.muted or self._queue or mode not in QUIET_MODES:
            return False
        if self.clock() - self._last_speech < self.min_silence:
            return False
        return self._tokens >= 1.0
