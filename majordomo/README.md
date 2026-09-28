# Majordomo

A personality-driven flight companion for Elite Dangerous. It listens to the game's Journal
files, comments on what happens in the voice of a character you choose, and knows when to
keep quiet. It **advises and entertains; it never flies**: no input is ever sent to the game.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full design. This is milestone **M0**.

## Quick start (Windows)

```powershell
cd D:\dev\elite\majordomo
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,tts]"

majordomo personas                                            # list the cast
majordomo replay samples\sample_session.log --persona pip     # no game needed
majordomo replay samples\sample_session.log --speed 30 --voice pyttsx3   # hear it
majordomo live --persona ashford                              # with the game running
```

`live` reads `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous` by default
(`--journal-dir` to override). Lines already in the Journal when it starts only update the
game state; the companion talks about what happens from then on.

## What's in M0

| Module | Role |
|---|---|
| `sources.py` | Follows the newest Journal file and `Status.json` by polling; reads recordings |
| `status.py` | Decodes `Status.json` flags and detects when they switch on/off |
| `normaliser.py` | Journal/Status entries → typed `GameEvent`s; tracks mode (docked, supercruise, combat…) |
| `director.py` | Talk budget: priorities, cooldowns, chatter budget, combat rules, staleness, mute |
| `persona.py` | Persona files, validation, line rendering, Fact guard |
| `voice.py` | Console voice; offline system voice via pyttsx3 |
| `companion.py` | Wires it all together; replay with a clock driven by Journal timestamps |

## Personas

Personas live in `src/majordomo/personas/*.yaml`. Copy one, change the lines, run
`majordomo personas` to validate. Rules:

* Facts only through `{slots}` (`{system}`, `{hull_pct}`, `{pad}`…). Lines for
  `fsd_jump`, `hull_damage` and `docking_granted` must mention their key fact.
* A line whose optional slot is missing (e.g. `{ship}`) is skipped automatically.
* `combat_lines` override `lines` while in combat (see Pip).
* `traits.chattiness` (0–1) sets how often the companion volunteers small talk.

## Tests

```powershell
pytest
```

## Next milestones

M1 voice (Piper, interruption) · M2 Director tuning · M3 cached line variants from a
language model · M4 memory · M5 conversation · M6 persona studio. Details in the design doc.
