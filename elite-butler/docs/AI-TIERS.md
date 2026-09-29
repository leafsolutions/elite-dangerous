# Elite Butler — When the AI speaks: the tiered response model

*Specification · v0.2 · 2026-09-29 · companion to `DESIGN.md` (v0.3)*

*Changes in v0.2: project renamed from Majordomo to Elite Butler; no other changes.*

## 1. Purpose

This document decides, for every situation in which Elite Butler might speak, **which machinery produces the words**: a pre-written line, a deterministic lookup, or a call to a large language model. The goal is a companion that feels alive while keeping model calls rare, deliberate and budgeted.

## 2. Terms used here

| Term | Meaning |
|---|---|
| **Model call** | A request to a generative large language model (LLM), local or cloud. This is the expensive, slow and fallible step this document rations. |
| **Local recognition** | Speech-to-text (turning the commander's voice into text) and simple text matching run on the player's PC. They use machine learning but cost nothing per use, so they do **not** count as model calls. |
| **Intent** | What the commander wants, as a named action from a fixed catalogue, e.g. `nearest.service`. |
| **Slot** | A value an intent needs, e.g. the service `interstellar factors` or the commodity `tritium`. |
| **Tool** | A deterministic function the program can run: read game state, query Spansh or EDSM, look up a local table, search memory. |
| **RAG** | Retrieval-augmented generation: before a model call, the program searches a text library (wiki extracts, lore, notes) and pastes the relevant passages into the request, so the model answers from those passages instead of from its own recollection. |
| **Quiet window** | A game phase where chatter is welcome: supercruise cruising, hyperspace jump, docked and idle. Defined by the Director (`DESIGN.md` §5). |
| **Tier** | One of the four response mechanisms defined in §4. |

## 3. Principles

1. **Data answers, the model phrases.** Every fact the companion states (names, distances, prices, blueprint materials, percentages) comes from the game files, a tool or a local table. The model never supplies game facts from its own training: it was trained before the latest game update and cannot be trusted with numbers.
2. **Cheapest tier that does the job well.** A request starts at the lowest tier able to handle it and moves up only on an explicit trigger listed in this document.
3. **Safety beats wit.** Critical alerts (P0) never wait for a model. A model is never on the path between a danger and the commander's ears.
4. **Fully playable without an API key.** Tiers 0 and 1 cover all alerts, all event commentary, jokes, and the command catalogue. Model tiers are an enhancement, never a dependency.
5. **Pay once, play many.** Creativity is bought at build time: a model writes hundreds of variant lines offline, they are checked and stored, and they are replayed for free at runtime.
6. **Say it now, savour it later.** A notable event gets an instant scripted line. If it is truly special, a model-written follow-up may come in the next quiet window.

## 4. The four tiers

| Tier | Name | What produces the line | Model call at runtime? | Target latency | Cost per use |
|---|---|---|---|---|---|
| **T0** | Scripted | Persona templates, conditional lines, cached variants, banks (jokes, lore trivia, idle remarks) | No | < 400 ms (P0), < 1 s (P1) | None |
| **T1** | Command | Local intent matcher → tool → answer template | No | < 1.5 s (includes a web lookup) | None (subject to community API rate limits) |
| **T2** | Assistant | Model with tools, optionally RAG | Yes, on demand | Acknowledgement < 700 ms, first sentence < 3 s, full answer < 6 s | Per call, capped per session |
| **T3** | Storyteller | Model with event facts and memory extracts, no web tools | Yes, rationed | No hard limit; dropped if the quiet window closes | Per call, capped per hour and per session |

Build-time AI (§10) is not a runtime tier: it feeds T0 and T1.

### Who owns what

- **T0 and T1 are the companion's reflexes**: always on, instant, predictable, free.
- **T2 is the companion's head**: used when the commander asks something that needs understanding, combining or explaining.
- **T3 is the companion's heart**: used rarely, to connect the moment to shared history and make the character memorable.

## 5. Routing game events

### 5.1 Decision procedure

```
on GameEvent e:
    line = T0.render(e)                          # always, immediately
    director.submit(line, priority = e.priority)

    if e.priority == P0:            return       # never escalate a critical alert
    if not t3_trigger(e):           return
    if director.mode == combat:     return
    if not budget.t3_available():   return
    director.schedule_followup(T3.request(e), when = next_quiet_window, ttl = 10 min)
```

An event therefore always speaks through T0. A T3 follow-up is an optional second beat, never a replacement.

### 5.2 T3 triggers (events worth a model-written follow-up)

| Trigger | Examples | Why templates are not enough |
|---|---|---|
| **First-ever milestone** | First Elite rank, first Thargoid encounter, first Earth-like world discovered, first carrier jump | Happens once per career; deserves a unique line |
| **Rare and valuable** | Undiscovered Earth-like or water world (`Scan` with `WasDiscovered=false`), guardian site, very large payout | Worth celebrating with context |
| **Memory link** | Third death in the same system; return to a system with history; anniversary of the first session | Needs to weave several past facts into one sentence |
| **Session boundaries** | Session start ("previously, Commander…"), session end debrief | Summarises many events; one call per boundary |
| **Relationship threshold** | Relationship counters cross a level (`DESIGN.md` §7) | Changes the character's tone; a scripted line would feel generic |
| **Earned quiet chatter** | Long quiet window, chatter budget full, no other trigger for a while | Keeps idle talk fresh; still rationed |

Everything else stays in T0, including **all P0 alerts**, routine P1 events (jumps, docking, scooping, mission completion) and any event whose useful life is shorter than a model round trip.

### 5.3 Making T0 rich enough to need T3 rarely

T0 is not a flat list of one-liners. It supports:

- **Conditional lines**: each line may carry a condition on event facts or game state. Example for `low_fuel`:
  - *next star on route is scoopable* → "Fuel low, Commander. The next star will oblige."
  - *next star not scoopable* → "Fuel low, and the next star will not help us. Shall we reconsider the route?"
  The route comes from `NavRoute.json`, which the game writes when a route is plotted: pure data, no model.
- **State slots** beyond the event: ship name, rank, time flown tonight, jumps this session.
- **Context-tagged banks**: jokes, lore trivia and idle remarks tagged by context (`supercruise`, `near_gas_giant`, `docked_outpost`, `exobiology`). The Director picks one that fits the moment.
- **Cached variants**: 20–50 checked variants per event per persona, generated offline (§10).

## 6. Routing speech

### 6.1 Decision procedure

```
on push-to-talk released:
    text = STT(audio)                                        # local
    if control = match_control(text):                        # quiet, repeat, louder, stop, switch persona
        return control.execute()                             # T1, instant
    candidates = intent_matcher(text, catalogue)             # local, ranked with confidence
    best = candidates[0]
    fill missing slots from game state (current system, ship, jump range)
    if best.confidence >= HIGH and best.slots_complete:
        return T1.answer(best)
    if budget.t2_available():
        director.say(T0.ack_line(), priority = Reply)        # "One moment, Commander."
        return T2.answer(text, hint = candidates)
    if best.confidence >= MEDIUM and best.slots_complete:
        return T1.answer(best, preface = T0.degraded_line()) # "I cannot think it all through right now, but…"
    return T0.cannot_line() + T0.command_hint()              # suggests a phrasing that T1 understands
```

The matcher's candidates are passed to T2 as a hint, so the model can reuse a T1 tool directly when the question is a near miss.

### 6.2 Command catalogue v1 (T1)

| Intent | Example phrasings | Slots | Data source | Answer template (default persona) |
|---|---|---|---|---|
| `status.fuel` / `status.hull` / `status.cargo` | "How's our fuel?" | — | Game state | "Fuel at {fuel_pct} percent, about {jumps_left} jumps." |
| `status.location` | "Where are we?" | — | Game state | "{body}, in {system}, Commander." |
| `nearest.service` | "Nearest interstellar factors" | service | Spansh / EDSM station search, from current system | "{station} in {system}, {distance_ly} light years." |
| `nearest.body_type` | "Closest metal-rich world" | body type | Spansh body search, from current system | "The nearest metal-rich body is {body}, {distance_ly} light years away." |
| `market.sell` / `market.buy` | "Where can I sell tritium?" | commodity | EDDN-fed market data (e.g. Spansh) | "Best nearby price: {station}, {price} credits, {distance_ly} light years." |
| `engineering.blueprint` | "What do I need for grade five long range FSD?" | module, blueprint, grade | Local blueprint table | "{grade_materials}." |
| `memory.recall` | "When did we last die?" | event kind | Memory database query | "{date}, in {system}. I have not forgotten." |
| `fun.joke` / `fun.lore` | "Tell me a joke" | optional topic | T0 banks | (bank line) |

The catalogue is data (YAML), like personas, so it can grow without code changes.

### 6.3 Worked example: the metal-rich world

The request that looks like it needs AI often does not. What decides the tier is the shape of the request, not its topic.

- **"Find the closest metal-rich world."** One intent, one slot, origin taken from the game state. → **T1**: Spansh body search sorted by distance, answer from a template. No model call, under 1.5 s.
- **"Find the closest metal-rich world I haven't mapped yet, within my jump range, near a station where I can sell the data."** Several constraints, some from the commander's own history (which bodies were already mapped, from past Journal files), one from the ship (jump range, from the `Loadout` event), one from a second search (stations nearby). → **T2**: the model plans the tool calls, combines results and answers in character. Every name and number in the answer is checked against the tool results by the Fact guard.

### 6.4 What belongs in T2

| Kind of request | Example | Tools / knowledge |
|---|---|---|
| Multi-constraint search | The second metal-rich example above | Game state, memory, Spansh / EDSM |
| Planning | "I have two hours and a Python; how do I make money tonight?" | Game state, market and mission data, RAG on activity guides |
| Explanation of mechanics | "How does a neutron boost work?" | RAG on wiki extracts |
| Diagnosis from logs | "Why did we lose that fight?" | Recent events from the Journal, game state |
| Free conversation with the character | "What do you think of my Krait?" | Memory, game state |
| Anything the matcher does not understand | — | All of the above |

### 6.5 T2 rules

- **Evidence or nothing.** If no tool or retrieved passage supports a factual claim, the model says, in character, that it does not know. The prompt makes this explicit, and the Fact guard checks names and numbers against tool output.
- **Structured data goes through tools, prose goes through RAG.** Blueprints, materials, prices and body data are tables and web queries, never pasted text. RAG is reserved for explanations, lore, Galnet articles and the persona's own backstory. Wiki content keeps its licence attribution in the index.
- **At most three tool rounds** per question; beyond that, answer with what is known.
- **Instant acknowledgement** from T0 while the model works, then text-to-speech sentence by sentence as the answer streams in.
- **Model sizing.** A small, fast model by default; a larger model only for the planning class. Both are configuration, not code.

## 7. Budgets and fallback

### 7.1 Default budgets (to be tuned in M2, M4 and M5b)

| Budget | Default | Notes |
|---|---|---|
| Session spend cap | Configurable, off when no API key is set | Existing rule (`DESIGN.md` §10) |
| T3 per hour | 6 | Minimum 8 minutes between two T3 lines; only in quiet windows |
| T3 per session boundary | 1 at start, 1 at end | Can be disabled |
| T2 per session | 60 | Player-initiated, so no hourly limit; in-character warning at 80 % |
| Tokens per spoken line | Output ≤ 80 tokens | Two sentences, matching the persona style rule |
| Context per call | Persona style + tool definitions + only the facts that line needs | Stable parts are cached where the provider supports prompt caching |

The same question asked twice in a session with unchanged game state reuses the previous answer.

### 7.2 Fallback ladder

| When this fails… | …the companion does this |
|---|---|
| T3 (no budget, error, timeout, window closed) | Nothing extra: the T0 line already spoke. Optionally a bank line in the next quiet window. |
| T2 (no budget, no network, error) | Best T1 match with a degraded preface, else a T0 "cannot now" line plus a command hint |
| T1 (community API down) | T0 line saying the charts are unavailable; game-state intents still work offline |
| Fact guard rejects a generated line | Template line for events; "I would rather not guess" line for replies |

## 8. Workflows

**A. Event commentary (T0).** Watcher → Normaliser → `GameEvent` → Director checks cooldowns, mode and staleness → T0 picks a line whose condition matches and that was not used recently → Fact guard (trivial for templates) → text-to-speech.

**B. Voice command (T1).** Push-to-talk → local speech-to-text → control match or intent match → slots filled from speech and game state → tool call → answer template in the persona's voice → Director (as Reply) → text-to-speech.

**C. Open question (T2).** Push-to-talk → speech-to-text → matcher below threshold → T0 acknowledgement spoken at once → model call with persona style, game-state summary, candidate intents and tools → tool calls (≤ 3 rounds) and RAG retrieval → streamed answer → Fact guard per sentence → Director (as Reply; combat rules still apply) → text-to-speech.

**D. Storyteller moment (T3).** T3 trigger fires on an event → T0 line spoken now → follow-up request queued with a 10-minute time-to-live → at the next quiet window, if budget allows, model call with the event facts and 1–3 memory extracts → Fact guard → spoken as P2.

**E. Build time (offline).** See §10.

## 9. Measurement

Each utterance is logged locally with: tier, trigger, latency, tokens in and out, fallback reason. A short end-of-session report (also useful for testers) shows the mix.

Targets for a typical one-hour session:

- ≥ 95 % of spoken lines from T0 or T1.
- ≤ 6 T3 lines per hour.
- Zero P0 alerts that waited for a model.
- ≥ 80 % of commands answered in T1 once the catalogue is mature; the misses are reviewed to grow the catalogue.

## 10. Build-time AI

Model calls made by the developer or the persona author, not during play:

- **Cached variants** (M3): 20–50 lines per event per persona, checked by the Fact guard, stored with the persona.
- **Banks**: jokes, lore trivia and idle remarks per persona and context tag, reviewed by a human before shipping.
- **Command phrasings**: the model generates many ways of saying each intent ("closest", "nearest", "any … around here"); they extend the matcher and become a regression test set (phrase → expected intent and slots).
- **Persona authoring assistant** (M6): helps commanders write new personas and their line sets.

## 11. Open questions

- Should a local model handle T3 when no cloud key is configured? Quality versus the "runs comfortably next to the game" goal.
- Should the commander be able to force T2 with a wake phrase ("Ashford, think about…") even when a T1 intent matches?
- Italian: the intent matcher and command phrasings need an Italian catalogue, not just translated templates.
- Should T3 budgets be shown to the commander (a "mood" or "energy" meter) or stay invisible?
