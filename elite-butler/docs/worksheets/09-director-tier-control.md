# AI System Scoping Document — Director: Tier Routing and Budgets

*Orchestrates T0–T3 · Roadmap milestones M2, M4 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §5, §7, §9; `DESIGN.md` §4, §5*

### Section 1 — Problem Statement
The companion must be talkative without being tiring, never late with a warning, and never over budget. Someone has to decide, for every event, whether to speak, when, at what priority, and whether it deserves a model-written follow-up. If this goes wrong, the companion either chatters during a dogfight, stays silent when a joke would land, or spends the whole month's money in one evening.

The outcome needed: a one-hour session feels right to the commander, critical alerts always pre-empt everything, at least 95 % of lines come from the free tiers, and spending never exceeds the configured cap.

### Section 2 — AI Approach Category
**Rule-based scheduler and budget controller (classical, no model).** The decisions follow explicit rules (priorities, cooldowns, token-bucket counters, modes), which must be predictable and testable; a model in this path would break the safety principle.

### Section 3 — System Boundary

**In scope:**

- The speaking queue with pre-emption and time-to-live per utterance.
- Cooldowns per event kind, chatter budget, silence command.
- Game modes (combat, supercruise, jumping, docked) and quiet windows.
- Tier decisions: the T3 trigger test, the T2 and T3 budgets, the spend cap, the fallback ladder.
- Per-utterance logging of tier, trigger, latency, tokens, and the end-of-session report.

**Out of scope:**

- Writing the lines (modules 01, 06, 08) and checking facts (module 02).
- Understanding speech (modules 03, 04).
- Audio playback itself (module 11).
- Any model call of its own.

**Upstream dependencies (what feeds the AI system):**

`GameEvent`s, game-state and mode, Memory callbacks, persona settings (chattiness, cooldowns), budget configuration, and the tier modules' results and errors.

**Downstream consumers (what the AI system feeds):**

The voice module (what to say, in what order), the tier modules (permission to run), and the session report for the commander and testers.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Alerts never wait | Critical alerts that waited for a model or were delayed by a lower-priority line | 0 |
| Tier mix | Share of spoken lines from T0 or T1 in a typical one-hour session | ≥ 95 % |
| Session feel | Commander rating (1–5) of "talkative but not tiring" after one-hour sessions | ≥ 4 average |

---

### Section 5 — Key Unknowns

1. **Unknown:** How reliably combat mode is detected from the `Music` event and the danger flags.  
   **Why it blocks design:** A missed detection means chatter or a model line in a fight, which breaks the central promise; a fallback signal may be needed.

2. **Unknown:** The right budget numbers (6 follow-ups per hour, 8 minutes apart, 60 assistant calls, chatter refill rates).  
   **Why it blocks design:** They are guesses; tuning needs session logs, so the logging must be designed first.

3. **Unknown:** Whether the commander should see the budgets (a "mood" or "energy" meter) or not.  
   **Why it blocks design:** A visible meter needs a display and a persona hook; an invisible one does not, and the choice changes the interface scope.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's sense of timing: it decides when to speak, when to stay quiet and when a moment deserves something special, and it keeps the spending within a limit the commander sets. We are building it so the companion is lively without being annoying and never gets in the way of a warning. We will know it worked when a long evening of play feels balanced, no warning is ever late, and the cost stays where it was set.

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

**Self-assessment note:** Metric 3 is subjective by nature; it is the only honest measure of the "feels right" goal, so it stays.
