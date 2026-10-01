# AI System Scoping Document — Knowledge Index (retrieval library)

*Supports T2 · Roadmap milestone M5b · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §2, §6.4, §6.5; `DESIGN.md` §8, §11*

### Section 1 — Problem Statement
When the commander asks how something works ("how does a neutron boost work?"), the answer must come from text the project has chosen, not from the model's memory, because the model was trained before the latest game update. Without a curated library the assistant either guesses or has nothing to say about mechanics, lore and news.

The outcome needed: for a test set of mechanics and lore questions, the passages retrieved contain the answer, every used passage carries its source and licence attribution, and the library can be rebuilt after a game update without code changes.

### Section 2 — AI Approach Category
**Retrieval (the search half of RAG).** The task is finding the right passages in a text library; the language model is not involved in this module. Structured data such as blueprints, prices and body data is explicitly kept out and served by tools.

### Section 3 — System Boundary

**In scope:**

- Collecting and cleaning source text: wiki extracts, lore, Galnet articles, the persona's backstory.
- Splitting it into passages, indexing it, and returning the best passages for a question with their source and licence.
- Marking the age of each passage so stale content can be spotted.
- Rebuilding the index on demand.

**Out of scope:**

- Structured game data (blueprints, materials, prices, body data), which belongs to tools.
- Writing the answer (module 06) and checking it (module 02).
- Redistributing content whose licence forbids it.
- Hosting any online service.

**Upstream dependencies (what feeds the AI system):**

Licensed or permitted text sources, the question text from the conversation agent, optional embedding model (the numeric-fingerprint model used for similarity search).

**Downstream consumers (what the AI system feeds):**

The conversation agent (passages plus attributions), the Fact guard (passages count as evidence), and the licence notices shown in the app.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Retrieval hit rate | Questions in a fixed test set where a returned passage contains the needed information | ≥ 85 % in the top three passages |
| Attribution completeness | Retrieved passages carrying source and licence in the index | 100 % |
| Rebuild effort | Time for the project owner to rebuild the index after a game update | < 30 minutes, no code change |

---

### Section 5 — Key Unknowns

1. **Unknown:** Which sources may be copied into, or built from, a public repository under their licences.  
   **Why it blocks design:** It decides whether the index ships with the project or each commander builds it locally.

2. **Unknown:** How to detect and flag passages made outdated by a game update.  
   **Why it blocks design:** Outdated mechanics explained confidently are the exact failure the project is designed to avoid.

3. **Unknown:** Whether plain keyword search is enough or an embedding model is needed, and whether it must run locally.  
   **Why it blocks design:** It decides install size, speed and whether the module works without any account.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's reference library: a collection of trusted texts about how the game works, which it searches whenever the commander asks for an explanation. We are building it so that explanations come from real sources with credit given, not from an AI's memory, which may be out of date. We will know it worked when test questions find the right passage almost every time, and the library can be refreshed easily after a game update.

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

**Self-assessment note:** Licensing (Unknown 1) is a legal question, not a technical one, and is the one most likely to change the product shape.
