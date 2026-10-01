# AI System Scoping Document — Persona Authoring Assistant (build time)

*Tooling for commanders and the author · Roadmap milestone M6 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §10; `DESIGN.md` §6, §11, §12*

### Section 1 — Problem Statement
Personas are data files that commanders can tune and share, but writing a full persona (traits, voice, style, dozens of event lines, banks) is long and requires knowing the file format. Without help, few community personas will exist and those that do may be uneven, unsafe or copies of protected characters.

The outcome needed: a commander can describe a character in a few sentences and obtain a complete, valid, original persona that loads cleanly, with every line passing the same checks as shipped personas.

### Section 2 — AI Approach Category
**Generative assistant with validation (a guided model conversation producing structured files).** The task is drafting content to a strict schema, so the model proposes and deterministic checks and the commander decide.

### Section 3 — System Boundary

**In scope:**

- Turning a short character description into a persona file: traits, voice choice, style prompt, line sets and banks.
- Validating against the persona schema and the Fact guard.
- Flagging likely copies of existing characters, names or likenesses.
- Letting the commander edit and re-generate parts.

**Out of scope:**

- Running during play and any runtime model call.
- Publishing or moderating shared personas.
- Voice cloning or any real person's likeness.
- Guaranteeing legal clearance of a persona (it warns, it does not certify).

**Upstream dependencies (what feeds the AI system):**

The persona schema, the event table and fact contracts, the Fact guard, the variant generator (module 12), the language-model service and the commander's own API key.

**Downstream consumers (what the AI system feeds):**

The persona file loaded by the Scripted Line Renderer, the persona studio editor, and any sharing channel the commander chooses.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Valid on first load | Generated personas that load with no schema errors | ≥ 95 % |
| Time to a playable persona | From first description to a persona that speaks in a session replay | < 30 minutes |
| Originality flags | Test descriptions naming a known character that are flagged before saving | 100 % of the test set |

---

### Section 5 — Key Unknowns

1. **Unknown:** Whether the persona file format is stable after the tuning milestones (M2, M3).  
   **Why it blocks design:** A schema that still changes makes the assistant's output obsolete after every change.

2. **Unknown:** Who bears the model cost: the commander's own key, a shared key, or a local model.  
   **Why it blocks design:** A public, secret-free repository cannot ship a shared key, so the access model shapes the tool.

3. **Unknown:** How reliably copies of protected characters can be detected.  
   **Why it blocks design:** The design forbids them; if detection is weak, the tool must restrict inputs or add a human review step.

---

### Section 6 — Stakeholder Communication Summary
This is a helper that lets a player describe a new companion character in plain words and receive a ready-to-use one, with all its lines. We are building it so the community can create and share characters without technical skill, while keeping them original and correct. We will know it worked when a player gets a working character in minutes and the characters shared are original and trouble-free.

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

**Self-assessment note:** Latest and least defined module (M6); all three unknowns are legitimate reasons to defer detailed design.
