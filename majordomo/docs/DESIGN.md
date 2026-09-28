# Majordomo — a personality-driven flight companion for Elite Dangerous

*Design document · v0.1 · 2026-09-27*

## 1. Vision

A talkative, humorous and useful companion that rides along in the cockpit. It listens to what happens in the game, comments on it in the voice of a character chosen by the commander, remembers the shared history, and can be talked to.

The companion **advises and entertains; it never flies**. It sends no input to the game.

### Goals

- Correct, timely information in critical moments, whatever the persona.
- A strong sense of character: the same event sounds completely different from a Perfect Butler and a Ninja Maid.
- Memory of the commander's career, used for callbacks and running jokes.
- Personas defined as data files that commanders can tune and share.
- Runs comfortably next to the game on a normal gaming PC, with cost under control.

### Non-goals

- Any control of the ship (no virtual joystick, no key injection). This keeps the tool clear of Frontier's rules against bots and automated play.
- Copies of existing characters or clones of real people's voices. Personas are original characters built on archetypes.
- Replacing Inara, Spansh or EDSM. The companion *calls* them; it does not duplicate them.

## 2. Glossary

| Term | Meaning |
|---|---|
| Journal | Line-by-line JSON log files the game writes while playing, one event per line, in `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\` |
| `Status.json` | File in the same folder, rewritten by the game whenever the ship's live state changes (flags for shields, supercruise, heat, fuel, danger…) |
| COVAS | Cockpit Voice Assistant: the game's own ship voice. Majordomo is, in lore terms, a COVAS with a personality |
| STT | Speech-to-text: turns the commander's voice into text |
| TTS | Text-to-speech: turns the companion's lines into audio |
| LLM | Large language model, e.g. Claude, used for free conversation and rare events |
| Persona | A data file describing one companion character: tone, lines, voice, quirks |
| Director | The component that decides *whether* and *when* the companion speaks |
| Utterance | One thing the companion says |

## 3. Architecture

```
 Journal files ─┐
                ├─► Watcher ─► Normaliser ─► GameEvent ─┬─► Game-state model
 Status.json ───┘                                       │
                                                        ├─► Memory (episodes, facts)
                                                        ▼
 Commander voice ─► STT ─► Conversation agent ──► Director (talk budget, priorities,
                           (LLM + tools)            cooldowns, modes)
                                                        │
                                                        ▼
                                              Persona renderer
                                   (template lines ► cached variants ► LLM)
                                                        │
                                                        ▼
                                                   Fact guard ─► TTS ─► speakers
```

Everything runs locally except optional cloud calls (LLM, cloud TTS, community APIs).

### Components

1. **Watcher**: follows the newest Journal file (the game starts a new file each session, and splits long sessions with a `Continued` event) and polls `Status.json`. Emits raw dictionaries.
2. **Normaliser**: turns raw Journal events and `Status.json` flag *changes* into typed `GameEvent`s with a priority, a kind and a small fact payload.
3. **Game-state model**: current system, station, ship, fuel, cargo, mode (docked, supercruise, combat…). The combat mode comes from the Journal `Music` event (for example `MusicTrack: Combat_Dogfight`) plus the "in danger" and "being interdicted" status flags.
4. **Director**: the heart of the "talkative but not annoying" requirement (section 5).
5. **Persona renderer**: turns an approved event into text in the persona's voice (section 6).
6. **Fact guard**: checks that any generated line still carries the exact facts of the event (numbers, names). If it doesn't, it falls back to the persona's template line.
7. **Voice**: TTS back-ends behind one interface (console, local Piper, cloud).
8. **Conversation agent**: push-to-talk → STT → LLM with tools (game state, memory, route and market lookups) → back through the Director as a high-priority reply.
9. **Memory**: SQLite database of episodes (sessions, notable events) and facts (favourite ship, running jokes, grudges).

## 4. Event model

### Priority classes

| Class | Examples | Rule |
|---|---|---|
| **P0 Critical** | Interdiction, hull damage, shields down, overheating, low fuel, `Died` | Always spoken, immediately, preempts everything. Short. Persona may colour the words, never hide the fact |
| **P1 Useful** | FSD jump arrival, docking granted/denied, mission completed, fuel scoop full, valuable scan | Spoken in character, brief, subject to cooldowns |
| **P2 Chatter** | Idle remarks, lore, callbacks to memory, banter | Only in quiet moments, only if the talk budget allows, dropped in combat |
| **Reply** | Answer to the commander's question | Treated like P1 but never dropped |

### `GameEvent` shape

```json
{
  "kind": "fsd_jump",
  "priority": "P1",
  "timestamp": "2026-09-27T20:14:03Z",
  "facts": { "system": "Shinrarta Dezhra", "distance_ly": 14.2, "star_class": "A" },
  "source": "journal:FSDJump"
}
```

### Initial event mapping

| Source | Kind | Priority |
|---|---|---|
| `Interdicted` / Status flag "being interdicted" | `interdiction` | P0 |
| `HullDamage` (below thresholds 75/50/25%) | `hull_damage` | P0 |
| `ShieldState` with `ShieldsUp=false` | `shields_down` | P0 |
| Status flag "overheating" rising edge / `HeatWarning` | `overheating` | P0 |
| Status flag "low fuel" rising edge | `low_fuel` | P0 |
| `Died` | `died` | P0 |
| `FSDJump` | `fsd_jump` | P1 |
| `DockingGranted` / `DockingDenied` | `docking_granted` / `docking_denied` | P1 |
| `Docked` / `Undocked` | `docked` / `undocked` | P1 |
| `MissionCompleted` | `mission_completed` | P1 |
| `ReservoirReplenished`, Status "scooping fuel" falling edge | `fuel_scoop_done` | P1 |
| `LoadGame` | `session_start` | P1 |
| Timer during quiet modes | `idle` | P2 |

The mapping is a table in code, easy to extend (colonisation, exobiology, Powerplay…).

## 5. Director: the talk budget

The Director keeps the companion talkative without making it tiring.

- **Queue with preemption**: a P0 cuts the current utterance short (the TTS back-end supports `stop()`) and jumps the queue.
- **Cooldowns per event kind**: e.g. no second `fsd_jump` remark within 20 s; the persona can shorten or extend them.
- **Chatter budget**: a token bucket (a counter that refills slowly over time and is spent by each P2 line). The persona's `chattiness` (0–1) sets how fast it refills. Budget empty → no chatter.
- **Modes**: `combat` drops all P2 and trims P1 to essentials. `supercruise` and `jumping` are "quiet windows" where chatter is welcome.
- **Staleness**: an utterance older than its time-to-live (e.g. 5 s for P1) is dropped rather than said late.
- **Silence command**: "quiet please" mutes P1 and P2 for N minutes; P0 always stays on.
- **No repeats**: the renderer avoids the last N lines used for the same event.

## 6. Personas

### Principle: humour lives in the delivery, never in the data

Every line template has **slots** (`{system}`, `{hull_pct}`). Facts come only from the event. The Fact guard rejects any LLM-generated line that loses or changes a slot value.

### Persona file (YAML)

```yaml
id: perfect_butler
name: Ashford
archetype: Perfect Butler
description: Impeccable, composed, anticipates every need.
address_commander_as: "Commander"
traits: { formality: 0.9, snark: 0.3, chattiness: 0.5, loyalty: 0.8 }
voice: { engine: console, voice_id: en_GB-alan-medium }
style_prompt: >
  Speak as an impeccably composed English butler. Understated wit.
  Never flustered. Maximum two sentences.
cooldowns: { fsd_jump: 30 }
lines:
  interdiction:
    - "Interdiction in progress, {address}. I suggest we decline the invitation."
  hull_damage:
    - "Hull at {hull_pct} percent, {address}. The upholstery is suffering."
  fsd_jump:
    - "We have arrived in {system}, {address}. {distance_ly} light years, without incident."
  idle:
    - "Might I say, {address}, the void is looking particularly vast this evening."
```

### Starter cast (original characters)

| Archetype | Name | One-liner |
|---|---|---|
| Perfect Butler | Ashford | Composure incarnate; the default |
| Hidden Powerhouse | Pip | Dithering and apologetic, until combat starts: then cold, exact callouts (`combat_lines` override) |
| Ninja Maid | Kage | Minimum words, maximum efficiency |
| Old Retainer | Mr. Hale | Remembers everything the fleet has been through; loves a callback |
| Battle Butler | Graves | Polite critic of your gunnery |
| Devoted Khansama | Sora | Jealous of your other ships, kept light-hearted |
| Supernatural | The Tenant | Something living in the ship's core; knows too much about Thargoids |
| Comedic/Inept | Bumble | Gets the trivia wrong, never the facts |

### Rendering pipeline

1. **Template line** from the persona file: instant, free, always correct.
2. **Cached variants**: an offline tool asks the LLM for 20–50 variants per event per persona, runs them through the Fact guard, and stores them. Instant at runtime, lots of variety.
3. **Live LLM**: only for P2 chatter with memory callbacks, and conversation replies. Guarded, with fallback to 1 or 2.

## 7. Memory

- **Episodes**: one row per session plus notable events (first visit to a system, deaths, big payouts, near misses).
- **Facts**: key-value statements with a source event ("favourite ship: Krait Mk II", "was interdicted 3 times near Deciat").
- **Relationship**: a few slow-moving counters (time flown together, rescues, insults) that shift the persona's tone over weeks.
- Retrieval: when a P2 slot opens, the Director asks Memory for a relevant callback (same system, same ship, anniversary).
- All data stays on the commander's machine. The only personal data is the commander name and play history; the LLM prompt gets only what that utterance needs.

## 8. Conversation

- Push-to-talk key (a global hotkey; we don't read game inputs).
- STT: local `faster-whisper` by default.
- LLM agent with tools: `game_state()`, `memory_search()`, `nearest(service)` via Spansh/EDSM, `market(commodity)` via Inara/EDDN-backed sources.
- Replies go through the Director like any other utterance, so combat rules still apply.

## 9. Technology choices

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for LLM, STT and TTS; asyncio fits an event pipeline |
| File watching | Polling (0.25 s) | Simple and reliable on Windows; the Journal is appended, not replaced |
| Storage | SQLite | Zero setup, one file |
| LLM | Claude API (Anthropic SDK), pluggable | Quality for persona voice; a local model can be plugged in later |
| STT | faster-whisper | Local, fast, free |
| TTS | Piper (local) default, cloud optional | Local keeps latency and cost low |
| Config / personas | YAML | Human-editable, shareable |

## 10. Latency and cost budget

- P0 from event to first audio: **< 400 ms** (template line plus local TTS).
- P1: < 1 s. Conversation reply: < 2.5 s.
- LLM spend cap per session (configurable); once reached, the companion falls back to templates and cached variants and says so in character.

## 11. Legal and fair-play notes

- **No automation of play**: the tool reads files the game writes for third-party tools, and never sends input.
- **Original characters only**: archetypes are free to use; specific manga characters, names and likenesses are not.
- **Voices**: only licensed stock voices or voices made with the consent of the person; no clones of actors.
- **Privacy**: local-first; nothing is uploaded except what an LLM or API call needs, and the commander can see and wipe memory.

## 12. Roadmap

| Milestone | Scope | Done when |
|---|---|---|
| **M0 Skeleton** | Watcher, normaliser, Director, template renderer, console voice, replay mode, three personas, tests | `majordomo replay sample.log` prints a believable session |
| M1 Voice | Piper TTS, preemption, audio device selection | You hear Ashford in-game |
| M2 Director tuning | Modes from `Music` and status flags, budget tuning, silence command | A 1-hour session feels right |
| M3 Cached variants | Offline generator plus Fact guard | 30 variants per event per persona |
| M4 Memory | SQLite episodes/facts, callbacks in chatter | Companion references last week's session |
| M5 Conversation | Push-to-talk, STT, LLM agent with tools | "Where can I sell tritium?" works |
| M6 Persona studio | Slider editor, import/export, sharing | Community personas load cleanly |

## 13. Open questions

- Overlay or not? A small always-on-top subtitle window would help streamers and accessibility.
- Multiple companions at once (a bickering crew) — fun, but doubles the Director's complexity.
- Squadron mode: shared memory between commanders' companions.
- Localisation: Italian personas need Italian TTS voices and templates.
