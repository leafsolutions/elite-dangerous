# Elite Butler — AI systems and modules: scoping worksheets

*Index · v0.1 · 2026-10-01 · derived from `AI-TIERS.md` v0.2 and `DESIGN.md` v0.3, using `templates/worksheet.md`*

Each worksheet scopes one system or module that takes part in deciding **how the companion speaks**. "Business" in the template is read as the commander's experience; "organisation" as the Elite Butler project.

| # | Module | Tier / role | Approach | Milestone | Runtime model call? |
|---|---|---|---|---|---|
| 01 | [Scripted Line Renderer](01-scripted-line-renderer.md) | T0 | Rules and templates | M0, M2, M3 | No |
| 02 | [Fact Guard](02-fact-guard.md) | Safety, all tiers | Deterministic validation | M3–M5b | No |
| 03 | [Speech-to-Text](03-speech-to-text.md) | Input | Pre-trained local model | M5a | No (local recognition) |
| 04 | [Router and Intent Matcher](04-router-and-intent-matcher.md) | Input to T1/T2 | Fuzzy matching, maybe embeddings | M5a | No |
| 05 | [Command Handler](05-command-handler.md) | T1 | Tool pipeline and templates | M5a | No |
| 06 | [Conversation Agent](06-conversation-agent.md) | T2 | Agent plus RAG | M5b | Yes, on demand |
| 07 | [Knowledge Index](07-knowledge-index.md) | Supports T2 | Retrieval | M5b | No |
| 08 | [Storyteller](08-storyteller.md) | T3 | Generative, no tools | M4 | Yes, rationed |
| 09 | [Director: tier routing and budgets](09-director-tier-control.md) | Orchestration | Rule-based scheduler | M2, M4 | No |
| 10 | [Memory and Callback Retrieval](10-memory-retrieval.md) | Supports T1/T2/T3 | Database queries | M4 | No |
| 11 | [Voice (Text-to-Speech)](11-voice-text-to-speech.md) | Output | Pre-trained local model | M1 | No |
| 12 | [Variant and Bank Generator](12-variant-and-bank-generator.md) | Build time, feeds T0 | Offline generative | M3 | Build time only |
| 13 | [Command Phrasing Generator](13-command-phrasing-generator.md) | Build time, feeds T1 | Offline generative | M5a | Build time only |
| 14 | [Persona Authoring Assistant](14-persona-authoring-assistant.md) | Build time | Generative with validation | M6 | Build time only |

## How the modules relate

- **Reflexes (always on, free):** 01, 02, 05, with 03 and 04 in front of 05, 09 orchestrating and 11 speaking.
- **Head (on demand):** 06 with 07; 10 supplies facts.
- **Heart (rationed):** 08 with 10.
- **Built before play:** 12, 13, 14.

## Choices made while scoping (please review)

- Modules that are not AI in the strict sense (Director, Memory, Fact guard, Scripted renderer) are included because `AI-TIERS.md` makes them part of the AI decision path; each says so under its approach category.
- The Watcher, Normaliser and game-state model are left out: they feed the AI modules but contain no AI decisions.
- Targets marked in the "Self-assessment note" of each file are placeholders to be confirmed with the first measurements (replay sessions, recorded phrases, API experiments).
- The most cross-cutting unknowns: the fact contract per event (02, 05, 12), the licences of voices and wiki text (07, 11), and the need for a recorded test set of real spoken phrases (03, 04, 13).
