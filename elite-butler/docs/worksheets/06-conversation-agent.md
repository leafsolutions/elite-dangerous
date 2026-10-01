# AI System Scoping Document — Conversation Agent

*Tier T2 (Assistant) · Roadmap milestone M5b · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §4, §6.3–6.5, §7; `DESIGN.md` §8*

### Section 1 — Problem Statement
Some requests cannot be answered by a ready-made command: a search with several conditions ("closest metal-rich world I have not mapped, within my jump range, near a station that buys the data"), planning ("two hours and a Python, how do I make money tonight?"), explanations of game mechanics, diagnosis from the recent log ("why did we lose that fight?"), and open conversation with the character. These need understanding, combining and explaining.

The outcome needed: the commander gets a correct, in-character answer in under 6 seconds (first sentence under 3 s), within a cost cap of 60 assistant calls per session, and every name and number in the answer is traceable to a tool result. When evidence is missing, the character says it does not know instead of inventing.

### Section 2 — AI Approach Category
**Agent with tools, plus retrieval-augmented generation (RAG).** RAG means searching a text library and giving the relevant passages to the model so it answers from them. The task needs planning across several tools (agent); explanations need retrieved text (RAG); structured data goes through tools, never through pasted text.

### Section 3 — System Boundary

**In scope:**

- Planning up to three tool rounds per question, then answering with what is known.
- Using the tools: game state, memory search, the command-handler tools, Journal history, and retrieval of explanatory passages.
- Answering in the persona's voice, two sentences at most, streamed sentence by sentence.
- Saying "I do not know" in character when no evidence supports a claim.
- Using a small fast model by default and a larger one for planning requests (set in configuration).

**Out of scope:**

- Questions the command handler answers with high confidence.
- Storing facts from its own training as game facts.
- Spontaneous remarks (Storyteller) and critical alerts.
- Any action in the game.
- Running with no API key (the fallback ladder takes over).

**Upstream dependencies (what feeds the AI system):**

The Router (question plus candidate intents as hint), game-state summary, memory, tool services, the knowledge index (module 07), persona style prompt, budget status from the Director, and the language-model service.

**Downstream consumers (what the AI system feeds):**

The Fact guard (per sentence), the Director (Reply priority, combat rules still apply), the voice module, the utterance log (tokens, latency, rounds, reject reasons).

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Fully grounded answers | Answers whose every name and number appears in a tool result or retrieved passage, from a fixed test set including the metal-rich example | 100 % pass the Fact guard; invented-fact rate 0 |
| Answer speed | Time to first spoken sentence and to full answer | First sentence < 3 s, full answer < 6 s for 90 % of questions |
| Session cost | Assistant calls and spend per hour of play | ≤ 60 calls per session, within the configured spend cap |

---

### Section 5 — Key Unknowns

1. **Unknown:** Whether a small, fast model can plan multi-tool questions within three rounds, or whether the larger model is always needed.  
   **Why it blocks design:** It determines the cost per question, which sets the realistic call cap and the model configuration.

2. **Unknown:** Whether the commander's own history (bodies already mapped, past deaths) can be queried from Journal files and memory fast enough, and in what form.  
   **Why it blocks design:** The signature example depends on it; without a history tool the assistant cannot honour "that I have not mapped yet".

3. **Unknown:** What a satisfying "I do not know" sounds like in character when evidence is missing, and how often it will happen.  
   **Why it blocks design:** If it happens too often the module feels useless; the prompt, the tools and the retrieval scope must be shaped around that rate.

---

### Section 6 — Stakeholder Communication Summary
This is the part of the companion that can think: when the commander asks something unusual or complicated, it looks up the real facts, combines them and answers in the character's voice. We are building it for the questions a simple lookup cannot handle, and we keep it on a strict budget so it stays affordable. We will know it worked when its answers are correct and traceable, arrive within a few seconds, and it admits honestly when it does not know.

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

**Self-assessment note:** Unknown 1 needs a small experiment (a handful of planning questions on two model sizes) before any cost target is firm.
