"""Typed game events: the common language between the watcher, the Director and the renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any


class Priority(IntEnum):
    """Lower value = more urgent. Sorting a queue by priority puts critical events first."""

    P0 = 0  # critical: always spoken, preempts everything
    REPLY = 1  # answer to the commander: never dropped
    P1 = 2  # useful information
    P2 = 3  # chatter: only when the talk budget allows


@dataclass(frozen=True)
class GameEvent:
    kind: str
    priority: Priority
    facts: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"{self.priority.name}:{self.kind} {self.facts}"


def parse_timestamp(value: str | None) -> datetime:
    """Journal timestamps look like '2026-09-27T20:14:03Z'."""
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
