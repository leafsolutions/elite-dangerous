# AI System Scoping Document — Storyteller

*Tier T3 (Storyteller) · Roadmap milestone M4 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §3.6, §5.1, §5.2, §7.1, §8D, §11; `DESIGN.md` §6, §7*

### Section 1 — Problem Statement
Pre-written lines are instant and correct but cannot weave several past facts into one sentence, celebrate a once-in-a-career moment uniquely, or keep idle talk fresh over weeks. The companion needs an occasional, memorable second remark that connects the moment to shared history, without ever delaying a first reaction and without turning into an expensive chatterbox.

The outcome needed: no more than 6 model-written lines per hour of play, each spoken only in a quiet moment as a follow-up to an instant scripted line, each carrying only verified facts, and the commander perceiving them as the highlights of the session.

### Section 2 — AI Approach Category
**Generative pipeline (a language model writes a short line from supplied facts), with no web tools.** The task is phrasing and connecting known facts, not finding new ones, so the model gets event facts and one to three memory extracts and nothing else.

### Section 3 — System Boundary

**In scope:**

- Writing one short follow-up (at most 80 words of output, two sentences) for the listed triggers: first-ever milestones, rare and valuable events, memory links, session start and end, relationship thresholds, earned quiet chatter.
- Waiting for the next quiet window and dropping the request after 10 minutes.
- Respecting hourly and per-session caps and the minimum 8 minutes between lines.

**Out of scope:**

- Any critical alert (never escalates) and routine events.
- Answering the commander's questions (module 06).
- Looking things up on the web or in tools.
- Speaking in combat.
- Providing any fact from the model's own knowledge.

**Upstream dependencies (what feeds the AI system):**

The Director (trigger, budgets, quiet window), the originating event facts, Memory (extracts), the persona style prompt, relationship counters, and the language-model service.

**Downstream consumers (what the AI system feeds):**

The Fact guard, then the Director (spoken as lowest-priority chatter), the voice module, and the utterance log.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Line rate | Model-written follow-ups spoken per hour of play | ≤ 6 per hour, ≥ 8 minutes apart |
| Commander preference | In blind comparison of the same moments, the share of cases where the model-written follow-up is chosen over the best scripted variant | ≥ 70 % of the sample |
| Accuracy | Follow-ups spoken with a fact differing from the event or memory | 0 |

---

### Section 5 — Key Unknowns

1. **Unknown:** Whether model-written follow-ups are really better than well-made scripted variants.  
   **Why it blocks design:** If the preference score is low, the budget, the triggers and possibly the whole tier are not justified.

2. **Unknown:** How often quiet windows occur and how long they last compared with the speech time of a line and the 10-minute time limit.  
   **Why it blocks design:** If windows are rare or short, follow-ups are mostly dropped and the trigger list and timing rules must change.

3. **Unknown:** Whether a local model can serve this tier when no cloud key is configured.  
   **Why it blocks design:** It decides whether this tier is "cloud only" or a standard feature, and so the dependency picture of the whole product.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's storyteller: now and then, in a calm moment, it adds a personal remark that ties what just happened to the commander's history, such as "this is the third time we have lost a ship here". We are building it to make the character memorable, and we ration it strictly so it stays special and affordable. We will know it worked when players say those moments are the best part of a session and the bill stays small.

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

**Self-assessment note:** Metric 2 needs a human comparison panel (even just the project owner); Unknown 1 is the make-or-break question for this tier.
