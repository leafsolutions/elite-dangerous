# AI System Scoping Document — Memory and Callback Retrieval

*Feeds T1, T2, T3 and chatter · Roadmap milestone M4 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §5.2, §6.2; `DESIGN.md` §7*

### Section 1 — Problem Statement
A companion that forgets everything each session cannot make a callback ("third time we have died near Deciat"), answer "when did we last die?", or change its tone as the relationship grows. The commander's history must be stored, found at the right moment and handed on as a few exact facts, while staying on the commander's own computer and visible and erasable by them.

The outcome needed: the companion references a real earlier session or event correctly, the "when did we last die" type of question is always answered correctly, and the commander can inspect and wipe everything stored.

### Section 2 — AI Approach Category
**Classical database queries (SQLite, a single-file database), with text similarity search added only if plain queries prove insufficient.** Callbacks are based on same system, same ship, anniversary and counters, which are exact lookups.

### Section 3 — System Boundary

**In scope:**

- Storing episodes (sessions, notable events) and facts (favourite ship, running jokes, grudges) with their source event.
- Maintaining slow relationship counters (time flown, rescues, insults).
- Finding a relevant callback when the Director opens a chatter or storyteller slot.
- Answering memory queries for the command handler.
- Letting the commander view and wipe stored data.

**Out of scope:**

- Writing the remark (modules 01 and 08).
- Deciding when a callback is wanted (Director).
- Storing audio, the language-model conversation text, or anything beyond play history and commander name.
- Sending data off the machine.

**Upstream dependencies (what feeds the AI system):**

`GameEvent`s, game-state model, relationship rules, Director requests for callbacks, commander requests to view or wipe.

**Downstream consumers (what the AI system feeds):**

The command handler (recall answers), the Storyteller (one to three extracts), the Director and renderer (callbacks for chatter), and the relationship level that shifts the persona's tone.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Recall correctness | Memory answers and callbacks matching the Journal history in a fixed test replay | 100 % |
| Callback relevance | Callbacks rated "fits the moment" by the commander in a sample of sessions | ≥ 80 % |
| Control | Commander can view and wipe all stored data, verified by test | Always possible; wipe leaves 0 rows |

---

### Section 5 — Key Unknowns

1. **Unknown:** Which events become episodes or facts, and how a fact is extracted without guessing.  
   **Why it blocks design:** The storage schema and every later callback depend on it; adding fields later means migrating every user's database.

2. **Unknown:** Whether exact queries are enough to pick a callback that feels relevant, or similarity search is needed.  
   **Why it blocks design:** Similarity search adds an embedding model and complexity; the choice shapes the module's technology.

3. **Unknown:** The exact privacy boundary: what may enter a model request and how the commander reviews it.  
   **Why it blocks design:** The project is public and local-first; the boundary must be fixed before any data flows to a cloud service.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's memory: it keeps a private record of the commander's career, such as past sessions, deaths and favourite ships, and brings the right piece back at the right moment. We are building it so the companion feels like it has shared a history, while the data stays on the commander's computer and can be wiped at any time. We will know it worked when its references to the past are accurate and welcome, and the commander stays in full control of what is kept.

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

**Self-assessment note:** The only module whose privacy promise is itself a success metric; Unknown 3 should be answered before any cloud call is wired in.
