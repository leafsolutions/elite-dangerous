# AI System Scoping Document — Variant and Bank Generator (build time)

*Feeds T0 · Roadmap milestone M3 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §3.5, §5.3, §10; `DESIGN.md` §6*

### Section 1 — Problem Statement
Instant scripted lines are only as good as their variety. Writing 20–50 variants per event for every persona by hand is not realistic (roughly 15 event kinds times 8 personas times 30 variants is about 3,500 lines), but a line spoken live by a model cannot be trusted or afforded for every event. The solution is to use a model once, offline, to write the lines, check them, and store them.

The outcome needed: each shipped persona has a checked set of variants per event and context-tagged banks (jokes, lore, idle remarks), the commander rarely hears the same line twice in an evening, and no variant ever alters a fact.

### Section 2 — AI Approach Category
**Offline generative pipeline with automated checks and human review.** The task is creative writing at scale under strict constraints; the model drafts, the Fact guard and similarity checks filter, a human approves banks.

### Section 3 — System Boundary

**In scope:**

- Generating variants per event and persona from the persona's style prompt and slot definitions.
- Generating joke, lore and idle banks per context tag.
- Running the Fact guard and near-duplicate and style checks on every variant.
- Producing a review report and storing accepted lines with the persona.

**Out of scope:**

- Any model call during play.
- Writing the persona's core definition, traits and starter lines (human).
- Generating command phrasings (module 13) or personas for others (module 14).
- Copying existing characters, names or likenesses (forbidden by the design).

**Upstream dependencies (what feeds the AI system):**

Persona files, the event table with its fact contracts, the Fact guard, the language-model service, a human reviewer, and the developer's API key (kept out of the repository).

**Downstream consumers (what the AI system feeds):**

The Scripted Line Renderer (variants and banks stored with each persona) and the review report.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Fact-safe variants | Stored variants that change or lose a slot value | 0 |
| Variety | Near-duplicate rate among stored variants of the same event | < 10 % |
| Review effort | Human time to approve a persona's full set | < 2 hours per persona |

---

### Section 5 — Key Unknowns

1. **Unknown:** How to measure near-duplication and drift from the persona's tone automatically.  
   **Why it blocks design:** Without it, quality control is manual and the review-time target cannot be met.

2. **Unknown:** Whether the human review of banks can be sampled, or must cover every line.  
   **Why it blocks design:** It decides whether the pipeline scales to eight personas and to community personas.

3. **Unknown:** How strict the Fact guard (module 02) will be for lines with slots and free wording.  
   **Why it blocks design:** The rejection rate decides how many drafts must be generated to obtain 30 good variants.

---

### Section 6 — Stakeholder Communication Summary
This is a workshop used before the product ships: an AI writes hundreds of alternative lines for each character, a checker removes any that get a fact wrong, and a person approves the jokes. We are building it so the companion can sound fresh all evening without paying for an AI on every sentence. We will know it worked when players rarely hear the same line twice and none of the lines ever says something false.

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

**Self-assessment note:** Review effort target is soft until Unknown 2 is answered.
