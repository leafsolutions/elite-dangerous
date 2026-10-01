# AI System Scoping Document — Voice (Text-to-Speech)

*Output stage for all tiers · Roadmap milestone M1 · Draft v0.1 · 2026-10-01 · Source: `AI-TIERS.md` §4, §8; `DESIGN.md` §3, §9, §11*

### Section 1 — Problem Statement
Everything the companion says must become audible, in a voice that fits the character, quickly enough for a warning, and interruptible when a more urgent line arrives. A slow or robotic voice ruins the character; a voice that cannot be stopped makes a critical alert wait behind a joke; a voice with an unclear licence is a legal risk for a public project.

The outcome needed: critical alerts are audible in under 400 ms from the event, the voice can be cut off instantly, each persona has a distinct and legitimately licensed voice, and the companion works offline.

### Section 2 — AI Approach Category
**Pre-trained speech synthesis, used as is (local Piper by default, cloud optional) behind one common interface.** The task is converting known text to audio; no training is needed, and local running keeps delay and cost at zero.

### Section 3 — System Boundary

**In scope:**

- Converting approved text to audio through interchangeable back-ends (console for tests, local Piper, optional cloud).
- Starting playback sentence by sentence as text streams in.
- Stopping playback instantly (`stop()`) for pre-emption.
- Selecting the audio device and the persona's voice.

**Out of scope:**

- Deciding what is spoken and when (Director) or checking facts (module 02).
- Cloning real people's voices (forbidden by the design).
- Speech recognition (module 03) and sound effects or music.
- Mixing with the game's audio beyond device selection.

**Upstream dependencies (what feeds the AI system):**

Approved lines with priority from the Director, the persona's voice setting, the audio device configuration.

**Downstream consumers (what the AI system feeds):**

The commander's speakers or headset, and latency measurements in the utterance log.

---

### Section 4 — Success Metrics

| Metric | Definition | Target |
|---|---|---|
| Alert audio delay | Time from a line being approved to the first audio sample, local back-end | < 150 ms (leaving room within the 400 ms alert budget) |
| Interruption speed | Time from a critical alert to silence of the current utterance | < 100 ms |
| Distinct voices | Starter personas with a distinct, licensed voice | All shipped personas |

---

### Section 5 — Key Unknowns

1. **Unknown:** Which available voices (including Italian ones) allow redistribution in a public repository, and what their quality is.  
   **Why it blocks design:** It decides whether voices ship with the project, are downloaded separately, or require a different engine, and whether Italian personas are possible at all.

2. **Unknown:** Real synthesis delay of the local engine on a typical gaming PC while the game runs.  
   **Why it blocks design:** If it exceeds the alert budget, short alerts may need pre-rendered audio, which changes the architecture.

3. **Unknown:** Whether sentence-by-sentence streaming sounds natural enough (pauses, intonation) for longer assistant answers.  
   **Why it blocks design:** It sets how answers are chunked and whether a cloud back-end is needed for quality.

---

### Section 6 — Stakeholder Communication Summary
This is the companion's voice: it turns every line of text into speech, in a different voice for each character, and can stop talking instantly when something urgent happens. We are building it so the companion actually sounds like a butler, a ninja maid or a nervous assistant, and so a warning is never stuck behind a joke. We will know it worked when warnings are heard at once, the characters sound distinct, and every voice is properly licensed.

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

**Self-assessment note:** Unknown 1 (voice licences) is a legal check and may remove options; the technical targets are firm.
