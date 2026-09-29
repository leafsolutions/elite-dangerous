# Majordomo — a personality-driven flight companion for Elite Dangerous

*Design document · v0.2 · 2026-09-29*

*Changes in v0.2: the tiered response model (when the companion uses a language model and when it does not) is specified in `AI-TIERS.md`; this document now points to it from the architecture, rendering, conversation, latency and roadmap sections.*

## 1. Vision

A talkative, humorous and useful companion that rides along in the cockpit. It listens to what happens in the game, comments on it in the voice of a character chosen by the commander, remembers the shared history, and can be talked to.

The companion **advises and entertains; it never flies**. It sends no input to the game.

### Goals

- Correct, timely information in critical moments, whatever the persona.
- A strong sense of character: the same event sounds completely different from a Perfect Butler and a Ninja Maid.
- Memory of the commander's career, used for callbacks and running jokes.
- Personas defined as data files that commanders can tune and share.
- Runs comfortably next to the game on a normal gaming PC, with cost under control.
- Fully playable without a language model: alerts, commentary and voice commands work with no API key (`AI-TIERS.md` §3).

### Non-goals

- Any control of the ship (no virtual joystick, no key injection). This keeps the tool clear of Frontier's rules against bots and automated play.
- Copies of existing characters or clones of real people's voices. Personas are original characters built on archetypes.
- Replacing Inara, Spansh or EDSM. The companion *calls* them; it does not duplicate them.

## 2. Glossary

| Term | Meaning |
|---|---|
| Journal | Line-by-line JSON log files the game writes while playing, one event per line, in `%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous\` |
| `Status.json` | File in the same folder, rewritten by the game whenever the ship's live state changes (flags for shields, supercruise, heat, fuel, danger…) |
| `NavRoute.json` | File in the same folder, written when a route is plotted: the list of systems and star classes ahead |
| COVAS | Cockpit Voice Assistant: the game's own ship voice. Majordomo is, in lore terms, a COVAS with a personality |
| STT | Speech-to-text: turns the commander's voice into text |
| TTS | Text-to-speech: turns the companion's lines into audio |
| LLM | Large language model, e.g. Claude, used for free conversation and rare events |
| RAG | Retrieval-augmented generation: searching a text library and pasting the relevant passages into an LLM request so it answers from them |
| Persona | A data file describing one companion character: tone, lines, voice, quirks |
| Director | The component that decides *whether* and *when* the companion speaks |
| Router | The component that decides *which tier* answers a spoken request |
| Tier | One of four response mechanisms: T0 Scripted, T1 Command, T2 Assistant, T3 Storyteller (`AI-TIERS.md` §4) |
| Intent / Slot | A named action from the command catalogue (e.g. `nearest.service`) and a value it needs (e.g. `interstellar factors`) |
| Utterance | One thing the companion says |

## 3. Architecture

```
 Journal files ──┐
 Status.json ────┼─► Watcher ─► Normaliser ─► GameEvent ─┬─► Game-state model
 NavRoute.json ──┘                                       │
                                                         ├─► Memory (episodes, facts)
                                                         ▼
                                                     Director (talk budget, priorities,
                                                         ▲    cooldowns, modes, tier budgets)
 Commander voice ─► STT ─► Router ─┬─► T1 Command handler │
                                   │   (intent + tools,   │
                                   │    no LLM) ──────────┤
                                   └─► T2 Conversation    │
                                       agent (LLM + tools │
                                       + RAG) ────────────┘
                                                         │
                                                         ▼
                                              Persona renderer
                                   (T0 lines & variants ► T3 LLM follow-ups)
                                                         │
                                                         ▼
                                                    Fact guard ─► TTS ─► speakers
```

Everything runs locally except optional cloud calls (LLM, cloud TTS, community APIs).

### Components

1. **Watcher**: follows the newest Journal file (the game starts a new file each session, and splits long sessions with a `Continued` event) and polls `Status.json` and `NavRoute.json`. Emits raw dictionaries.
2. **Normaliser**: turns raw Journal events and `Status.json` flag *changes* into typed `GameEvent`s with a priority, a kind and a small fact payload.
3. **Game-state model**: current system, station, ship, fuel, cargo, jump range, plotted route, mode (docked, supercruise, combat…). The combat mode comes from the Journal `Music` event (for example `MusicTrack: Combat_Dogfight`) plus the "in danger" and "being interdicted" status flags.
4. **Director**: the heart of the "talkative but not annoying" requirement (section 5). Also holds the tier budgets.
5. **Persona renderer**: turns an approved event into text in the persona's voice (section 6).
6. **Fact guard**: checks that any generated line still carries the exact facts of the event or tool result (numbers, names). If it doesn't, it falls back to the persona's template line.
7. **Voice**: TTS back-ends behind one interface (console, local Piper, cloud).
8. **Router**: after push-to-talk and STT, matches controls and intents locally and chooses T1 or T2 (`AI-TIERS.md` §6).
9. **Command handler (T1)**: fills slots from speech and game state, calls a tool, answers from a template. No LLM.
10. **Conversation agent (T2)**: LLM with tools and RAG, for requests the command catalogue cannot handle.
11. **Memory**: SQLite database of episodes (sessions, notable events) and facts (favourite ship, running jokes, grudges).

## 4. Event model

### Priority classes

| Class | Examples | Rule |
|---|---|---|
| **P0 Critical** | Interdiction, hull damage, shields down, overheating, low fuel, `Died` | Always spoken, immediately, preempts everything. Short. Persona may colour the words, never hide the fact. Always T0 |
| **P1 Useful** | FSD jump arrival, docking granted/denied, mission completed, fuel scoop full, valuable scan | Spoken in character, brief, subject to cooldowns. T0, with optional T3 follow-up |
| **P2 Chatter** | Idle remarks, lore, callbacks to memory, banter | Only in quiet moments, only if the talk budget allows, dropped in combat. T0 banks, T3 when rationed budget allows |
| **Reply** | Answer to the commander's question | Treated like P1 but never dropped. T1 or T2 |

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
| `Scan` with `WasDiscovered=false` on a valuable body | `first_discovery` | P1 |
| `LoadGame` | `session_start` | P1 |
| Timer during quiet modes | `idle` | P2 |

The mapping is a table in code, easy to extend (colonisation, exobiology, Powerplay…).

## 5. Director: the talk budget

The Director keeps the companion talkative without making it tiring.

- **Queue with preemption**: a P0 cuts the current utterance short (the TTS back-end supports `stop()`) and jumps the queue.
- **Cooldowns per event kind**: e.g. no second `fsd_jump` remark within 20 s; the persona can shorten or extend them.
- **Chatter budget**: a token bucket (a counter that refills slowly over time and is spent by each P2 line). The persona's `chattiness` (0–1) sets how fast it refills. Budget empty → no chatter.
- **Tier budgets**: separate counters for T2 (per session) and T3 (per hour, per session), plus the LLM spend cap (`AI-TIERS.md` §7).
- **Modes**: `combat` drops all P2 and trims P1 to essentials. `supercruise` and `jumping` are "quiet windows" where chatter and T3 follow-ups are welcome.
- **Staleness**: an utterance older than its time-to-live (e.g. 5 s for P1, 10 min for a queued T3 follow-up) is dropped rather than said late.
- **Silence command**: "quiet please" mutes P1 and P2 for N minutes; P0 always stays on.
- **No repeats**: the renderer avoids the last N lines used for the same event.

## 6. Personas

### Principle: humour lives in the delivery, never in the data

Every line template has **slots** (`{system}`, `{hull_pct}`). Facts come only from the event, the game state or a tool result. The Fact guard rejects any LLM-generated line that loses or changes a slot value.

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
  low_fuel:
    - when: "route.next_scoopable"
      text: "Fuel low, {address}. The next star will oblige."
    - when: "not route.next_scoopable"
      text: "Fuel low, and the next star will not help us, {address}. Shall we reconsider the route?"
  fsd_jump:
    - "We have arrived in {system}, {address}. {distance_ly} light years, without incident."
  idle:
    - "Might I say, {address}, the void is looking particularly vast this evening."
banks:
  jokes: { tags: [any], file: ashford_jokes.yaml }
  lore:  { tags: [supercruise, docked], file: ashford_lore.yaml }
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

The renderer follows the tiered response model in `AI-TIERS.md`:

1. **T0 — template and conditional lines** from the persona file: instant, free, always correct.
2. **T0 — cached variants and banks**: generated offline by an LLM (20–50 variants per event per persona; joke, lore and idle banks by context tag), checked by the Fact guard and stored. Instant at runtime, lots of variety.
3. **T3 — live LLM follow-up**: only for listed triggers (first-ever milestones, rare discoveries, memory links, session start and end, relationship thresholds, rationed quiet chatter), only in quiet windows, never for P0. Guarded, with fallback to 1 or 2.

Replies to the commander (T1 and T2) are described in section 8.

## 7. Memory

- **Episodes**: one row per session plus notable events (first visit to a system, deaths, big payouts, near misses).
- **Facts**: key-value statements with a source event ("favourite ship: Krait Mk II", "was interdicted 3 times near Deciat").
- **Relationship**: a few slow-moving counters (time flown together, rescues, insults) that shift the persona's tone over weeks.
- Retrieval: when a P2 slot or T3 follow-up opens, the Director asks Memory for a relevant callback (same system, same ship, anniversary). Plain database queries first; text similarity search only if needed.
- All data stays on the commander's machine. The only personal data is the commander name and play history; the LLM prompt gets only what that utterance needs.

## 8. Conversation

- Push-to-talk key (a global hotkey; we don't read game inputs).
- STT: local `faster-whisper` by default.
- **Router** (`AI-TIERS.md` §6): controls first ("quiet please", "repeat", "switch persona"), then a local intent matcher over the command catalogue.
- **T1 Command handler**: high-confidence intents with complete slots are answered without an LLM: game state, `nearest(service)` and `nearest(body_type)` via Spansh/EDSM, `market(commodity)` via EDDN-fed market data, local blueprint table, memory queries, joke and lore banks.
- **T2 Conversation agent**: everything else. LLM with tools (`game_state()`, `memory_search()`, the T1 tools) and RAG on wiki extracts, lore and Galnet. A T0 acknowledgement plays at once; the answer streams sentence by sentence through the Fact guard. The model states only facts supported by tools or retrieved passages.
- Replies go through the Director like any other utterance, so combat rules still apply.

## 9. Technology choices

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for LLM, STT and TTS; asyncio fits an event pipeline |
| File watching | Polling (0.25 s) | Simple and reliable on Windows; the Journal is appended, not replaced |
| Storage | SQLite | Zero setup, one file |
| LLM | Claude API (Anthropic SDK), pluggable; small fast model by default, larger model for planning requests | Quality for persona voice; a local model can be plugged in later |
| Intent matching | Phrase patterns with fuzzy matching; local text embeddings later if needed | Local, free, testable |
| STT | faster-whisper | Local, fast, free |
| TTS | Piper (local) default, cloud optional | Local keeps latency and cost low |
| Config / personas / command catalogue | YAML | Human-editable, shareable |

## 10. Latency and cost budget

- P0 from event to first audio: **< 400 ms** (template line plus local TTS).
- P1: < 1 s.
- T1 command reply: < 1.5 s (includes a community API lookup).
- T2 reply: acknowledgement < 700 ms, first answer sentence < 3 s, full answer < 6 s.
- T3 follow-ups: no hard limit, dropped when their quiet window closes.
- Tier mix target: ≥ 95 % of spoken lines from T0 or T1 in a typical session; ≤ 6 T3 lines per hour.
- LLM spend cap per session (configurable); once reached, the companion falls back to T0 and T1 and says so in character. Full fallback ladder in `AI-TIERS.md` §7.

## 11. Legal and fair-play notes

- **No automation of play**: the tool reads files the game writes for third-party tools, and never sends input.
- **Original characters only**: archetypes are free to use; specific manga characters, names and likenesses are not.
- **Voices**: only licensed stock voices or voices made with the consent of the person; no clones of actors.
- **Third-party content**: wiki extracts used for RAG keep their licence attribution.
- **Privacy**: local-first; nothing is uploaded except what an LLM or API call needs, and the commander can see and wipe memory.

## 12. Roadmap

| Milestone | Scope | Done when |
|---|---|---|
| **M0 Skeleton** | Watcher, normaliser, Director, template renderer, console voice, replay mode, three personas, tests | `majordomo replay sample.log` prints a believable session |
| M1 Voice | Piper TTS, preemption, audio device selection | You hear Ashford in-game |
| M2 Director tuning | Modes from `Music` and status flags, budget tuning, silence command, conditional lines, utterance log with tier and latency | A 1-hour session feels right |
| M3 Cached variants | Offline generator plus Fact guard; joke, lore and idle banks | 30 variants per event per persona |
| M4 Memory | SQLite episodes/facts, callbacks in chatter, T3 follow-ups with budgets | Companion references last week's session |
| M5a Voice commands | Push-to-talk, STT, Router, intent matcher, T1 catalogue v1 | "Where can I sell tritium?" works with no API key |
| M5b Assistant | T2 agent with tools and RAG, acknowledgement lines, streamed replies | The multi-constraint metal-rich world question works |
| M6 Persona studio | Slider editor, import/export, sharing, persona authoring assistant | Community personas load cleanly |

## 13. Open questions

- Overlay or not? A small always-on-top subtitle window would help streamers and accessibility.
- Multiple companions at once (a bickering crew) — fun, but doubles the Director's complexity.
- Squadron mode: shared memory between commanders' companions.
- Localisation: Italian personas need Italian TTS voices, templates and an Italian command catalogue.
- Tier-model questions (local model for T3, forcing T2 with a wake phrase, visible budgets): see `AI-TIERS.md` §11.
