# AI System Scoping Document — Command Handler

*Tier T1 (Command) · Roadmap milestone M5a · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §4, §6.2, §6.3, §7.2; `DESIGN.md` §8*

### Section 1 — Problem Statement
Most questions a commander asks mid-flight have a precise, checkable answer: fuel level, nearest station with a service, best price for a commodity, materials for an upgrade, when we last died. A language model is slow and can get these wrong; a deterministic lookup is quick and right. The module must answer them in under 1.5 seconds, including a web lookup, at no per-question cost.

The outcome needed: the catalogue v1 intents work with no API key, answers are correct against the data source, and when a community web service is down the companion says so in character while game-state questions keep working offline.

### Section 2 — AI Approach Category
**Deterministic tool pipeline (no model): intent, slots, tool call, answer template.** The request has a fixed shape and a data source, so a function call plus a template is the correct and cheapest design.

### Section 3 — System Boundary

**In scope:**

- Executing the catalogue v1 intents: status (fuel, hull, cargo, location), nearest service, nearest body type, market buy and sell, engineering blueprint, memory recall, joke and lore.
- Calling the tools: game state, community services Spansh and EDSM (public Elite data websites), market data fed by EDDN (a live stream of market data shared by players), the local blueprint table, the memory database, the banks.
- Rendering the answer from the persona's template with facts only from the tool result.
- Caching and reusing the previous answer when the same question is asked with unchanged state.

**Out of scope:**

- Multi-constraint searches, planning, explanations and free conversation (module 06).
- Deciding which intent applies (module 04).
- Owning the data itself: no duplication of Inara, Spansh or EDSM.
- Any action in the game.

**Upstream dependencies (what feeds the AI system):**

Intent and slots from the Router, game-state model, community web services, local blueprint table, memory database, persona answer templates.

**Downstream consumers (what the AI system feeds):**

The Director (answer as a Reply), the Fact guard, the voice module, the utterance log, and the assistant (which can reuse these tools).

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Answer correctness | Catalogue answers matching the data source for a fixed test set of requests | 100 % of answers match the tool result |
| Response speed | Time from intent to start of speech, including a community service call | < 1.5 s for 95 % of requests |
| Offline resilience | Game-state intents answered correctly with the network disabled; unavailable-chart line spoken for web intents | 100 % of the tested cases |

---

### Section 5 — Key Unknowns

1. **Unknown:** Terms of use, rate limits and reliability of Spansh, EDSM and the market data source.  
   **Why it blocks design:** A public tool that hammers a community service or breaks its terms cannot ship; limits decide caching, request budgeting and whether the 1.5 s target is realistic.

2. **Unknown:** Whether those services can answer "nearest body type" and "nearest service" sorted by distance from an arbitrary current system, in one request.  
   **Why it blocks design:** If not, the module needs several calls or local data, which changes latency and the tool design.

3. **Unknown:** Source, licence and update path for the local blueprint table after game updates.  
   **Why it blocks design:** The project forbids stating game facts from model memory, so a wrong or stale table is a wrong answer; the update process must exist first.

---

### Section 6 — Stakeholder Communication Summary
This is the part that answers everyday questions such as "how much fuel do we have" or "where can I sell this cargo" by looking up the real information and reading it out in the character's voice. We are building it because these questions deserve instant, correct, free answers, not a guess from an AI. We will know it worked when the answers are right every time, arrive in about a second, and still work, at least for the ship's own status, without internet.

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

**Self-assessment note:** Strongest worksheet on boundary; all three unknowns are external-dependency checks that can be settled in a day or two of API experiments.
