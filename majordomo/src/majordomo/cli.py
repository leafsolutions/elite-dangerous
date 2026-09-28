"""Command line: ``majordomo live``, ``majordomo replay FILE``, ``majordomo personas``."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .companion import Companion, VirtualClock, replay
from .events import parse_timestamp
from .persona import Persona
from .sources import JournalWatcher, default_journal_dir, read_recording
from .voice import make_voice

PERSONA_DIR = Path(__file__).parent / "personas"


def resolve_persona(name_or_path: str) -> Persona:
    p = Path(name_or_path)
    if not p.exists():
        p = PERSONA_DIR / f"{name_or_path}.yaml"
    if not p.exists():
        available = ", ".join(sorted(f.stem for f in PERSONA_DIR.glob("*.yaml")))
        sys.exit(f"Persona '{name_or_path}' not found. Available: {available}")
    persona = Persona.load(p)
    problems = persona.validate()
    if problems:
        sys.exit("Persona file has problems:\n  " + "\n  ".join(problems))
    return persona


def cmd_live(args: argparse.Namespace) -> None:
    persona = resolve_persona(args.persona)
    folder = Path(args.journal_dir) if args.journal_dir else default_journal_dir()
    if not folder.is_dir():
        sys.exit(f"Journal folder not found: {folder}\nUse --journal-dir to point at it.")
    voice = make_voice(args.voice, persona.name, persona.voice,
                       stamp=lambda: datetime.now().strftime("%H:%M:%S"))
    companion = Companion(persona, voice)
    watcher = JournalWatcher(folder)
    print(f"{persona.name} ({persona.archetype}) is listening to {folder}. Ctrl+C to stop.")
    try:
        while True:
            for entry, live in watcher.poll():
                companion.feed(entry, live=live)
            companion.tick()
            time.sleep(args.poll)
    except KeyboardInterrupt:
        print(f"\n{persona.name}: Very good, {persona.address}. Signing off.")


def cmd_replay(args: argparse.Namespace) -> None:
    persona = resolve_persona(args.persona)
    entries = list(read_recording(Path(args.file)))
    if not entries:
        sys.exit("Recording is empty.")
    start = parse_timestamp(entries[0].get("timestamp")).timestamp()
    clock = VirtualClock(start)
    stamp = lambda: datetime.fromtimestamp(clock.now, timezone.utc).strftime("%H:%M:%S")
    voice = make_voice(args.voice, persona.name, persona.voice, stamp=stamp)
    companion = Companion(persona, voice, clock=clock)
    print(f"Replaying {args.file} with {persona.name} ({persona.archetype})\n")
    replay(companion, clock, entries, speed=args.speed)


def cmd_personas(args: argparse.Namespace) -> None:
    for f in sorted(PERSONA_DIR.glob("*.yaml")):
        p = Persona.load(f)
        status = "ok" if not p.validate() else "INVALID"
        print(f"{f.stem:<12} {p.name:<10} {p.archetype:<20} chattiness={p.chattiness:.1f}  [{status}]")
        print(f"{'':<12} {p.description}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="majordomo", description="A flight companion for Elite Dangerous")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    live = sub.add_parser("live", help="listen to the running game")
    live.add_argument("--persona", default="ashford")
    live.add_argument("--journal-dir")
    live.add_argument("--voice", choices=["console", "pyttsx3"], default="console")
    live.add_argument("--poll", type=float, default=0.25, help="seconds between file checks")
    live.set_defaults(func=cmd_live)

    rep = sub.add_parser("replay", help="replay a recorded Journal file")
    rep.add_argument("file")
    rep.add_argument("--persona", default="ashford")
    rep.add_argument("--voice", choices=["console", "pyttsx3"], default="console")
    rep.add_argument("--speed", type=float, default=0.0,
                     help="0 = instant; 60 = one real second per in-game minute")
    rep.set_defaults(func=cmd_replay)

    per = sub.add_parser("personas", help="list bundled personas")
    per.set_defaults(func=cmd_personas)

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    args.func(args)


if __name__ == "__main__":
    main()
