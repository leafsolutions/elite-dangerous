# AI System Scoping Document

### Section 1 — Problem Statement
*1–2 paragraphs. What is the underlying business problem? What outcome does the organisation need to achieve? Be specific about the metric that matters.*

[Your answer here]

---

### Section 2 — AI Approach Category
*1 paragraph. Which AI approach category applies — RAG, fine-tuned classifier, generative pipeline, agent, classical ML, or a combination? State your choice and give a one-sentence rationale.*

[Your answer here]

---

### Section 3 — System Boundary
*What is the AI system responsible for? What is it explicitly NOT responsible for? What are the upstream inputs and downstream outputs?*

**In scope:**

[Your answer here]

**Out of scope:**

[Your answer here]

**Upstream dependencies (what feeds the AI system):**

[Your answer here]

**Downstream consumers (what the AI system feeds):**

[Your answer here]

---

### Section 4 — Success Metrics
*2–3 metrics. Each must be specific, measurable, and connected to the business outcome — not a model performance metric.*

| Metric | Definition | Target |
|---|---|---|
| | | |
| | | |
| | | |

---

### Section 5 — Key Unknowns
*3 unknowns that must be resolved before design can proceed. Explain why each blocks the design.*

1. **Unknown:** [state it]  
   **Why it blocks design:** [explain]

2. **Unknown:** [state it]  
   **Why it blocks design:** [explain]

3. **Unknown:** [state it]  
   **Why it blocks design:** [explain]

---

### Section 6 — Stakeholder Communication Summary
*1 paragraph written for a non-technical executive. No jargon, no acronyms, no architecture. Just: what is this system, why are we building it, and how will we know it worked.*

[Your answer here]

---

## Self-Assessment Rubric

Check each criterion against your completed document.

| Criterion | What good looks like | ✓ / ✗ |
|---|---|---|
| Problem statement specificity | Names a measurable business outcome, not a technology preference | |
| Approach category correctness | The chosen category matches the task type (retrieval vs. reasoning vs. classification) | |
| System boundary clarity | In-scope and out-of-scope are unambiguous; a developer could use this to decide whether a new feature request is in scope | |
| Success metric quality | Each metric is measurable, connected to the business, and has a target | |
| Unknown quality | Each unknown is a genuine blocker, not a wishlist item | |
| Executive summary | A non-technical reader could explain this system to a colleague after reading it | |

**Overall quality signal:** If you presented this document in a design review, would stakeholders leave the room with a shared understanding of what is being built, what it is not, and how success will be measured? If yes, the scoping is working.
