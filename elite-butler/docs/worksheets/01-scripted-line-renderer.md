# AI System Scoping Document — Scripted Line Renderer

*Tier T0 (Scripted) · Roadmap milestones M0, M2, M3 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §4, §5.3; `DESIGN.md` §6*

*Here "business" means the commander's experience of the product; "organisation" means the Elite Butler project.*

### Section 1 — Problem Statement
Every game event (an interdiction, a jump, low fuel) needs a spoken reaction that starts in a fraction of a second, is always factually correct, and sounds like the chosen character. A call to a large language model (LLM, a text-generating AI service) is too slow (seconds), can be wrong about numbers and names, and costs money on every event, so it cannot sit between a danger and the commander's ears.

The outcome the project needs: at least 95 % of all spoken lines in a typical one-hour session come from this module or from the command module (T1), no critical alert ever waits for a model, critical alerts reach the speakers in under 400 ms and useful remarks in under 1 s, and the companion stays fully playable with no API key. A second, softer requirement is variety: the commander should not hear the same line twice in a row.

### Section 2 — AI Approach Category
**Rule-based templates with conditions (no AI at runtime), enriched by an offline generative pipeline.** Events are a closed, known set whose facts are already in the data, so a lookup with conditions is faster, cheaper and safer than reasoning; creativity is bought once at build time (module 12) and replayed for free.

### Section 3 — System Boundary

**In scope:**

- Choosing, for a given `GameEvent`, the persona line whose condition matches (e.g. "next star on route is scoopable") and filling its slots from event facts and game state.
- Avoiding recently used lines for the same event kind.
- Serving context-tagged banks (jokes, lore trivia, idle remarks) when the Director asks.
- Providing the fixed helper lines: acknowledgement ("One moment, Commander"), degraded-mode preface, "cannot now" plus command hint, "I would rather not guess".
- Acting as the fallback template when the Fact guard rejects a generated line.
- Persona-specific overrides (e.g. combat lines).

**Out of scope:**

- Deciding whether or when to speak (Director).
- Checking generated text against facts (Fact guard, module 02).
- Writing the lines (human authors and the build-time generator, module 12).
- Producing audio (voice module, 11) and any model call at runtime.
- Model-written follow-ups (Storyteller, module 08).

**Upstream dependencies (what feeds the AI system):**

Typed `GameEvent`s from the Normaliser, the game-state model (route, ship, rank, session counters), persona YAML files, cached variants and banks, and render requests from the Director.

**Downstream consumers (what the AI system feeds):**

The Director (a candidate line with its priority), the Fact guard (trivial check for templates), the Storyteller (the T0 line is always spoken first, so it is the "first beat"), and the utterance log.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Alert speed | Time from the game writing a critical event to the first audio sample, measured in replay and live | < 400 ms for 95 % of critical alerts; < 1 s for useful remarks |
| Silent events | Events in the mapping table that produced no line because a persona lacked a matching line | 0 per session replay, for every shipped persona |
| Audible repetition | Same line spoken twice in a row for the same event kind in a one-hour session | 0 occurrences |

---

### Section 5 — Key Unknowns

1. **Unknown:** How expressive the condition language in persona files must be (route facts, ship, rank, time flown, counters).  
   **Why it blocks design:** The persona file format is shared by commanders; changing the condition syntax later breaks every shared persona.

2. **Unknown:** How many variants per event a one-hour session really needs before repetition is noticed (the plan assumes 20–50).  
   **Why it blocks design:** It sizes the offline generation and human review work (module 12) and the persona file size.

3. **Unknown:** Whether the facts needed for conditions (such as star type of the next jump) are available at the moment the event fires, given when the game writes `NavRoute.json` and the Journal.  
   **Why it blocks design:** A condition that cannot be evaluated in time must be dropped or replaced, which changes the example lines the design relies on.

---

### Section 6 — Stakeholder Communication Summary
This is the part of the companion that reacts instantly to what happens in the game, using pre-written lines in the voice of the chosen character. We are building it so that warnings are never late or wrong, the character feels alive, and the game stays enjoyable without paying for an online service. We will know it worked when a full evening of play produces no missing, late or repeated reactions.

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

**Self-assessment note:** Weakest area is the metrics: the repetition target depends on variant counts that are still an assumption (Unknown 2).
