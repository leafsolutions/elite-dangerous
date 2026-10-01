# Elite Butler

A personality-driven flight companion for Elite Dangerous. It listens to the game's Journal
files, comments on what happens in the voice of a character you choose, and knows when to
keep quiet. It **advises and entertains; it never flies**: no input is ever sent to the game.

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full design. This folder holds the Python
prototype, milestone **M0**. Its package and command keep the project's original name,
`majordomo`; the .NET solution uses the new name (`EliteButler.*`).

## Quick start (Windows)

```powershell
cd elite-butler                 # from the repository root
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
| `events.py` | Typed `GameEvent`s and priorities: the common language between the other modules |
| `companion.py` | Wires it all together; replay with a clock driven by Journal timestamps |
| `cli.py` | The `majordomo` command: `live`, `replay`, `personas` |

All modules are in `prototypes/majordomo/`.

## Personas

Personas live in `prototypes/majordomo/personas/*.yaml`. Copy one, change the lines, run
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

## Disclaimer

Elite Butler is a free, unofficial fan tool. It is not affiliated with or endorsed by
Frontier Developments. "Elite" and "Elite Dangerous" are trademarks of Frontier Developments plc.
