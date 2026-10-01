# AI System Scoping Document — Speech-to-Text (Voice Capture)

*Local recognition, not counted as a model call · Roadmap milestone M5a · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §2, §6.1; `DESIGN.md` §8, §9*

### Section 1 — Problem Statement
The commander flies with hands on the controls and needs to ask questions by voice ("Where can I sell tritium?"). The companion must turn the spoken words into text, correctly and fast enough that the answer arrives within the 1.5 s target for command replies, without sending the player's voice to a paid online service and without slowing the game on a normal gaming PC.

The outcome needed: spoken commands are understood well enough that at least 80 % of them are answered by the free command path once the catalogue is mature, with speech recognition adding no more than a few hundred milliseconds and no noticeable drop in the game's frame rate.

### Section 2 — AI Approach Category
**Pre-trained speech recognition model, used as is, run locally (the plan names `faster-whisper`).** No training is needed; the task is plain transcription, and local running keeps cost and delay low.

### Section 3 — System Boundary

**In scope:**

- Recording audio while the push-to-talk key is held and transcribing it when released.
- Supporting English first, Italian later.
- Biasing recognition toward game vocabulary (system, station and commodity names) if shown to help.
- Returning text plus a confidence indication.

**Out of scope:**

- Reading game inputs or sending any input to the game (never allowed).
- Deciding what the text means (Router, module 04).
- Always-on listening or wake-word detection (only push-to-talk is planned).
- Speaker identification and storing audio.

**Upstream dependencies (what feeds the AI system):**

The commander's microphone, a global hotkey for push-to-talk, the chosen audio device, and the optional vocabulary list.

**Downstream consumers (what the AI system feeds):**

The Router and intent matcher (text), and the utterance log (latency, recognition result).

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Understood commands | Share of test spoken commands (recorded with real game noise) that end in the correct action | ≥ 90 % English; Italian target set after first measurement |
| Recognition delay | Time from releasing the key to text ready, on a typical gaming PC with the game running | < 500 ms for a 3-second phrase |
| Game impact | Drop in the game's average frame rate while the recogniser is active | < 3 % |

---

### Section 5 — Key Unknowns

1. **Unknown:** How well the model recognises Elite vocabulary (system names, "interstellar factors", "tritium") through microphone and game noise, in English and in Italian.  
   **Why it blocks design:** It decides the model size and whether vocabulary biasing or a name-correction step is required before the Router can be designed.

2. **Unknown:** The real processor and graphics-card load of the chosen model next to the running game.  
   **Why it blocks design:** If it competes with the game, the model must be smaller or run on demand, which changes accuracy and delay budgets.

3. **Unknown:** Whether a global push-to-talk hotkey conflicts with the commander's controller and keyboard bindings, and how to capture it without reading game input.  
   **Why it blocks design:** The interaction model and the fair-play promise (no interference with play) depend on it.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's ears: it listens while the commander holds a button, and writes down what was said. We are building it so the commander can ask questions without taking their hands off the controls, and without sending their voice over the internet. We will know it worked when nearly every spoken question is understood correctly, the answer comes quickly, and the game runs as smoothly as before.

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

**Self-assessment note:** Success targets are placeholders until a recorded test set exists; Unknown 1 is the first thing to measure.
