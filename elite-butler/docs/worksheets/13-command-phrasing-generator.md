# AI System Scoping Document — Command Phrasing Generator (build time)

*Feeds T1 matcher and regression tests · Roadmap milestones M5a, later Italian · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §9, §10, §11; `DESIGN.md` §8, §13*

### Section 1 — Problem Statement
People ask for the same thing in many ways ("closest", "nearest", "any station around here that sells..."). If the command matcher only knows a few phrasings, too many requests fall through to the paid assistant, and the 80 % free-path target is missed. Collecting phrasings by hand is slow, and the Italian catalogue needs its own natural phrasings, not translations.

The outcome needed: a wide, reviewed list of phrasings per intent, in English and later Italian, that both trains the matcher's patterns and serves as a regression test (phrase, expected intent, expected slots) so improving one intent never silently breaks another.

### Section 2 — AI Approach Category
**Offline generative pipeline producing labelled test data.** A model drafts many phrasings of a fixed meaning; a human filters; the result becomes data, not runtime behaviour.

### Section 3 — System Boundary

**In scope:**

- Generating many phrasings per intent and slot value, in English and Italian.
- Labelling each with its expected intent and slots.
- Keeping a held-back test portion that is not used to tune the matcher.
- Feeding misses from real sessions back as new cases.

**Out of scope:**

- Matching itself (module 04) and tools (module 05).
- Recording or transcribing speech.
- Any model call at runtime.
- Inventing intents (decided by the project owner).

**Upstream dependencies (what feeds the AI system):**

The command catalogue (intents and slots), the language-model service, the project owner's review, miss logs from real sessions.

**Downstream consumers (what the AI system feeds):**

The Router and intent matcher (patterns), the test suite, and the review report.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Held-out accuracy | Share of held-out phrases mapped to the right intent and slots by the matcher | ≥ 95 % |
| Real-world coverage | Real spoken requests in test sessions matched without the assistant | ≥ 80 % after two tuning rounds |
| Language parity | Italian held-out accuracy compared with English | Within 5 points |

---

### Section 5 — Key Unknowns

1. **Unknown:** How closely model-written phrases resemble what people really say, including speech-recognition mistakes.  
   **Why it blocks design:** If they differ, the test set gives false comfort; real recorded samples must be part of the data.

2. **Unknown:** Whether the Italian catalogue should be authored natively or derived by translation and corrected.  
   **Why it blocks design:** It decides the workflow, reviewer skills and the file layout of the catalogue.

3. **Unknown:** How to keep generated test cases separate from patterns derived from the same generation run.  
   **Why it blocks design:** Mixing them inflates accuracy and hides real failures; the data split must be designed up front.

---

### Section 6 — Stakeholder Communication Summary
This is a preparation tool that uses an AI to list the many ways a person might ask the same question, so the companion's free question-answering part recognises them. We are building it so that fewer questions need the paid assistant and so we can test every change safely, in English and Italian. We will know it worked when real questions in test sessions are understood almost every time without the paid part.

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

**Self-assessment note:** Unknown 1 undermines metric 1 until real spoken samples exist.
