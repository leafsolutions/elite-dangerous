"""Decoding of Status.json flags and detection of flag changes ("edges").

Bit layout follows Frontier's Player Journal documentation for the ``Flags`` field.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from typing import Any


class Flags(IntFlag):
    DOCKED = 1 << 0
    LANDED = 1 << 1
    LANDING_GEAR_DOWN = 1 << 2
    SHIELDS_UP = 1 << 3
    SUPERCRUISE = 1 << 4
    FLIGHT_ASSIST_OFF = 1 << 5
    HARDPOINTS_DEPLOYED = 1 << 6
    IN_WING = 1 << 7
    LIGHTS_ON = 1 << 8
    CARGO_SCOOP_DEPLOYED = 1 << 9
    SILENT_RUNNING = 1 << 10
    SCOOPING_FUEL = 1 << 11
    SRV_HANDBRAKE = 1 << 12
    SRV_TURRET_VIEW = 1 << 13
    SRV_TURRET_RETRACTED = 1 << 14
    SRV_DRIVE_ASSIST = 1 << 15
    FSD_MASS_LOCKED = 1 << 16
    FSD_CHARGING = 1 << 17
    FSD_COOLDOWN = 1 << 18
    LOW_FUEL = 1 << 19
    OVERHEATING = 1 << 20
    HAS_LAT_LONG = 1 << 21
    IN_DANGER = 1 << 22
    BEING_INTERDICTED = 1 << 23
    IN_MAIN_SHIP = 1 << 24
    IN_FIGHTER = 1 << 25
    IN_SRV = 1 << 26
    HUD_ANALYSIS_MODE = 1 << 27
    NIGHT_VISION = 1 << 28
    ALTITUDE_FROM_AVERAGE_RADIUS = 1 << 29
    FSD_JUMP = 1 << 30
    SRV_HIGH_BEAM = 1 << 31


@dataclass(frozen=True)
class FlagChange:
    flag: Flags
    rising: bool  # True = flag switched on, False = switched off


class StatusTracker:
    """Remembers the previous Status.json snapshot and reports which flags changed."""

    def __init__(self) -> None:
        self.flags = Flags(0)
        self.snapshot: dict[str, Any] = {}
        self._initialised = False

    def update(self, status: dict[str, Any]) -> list[FlagChange]:
        new = Flags(int(status.get("Flags", 0)))
        old = self.flags
        self.flags = new
        self.snapshot = status
        if not self._initialised:
            # First snapshot only establishes the baseline: nothing "changed".
            self._initialised = True
            return []
        changes: list[FlagChange] = []
        for flag in Flags:
            was, now = bool(old & flag), bool(new & flag)
            if was != now:
                changes.append(FlagChange(flag, rising=now))
        return changes

    def has(self, flag: Flags) -> bool:
        return bool(self.flags & flag)
