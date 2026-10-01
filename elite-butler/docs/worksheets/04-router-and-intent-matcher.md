# AI System Scoping Document — Router and Intent Matcher

*Entry to T1 and T2 · Roadmap milestone M5a · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §6.1, §6.2, §11; `DESIGN.md` §3, §8*

### Section 1 — Problem Statement
When the commander speaks, the companion must decide quickly and cheaply what was asked and which machinery answers: a control ("quiet please"), a ready-made command, or the language-model assistant. If it picks the model too often, cost and delay grow; if it picks a command wrongly, the commander gets a confident but wrong answer.

The outcome needed: at least 80 % of spoken requests answered by the free command path once the catalogue is mature, the remainder escalated correctly, and a wrong-command rate low enough that the commander does not stop trusting it. Misses are logged and used to grow the catalogue.

### Section 2 — AI Approach Category
**Classical text matching: phrase patterns with fuzzy matching, with local text embeddings (numeric fingerprints of meaning) added only if needed.** This is a classification task over a small, fixed set of intents, which pattern matching handles locally, for free and testably.

### Section 3 — System Boundary

**In scope:**

- Recognising controls first (quiet, repeat, louder, stop, switch persona) and executing them instantly.
- Ranking intents from the command catalogue with a confidence score.
- Filling missing slots (current system, ship, jump range) from game state.
- Applying the routing rules: command if confidence is high and slots are complete; else assistant if budget allows; else command with a degraded preface; else "cannot" line with a phrasing hint.
- Passing the ranked candidates to the assistant as a hint.

**Out of scope:**

- Turning audio into text (module 03).
- Running the tools and producing answers (module 05) or free reasoning (module 06).
- Owning the catalogue content (it is data, edited without code).
- Forcing the assistant with a wake phrase until decided (see unknowns).

**Upstream dependencies (what feeds the AI system):**

Transcribed text, the command catalogue (YAML), the game-state model, the Director's budget status.

**Downstream consumers (what the AI system feeds):**

The command handler (intent plus slots), the conversation agent (text plus candidates), the Director (controls, replies), the utterance log.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Free-path share | Commands answered without a model call, among all spoken requests in a session | ≥ 80 % once the catalogue is mature |
| Wrong-command rate | Requests answered with the wrong intent or slots, from a regression test of phrase, expected intent and slots | < 2 % |
| Routing delay | Time from text ready to a routing decision | < 50 ms |

---

### Section 5 — Key Unknowns

1. **Unknown:** The numeric thresholds for "high" and "medium" confidence.  
   **Why it blocks design:** The whole routing ladder depends on them, and they can only be set with a labelled set of real spoken phrases.

2. **Unknown:** Whether fuzzy patterns are enough or local embeddings are needed.  
   **Why it blocks design:** Embeddings add a model, memory and an install step; the choice decides the technology stack for this module.

3. **Unknown:** How to match proper nouns (systems, stations, commodities) that the speech recogniser may misspell, and where the vocabulary lists come from.  
   **Why it blocks design:** Slot filling fails silently otherwise; the answer sets what data the module must ship and update.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's switchboard: it works out what the commander asked for and sends the request to the cheapest part that can answer it well. We are building it so that most questions are answered instantly and for free, and only the hard ones use a paid assistant. We will know it worked when most questions are answered correctly and quickly without the paid part, and the questions it cannot answer are cleanly handed over or politely declined.

---

## Self-Assessment Rubric

| Criterion | What good looks like | ✓ / ✗ |
|---|---|---|
| Problem statement specificity | Names a measurable business outcome, not a technology preference | ✓ |
| Approach category correctness | The chosen category matches the task type (retrieval vs. reasoning vs. classification) | ✓ |
| System boundary clarity | In-scope and out-of-scope are unambiguous; a developer could use this to decide whether a new feature request is in scope | ✓ |
| Success metric quality | Each metric is measurable, connected to the business, and has a target | ✓ |
| Unknown quality | Each unknown is a genuine blocker, not a wishlist item | ✓ |
| Executive summary | A non-technical reader could explain this system to a colleague after reading it | ✓ |

**Overall quality signal:** If you presented this document in a design review, would stakeholders leave the room with a shared understanding of what is being built, what it is not, and how success will be measured? If yes, the scoping is working.

**Self-assessment note:** All three unknowns need a recorded phrase set; until it exists the 2 % and 80 % targets are aspirations, not commitments.
