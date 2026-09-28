"""Where entries come from: the live game folder, or a recorded Journal file (replay)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Iterator

log = logging.getLogger(__name__)


def default_journal_dir() -> Path:
    home = Path(os.environ.get("USERPROFILE", Path.home()))
    return home / "Saved Games" / "Frontier Developments" / "Elite Dangerous"


def parse_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        log.warning("Skipping malformed line: %.80s", line)
        return None


class JournalWatcher:
    """Follows the newest Journal file and Status.json by polling.

    ``poll()`` returns ``(entry, live)`` pairs. Entries that were already in the file
    when the watcher started are returned with ``live=False``: they update the game
    state (where we are, which ship) without making the companion talk about the past.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self._file: Path | None = None
        self._offset = 0
        self._partial = ""
        self._status_mtime = 0.0
        self._first_poll = True

    def _newest_journal(self) -> Path | None:
        files = list(self.folder.glob("Journal.*.log"))
        return max(files, key=lambda p: p.stat().st_mtime) if files else None

    def poll(self) -> list[tuple[dict[str, Any], bool]]:
        out: list[tuple[dict[str, Any], bool]] = []
        catching_up = self._first_poll
        self._first_poll = False

        newest = self._newest_journal()
        if newest and newest != self._file:
            log.info("Following %s", newest.name)
            self._file, self._offset, self._partial = newest, 0, ""
        if self._file:
            with self._file.open("r", encoding="utf-8") as fh:
                fh.seek(self._offset)
                chunk = fh.read()
                self._offset = fh.tell()
            data = self._partial + chunk
            lines = data.split("\n")
            self._partial = lines.pop()  # last piece may be an incomplete line
            for line in lines:
                entry = parse_line(line)
                if entry:
                    out.append((entry, not catching_up))

        status = self.folder / "Status.json"
        if status.exists():
            mtime = status.stat().st_mtime
            if mtime != self._status_mtime:
                try:
                    entry = json.loads(status.read_text(encoding="utf-8"))
                    self._status_mtime = mtime
                    if entry:
                        out.append((entry, not catching_up))
                except (json.JSONDecodeError, OSError):
                    pass  # the game is mid-write; try again next poll
        return out


def read_recording(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            entry = parse_line(line)
            if entry:
                yield entry
