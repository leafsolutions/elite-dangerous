"""Voice back-ends. M0 ships a console voice and an optional offline Windows voice (pyttsx3).

Piper (local neural voices) and cloud voices arrive in milestone M1 behind the same interface.
"""

from __future__ import annotations

import sys
from typing import Callable, Protocol

from .events import Priority

_COLOURS = {Priority.P0: "\033[91m", Priority.REPLY: "\033[96m",
            Priority.P1: "\033[97m", Priority.P2: "\033[90m"}
_RESET = "\033[0m"


class Voice(Protocol):
    def say(self, text: str, priority: Priority) -> None: ...
    def stop(self) -> None: ...


class ConsoleVoice:
    def __init__(self, speaker: str, colour: bool | None = None,
                 stamp: Callable[[], str] | None = None):
        self.speaker = speaker
        self.colour = sys.stdout.isatty() if colour is None else colour
        self.stamp = stamp
        self.log: list[tuple[Priority, str]] = []

    def say(self, text: str, priority: Priority) -> None:
        self.log.append((priority, text))
        prefix = f"{self.stamp()} " if self.stamp else ""
        line = f"{prefix}[{priority.name:<5}] {self.speaker}: {text}"
        if self.colour:
            line = f"{_COLOURS[priority]}{line}{_RESET}"
        print(line, flush=True)

    def stop(self) -> None:
        pass


class Pyttsx3Voice:
    """Offline system voice (SAPI on Windows). Blocking; preemption comes in M1."""

    def __init__(self, speaker: str, voice_id: str | None = None, rate: int | None = None):
        import pyttsx3  # optional dependency: pip install majordomo[tts]

        self.console = ConsoleVoice(speaker)
        self.engine = pyttsx3.init()
        if voice_id:
            self.engine.setProperty("voice", voice_id)
        if rate:
            self.engine.setProperty("rate", rate)

    def say(self, text: str, priority: Priority) -> None:
        self.console.say(text, priority)
        self.engine.say(text)
        self.engine.runAndWait()

    def stop(self) -> None:
        self.engine.stop()


def make_voice(engine: str, speaker: str, voice_cfg: dict | None = None, **kw) -> Voice:
    voice_cfg = voice_cfg or {}
    if engine == "pyttsx3":
        return Pyttsx3Voice(speaker, voice_cfg.get("voice_id"), voice_cfg.get("rate"))
    return ConsoleVoice(speaker, **kw)
