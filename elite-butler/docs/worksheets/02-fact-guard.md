# AI System Scoping Document — Fact Guard

*Cross-cutting safety module (applies to T0, T2, T3) · Roadmap milestones M3, M4, M5b · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §3, §6.5, §7.2; `DESIGN.md` §3, §6*

### Section 1 — Problem Statement
Text-generating AI can invent or distort numbers and names, and it was trained before the latest game update. If the companion says "Fuel at 12 percent" when it is 21, or sends the commander to a station that does not exist, trust in the whole tool collapses. The rule of the project is that every fact comes from game files or tools, and the model only phrases it.

The outcome needed: no spoken line contains a fact that differs from the event, game state or tool result behind it. Measured over replayed sessions and a test set of deliberately corrupted lines, the share of wrong facts reaching the speakers must be zero, while the share of good lines rejected unnecessarily stays low enough that the character still sounds varied.

### Section 2 — AI Approach Category
**Deterministic validation (classical rules), no model.** Checking that a sentence still contains the exact values it was given is a comparison problem, and a checker that is itself a model would reintroduce the risk it exists to remove.

### Section 3 — System Boundary

**In scope:**

- Comparing every generated or variant line against the structured facts it was supposed to carry (numbers, names, units).
- Checking, sentence by sentence for streamed answers, that names and numbers appear in the tool output or retrieved passages.
- Rejecting a line and telling the caller which fallback to use (template line for events; "I would rather not guess" for replies).
- Running offline over cached variants at build time.

**Out of scope:**

- Judging style, humour, taste or persona fit (human review).
- Judging whether a tool result is itself correct (data sources).
- Choosing the fallback text (Scripted Line Renderer) or deciding to retry.
- Checking safety of content in general (e.g. offensive text), unless later added as a separate module.

**Upstream dependencies (what feeds the AI system):**

The candidate line, the structured fact payload (event facts, tool results, retrieved passages), and the persona's slot definitions.

**Downstream consumers (what the AI system feeds):**

The voice module (approved lines only), the Director (a reject signal), the utterance log (reject reasons), and the build-time variant generator (accept/reject per variant).

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Wrong facts spoken | Lines with a name or number not backed by the event or tool result, found in session replays and in a test set of lines with injected errors | 0 reach the speakers |
| Needless rejections | Good generated lines rejected, as a share of reviewed good lines | < 5 % |
| Added delay | Time the check adds before a line goes to speech | < 20 ms per line |

---

### Section 5 — Key Unknowns

1. **Unknown:** How to match facts reliably when wording changes: "14.2", "fourteen point two", rounded values, units, and Italian number formats.  
   **Why it blocks design:** Plain text matching either misses correct paraphrases or lets altered numbers through; the matching method decides how free the generated phrasing may be.

2. **Unknown:** Which facts are mandatory for each event kind and intent (the "fact contract").  
   **Why it blocks design:** The guard can only check what is declared; the contract also shapes the event table, the templates and the tool outputs.

3. **Unknown:** How to treat harmless invented content such as a persona's joke or a made-up nickname.  
   **Why it blocks design:** A guard that is too strict kills character; too loose lets invented place names through. The boundary needs a rule before the guard is built.

---

### Section 6 — Stakeholder Communication Summary
This is a checker that reads every sentence the companion is about to say and makes sure the numbers and names in it match the real information from the game. We are building it because an assistant that sounds charming but sometimes gets a distance or a fuel level wrong cannot be trusted in a dangerous moment. We will know it worked when, across many test sessions, not a single wrong fact is spoken, and almost all good lines still get through.

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

**Self-assessment note:** Unknown 1 is the real risk: without a matching method, metric 2 (needless rejections) cannot yet be measured.
