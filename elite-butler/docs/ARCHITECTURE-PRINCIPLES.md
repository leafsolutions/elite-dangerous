# Elite Butler — Architecture principles

*v0.4 · 2026-09-29 · Draft for discussion · Companion to `DESIGN.md` (v0.3) and `AI-TIERS.md` (v0.2)*

*Changes in v0.4: project renamed from Majordomo to Elite Butler; modules become `EliteButler.*`.*
*Changes in v0.3: D1 decided (personal side project and learning lab, public repository); AP-17 reframed around experiments; new AP-19 on secrets and personal data in a public repository; AP-18 packaging relaxed for personal use.*
*Changes in v0.2: AP-18 allows Python (or other languages) for specific capabilities, as helper processes behind the same contracts; AP-03, the stack table and the module sketch updated accordingly.*

## 1. Purpose

### Project goals

Elite Butler is a personal side project with two goals:

1. **Fun**: a companion that makes playing Elite Dangerous more enjoyable.
2. **Learning**: a lab to experiment with non-trivial AI architectures and build lasting knowledge.

The GitHub repository is **public**. The community may pick the project up one day, but that is not a requirement: design for one commander, keep the door open for others.

### Why principles

Elite Butler moves from a Python prototype to a structured C#/.NET solution. Before choosing libraries or drawing components, this document fixes the **principles** that every architectural decision must respect. When two designs are possible, the one that better satisfies these principles wins. When a principle has to be broken, the exception is recorded as an Architecture Decision Record (ADR: a short document stating one decision, its context and its consequences, kept in `docs/adr/`).

## 2. Forces: why this is not a traditional application

A conventional desktop tool is deterministic, free to run and fails in predictable ways. Integrating AI services changes that. The architecture has to absorb these forces:

| Force | What it means for Elite Butler |
|---|---|
| **Nondeterminism** | The same prompt can produce a different answer each time. Correctness cannot be checked by comparing with one expected string. |
| **Metered cost** | Every cloud model call is billed by the amount of text in and out. Cost grows with usage, not with installs. |
| **Latency variance** | A model call takes from a few hundred milliseconds to many seconds, with a long tail. The game does not wait. |
| **External fragility** | Providers throttle, fail, change prices and retire models. Community services (Spansh, EDSM) have their own limits. |
| **Untrusted output** | A model can state false facts, ignore instructions or produce malformed data. |
| **Untrusted input** | Text placed in a prompt can steer the model (prompt injection). In Elite Dangerous much text is written by other players: commander names, ship and fleet-carrier names, squadron names, in-game chat. |
| **Data leaving the machine** | Cloud calls send play history and third-party names to a provider. |
| **Fast-moving ecosystem** | AI libraries change quickly: in .NET, Semantic Kernel was followed by Microsoft Agent Framework within two years. |

And the non-AI forces already known from the prototype:

| Force | What it means |
|---|---|
| **Real-time event stream** | Journal and status changes arrive continuously; critical alerts must be spoken in under 400 ms. |
| **Guest on a gaming PC** | CPU, GPU, memory and audio are shared with a demanding game. |
| **Single user, local-first** | One commander, one machine; no server to operate. |
| **Community content** | Personas and command phrasings are meant to be written, tuned and shared by players. |

## 3. Principles

Each principle has a statement, the reason for it, and what it implies in practice.

### A. Structure

**AP-01 · Deterministic core, AI at the edges.**
The domain logic (event normalisation, game state, the Director, tier routing, the Fact guard, budgets) is plain, deterministic code with no reference to any AI library. AI services are *adapters*: replaceable components that plug into interfaces the core defines (the "ports and adapters" pattern, also called hexagonal architecture).
*Why:* the core is where correctness and safety live; it must be testable without a model, a network or a GPU.
*Implies:* the core assembly references no AI, audio or HTTP package. A build rule enforces it.

**AP-02 · Provider-neutral contracts, one pipeline for cross-cutting concerns.**
Every AI capability is consumed through a narrow contract: chat (for the language model), speech-to-text, text-to-speech, embeddings (numeric representations of text used for similarity search). Concerns that apply to every call (budget check, caching, tracing, timeouts, retries, redaction of personal data) are layers wrapped around the contract, not code repeated in each caller.
*Why:* providers and models will change; the rules around them must not.
*Implies:* use `Microsoft.Extensions.AI` contracts (`IChatClient`, `IEmbeddingGenerator`), which are designed to be wrapped in such layers; define our own `ISpeechToText` and `ITextToSpeech`.

**AP-03 · One application, clear modules, events inside.**
Elite Butler is a *modular monolith*: a single .NET host process made of well-separated modules (one assembly each) that talk through in-process events and interfaces. No microservices, no servers for the player to install or run. Helper processes are allowed only under AP-18, started and supervised by the host, invisible to the player.
*Why:* one user on one machine; a distributed system would add failure modes and install friction without benefit.
*Implies:* the host owns the lifecycle of everything it runs; the player starts and stops one application.

**AP-04 · Tools are written once.**
A tool (game state, Spansh search, market lookup, blueprint table, memory query) is one implementation, used deterministically by the T1 Command handler and offered to the model by the T2 Assistant.
*Why:* one place to test, rate-limit and cache each data source; T1 and T2 can never disagree on facts.
*Implies:* tools have typed inputs and outputs and a description usable as a model tool definition. Exposing them to other AI clients through the Model Context Protocol (MCP, an open standard for giving AI applications access to tools) becomes cheap later, but is not a goal now.

**AP-05 · Content is data, versioned and validated.**
Personas, lines, banks, the command catalogue and **prompts** are files, not code. Each has a schema, a version, and is validated when loaded; invalid content is rejected with a clear message and never crashes the program.
*Why:* community authoring, safe sharing, and knowing exactly which prompt produced which line.
*Implies:* no prompt text inside C# string literals; every model call records the prompt identifier and version.

### B. Treating AI as an unreliable collaborator

**AP-06 · Model output is untrusted input.**
Nothing a model returns is used without validation: structured answers are parsed against a schema, spoken lines pass the Fact guard, and tool calls requested by the model are checked against an allow-list.
*Why:* models make things up and occasionally ignore instructions.
*Implies:* every tool offered to the model is **read-only**; the model can look things up but cannot change anything (memory writes, settings, persona switches go through deterministic code).

**AP-07 · Everything placed in a prompt is untrusted too.**
Player-controlled text (commander, ship, carrier and squadron names; chat from the Journal `ReceiveText` event), web content (wiki extracts, Galnet) and community personas can contain instructions aimed at the model. Such text is inserted only as clearly delimited data, never into the instruction part of the prompt, and is length-limited.
*Why:* prompt injection is the main security risk of this kind of application. With AP-06, the damage an injection can do is bounded to a wrong or odd sentence.
*Implies:* one prompt-building component owns delimiting and truncation; community persona `style_prompt` fields are checked on import and shown to the user.

**AP-08 · Every AI call is budgeted, bounded and cancellable.**
A call is allowed only if the budget ledger permits it; it has a timeout set by its tier; it can be cancelled when the moment passes (the utterance's time-to-live expires, a P0 preempts, the commander says "stop"). Repeated failures open a *circuit breaker* (a switch that stops calling a failing service for a while instead of hammering it).
*Why:* cost and latency are part of correctness here.
*Implies:* `CancellationToken` flows through every asynchronous path; budgets and circuit state are visible in the status view.

**AP-09 · Every AI capability has a declared fallback; no-AI mode is a first-class configuration.**
The fallback ladder in `AI-TIERS.md` §7 is implemented, not improvised. Running with no API key, no network, or no GPU is a supported, tested configuration.
*Why:* the companion must stay useful when AI is unavailable or unaffordable.
*Implies:* the automated test suite runs in no-AI mode by default.

### C. Runtime qualities

**AP-10 · Latency classes are separate lanes.**
Critical alerts, useful comments, replies and chatter travel in separate bounded queues with priorities. The critical lane never waits on a network call or a model.
*Why:* a queue shared with slow work eventually delays a fast one.
*Implies:* `System.Threading.Channels` with bounded capacity per lane; text-to-speech supports interruption; the P0 path is covered by a latency test.

**AP-11 · Be a good guest on a gaming PC.**
Elite Butler declares and respects resource limits: local models load lazily, run at reduced priority, and can be swapped for cloud services when the GPU is busy.
*Why:* if Elite Butler costs frame rate, players uninstall it.
*Implies:* memory and CPU budgets are measured in a one-hour replay; GPU use by local speech models is opt-in.

### D. Verifiability

**AP-12 · Everything is replayable.**
Time, game input and AI responses can all be substituted: time through an injectable clock, game input through recorded Journal sessions, AI responses through recorded answers.
*Why:* bugs in event-driven, nondeterministic systems cannot be fixed if they cannot be reproduced.
*Implies:* no direct use of `DateTime.Now` (use .NET's `TimeProvider`); a replay command exists from the first milestone, as in the prototype.

**AP-13 · Evaluations are the tests of AI behaviour.**
Where exact assertions are impossible, behaviour is measured on reference sets with pass thresholds: phrase → expected intent and slots; event → Fact guard pass rate; question → required facts present in the answer; persona → style checks.
*Why:* "the tests pass" must mean something for the AI parts too.
*Implies:* an evaluation runner separate from unit tests, runnable against recorded answers (free, in every build) and against live models (on demand, before changing model or prompt).

**AP-14 · Every utterance is observable.**
For each utterance the system records: trigger, tier, prompt identifier and version, model, input and output size, cost estimate, latency, fallback reason. Records stay on the machine.
*Why:* tuning the Director and the tier mix is impossible without data.
*Implies:* OpenTelemetry (the standard .NET way to emit traces and metrics) exported to a local file or viewer; nothing is sent anywhere by default.

### E. Trust

**AP-15 · Local-first and minimal prompts.**
Data stays on the machine unless a call needs it; each prompt carries only what that utterance needs. Other players' names are personal data of third parties: they are replaced by neutral placeholders before a cloud call whenever the answer does not need them. API keys are stored in the operating system's credential store, never in plain configuration files. Commanders bring their own key.
*Why:* privacy by design, and a simple story for players about what leaves their PC.
*Implies:* the redaction step is one of the layers of AP-02; a "what was sent" view is available per utterance.

**AP-16 · Read-only toward the game, by construction.**
The codebase contains no capability to send input to the game: no keyboard or joystick simulation, no dependency that offers it. Game files are opened read-only.
*Why:* fair play and Frontier's rules; architecture is the strongest guarantee.
*Implies:* a dependency check in the build rejects input-injection libraries.

**AP-17 · Stable core, experiments at the edges.**
Learning is a project goal, so trying agent frameworks, retrieval variants, local models or MCP is welcome, not a distraction. Experiments live at the edges: as alternative adapters behind the existing contracts, selected by configuration, compared on the evaluation suites (AP-13), and closed with an ADR that records the outcome, including "tried, rejected, and why". The core stays on long-term-supported platform pieces with pinned versions.
*Why:* the AI ecosystem will change several times during the life of this project, and an experiment teaches most when it can be compared with the alternative on the same measurements.
*Implies:* start with the .NET long-term support release and `Microsoft.Extensions.AI` as the baseline. Heavier options (for example Microsoft Agent Framework for T2) enter as experiment adapters next to the baseline, not as replacements. An experiment never requires changing Core.

### F. Language boundaries

**AP-18 · Polyglot where it pays, behind the same contract.**
C# is the language of the host, the core and every module by default. A capability may be implemented in Python (or another language) when that ecosystem is clearly better for it — typically local speech and audio models, which are often released for Python first. Such an implementation runs as a **worker**: a helper process that the host starts, supervises and stops, and that the rest of the system sees only through the ordinary .NET contract (for example `ITextToSpeech`).
*Why:* the AI ecosystem is richest in Python, and forcing everything into .NET would close off good options. But a second runtime has real costs — packaging, start-up time, a process boundary on a latency-critical path, a second supply chain of dependencies — so it must be a deliberate, contained choice.

Admission criteria (all recorded in an ADR before a worker is introduced):

1. **No good in-process option.** Many Python models also run through ONNX Runtime (a cross-language engine for machine-learning models with first-class C# support); if the model runs well in .NET that way, no worker is needed. The speech spike checks this first.
2. **A measurable gain**: quality, latency, features or development effort, stated in the ADR.
3. **A packaging plan**: how the Python runtime and dependencies reach the PC. For the personal project (D1) a managed Python environment created from a lock file on the development machine is enough; a self-contained bundle is needed only if community distribution becomes a goal. The worker must still set itself up from the repository alone, with no dependency on paths or tools specific to one machine.

Rules for every worker:

- **Same contract, swappable.** A worker is one adapter among others; an in-process .NET implementation of the same contract must remain possible, and the contract tests run against every implementation.
- **Local, private channel.** Host and worker talk over named pipes or standard input/output, never a network port open to other machines; the message format is versioned and schema-defined. Audio is streamed in chunks so playback can start before synthesis ends.
- **Supervised lifecycle.** The host starts the worker (warming up models at launch or on first use), checks its health, restarts it after a crash, and guarantees it dies with the host (on Windows, through a Job Object, which ties child processes to their parent).
- **Never the only path for critical alerts.** If a worker serves the critical lane (text-to-speech does), an in-process fallback exists — for example a built-in Windows voice — so a crashed or slow worker cannot silence a P0 alert (AP-09, AP-10).
- **Same observability and trust rules.** The worker reports logs and traces to the host (AP-14), needs no network access for local models, has pinned and hash-checked dependencies, and falls under the same dependency checks as the .NET code (AP-16).

**Build-time tools are free to use Python.** Offline tools that never ship to players — the variant generator, banks and phrasing generation, evaluation analysis, index building for retrieval — can stay in Python with no packaging cost. The existing prototype code is a natural starting point for them.

### G. Public repository

**AP-19 · Nothing secret or personal in the repository.**
The repository is public. It never contains secrets (API keys, tokens, connection strings, passwords) or personal data (real commander names, Frontier IDs, real Journal sessions, other players' names or chat, memory databases, logs, traces, recordings of real play).
*Why:* anything pushed to a public repository must be treated as published forever; git history keeps what later commits delete. The same discipline would apply to a private repository.
*Implies:*

- **Secrets outside the working tree.** During development, .NET *user secrets* (a per-user store outside the project folder that the configuration system reads in development mode); at runtime, the Windows Credential Manager; in automated builds, the build system's encrypted secrets. Configuration files in the repository hold placeholders only; local overrides (`appsettings.Local.json`, `.env`) are git-ignored.
- **Runtime data outside the working tree.** The memory database, logs, traces, recorded AI answers and caches live under the user's local application data folder, never inside the repository folder.
- **Synthetic or sanitised test data only.** A build-time sanitiser replaces commander names, Frontier IDs, other players' names and chat before a real session becomes a test fixture or an evaluation case. Fictional names are used in samples.
- **Guard rails, not just good intentions.** A secret scanner runs before each commit (for example gitleaks as a pre-commit hook) and in the automated build; GitHub secret scanning and push protection are enabled on the repository.
- **No secrets in output.** Logs, traces and configuration dumps redact secrets; the "what was sent" view (AP-15) never shows keys.
- **If a secret is pushed anyway:** revoke and replace it immediately, then clean the history. A pushed secret is compromised whatever happens to the history.
- The same rules apply to Python workers and build-time tools.

## 4. First consequences for the .NET stack

A first mapping, to be confirmed in a stack decision ADR after a short prototype ("spike") of the riskiest pieces: speech and audio.

| Concern | Candidate | Note |
|---|---|---|
| Runtime | .NET 10 (long-term support until November 2028) | AP-17 |
| Application shell | .NET Generic Host (the standard startup, configuration, dependency-injection and logging framework) | AP-03 |
| In-process messaging | `System.Threading.Channels` | AP-10 |
| Time | `TimeProvider` | AP-12 |
| Language-model contract | `Microsoft.Extensions.AI` (`IChatClient`) | AP-02 |
| Claude access | Official `Anthropic` NuGet package, which provides an `IChatClient` implementation | AP-02; other providers and local models plug into the same contract |
| Agent orchestration | Not needed at first; Microsoft Agent Framework 1.0 (April 2026) if T2 grows into multi-step agents | AP-17 |
| Resilience | `Microsoft.Extensions.Resilience` (timeouts, retries, circuit breakers) | AP-08 |
| Observability | OpenTelemetry for .NET | AP-14 |
| Speech-to-text | Whisper.net (.NET bindings for whisper.cpp, a local Whisper implementation) | Spike needed |
| Text-to-speech | To evaluate in the spike, in this order: Piper voices through ONNX Runtime in .NET; a Python worker (Piper or newer expressive voice models) under AP-18; Windows built-in voices as the always-available fallback for the critical lane | Spike needed; AP-18 |
| Worker channel | Named pipes or standard input/output with a versioned message schema | AP-18 |
| Build-time tools | Python (variant generator, evaluations analysis, retrieval index builder) | AP-18 |
| Storage | SQLite via `Microsoft.Data.Sqlite`, database under the local application data folder | Unchanged from prototype; AP-19 |
| Secrets | .NET user secrets (development), Windows Credential Manager (runtime); gitleaks pre-commit hook, GitHub secret scanning and push protection | AP-19 |
| Content files | YAML (YamlDotNet) with schema validation | AP-05 |
| Tests | xUnit, replay tests, evaluation runner | AP-12, AP-13 |
| User interface | Open decision (§6) | — |

### Module sketch (to be refined in the architecture document)

```
EliteButler.Core        domain: events, game state, Director, routing, Fact guard, budgets   (no dependencies)
EliteButler.Game        Journal, Status.json and NavRoute.json watchers, normaliser          → Core
EliteButler.Content     personas, banks, command catalogue, prompt assets, schemas           → Core
EliteButler.Tools       game-state, Spansh, EDSM, market, blueprint and memory tools         → Core
EliteButler.AI          chat pipeline, prompt builder, redaction, budget ledger adapter      → Core, Content
EliteButler.Speech      speech-to-text, text-to-speech, audio devices, push-to-talk,         → Core
                        worker supervisor and worker clients (AP-18)
EliteButler.Memory      SQLite episodes, facts, relationship counters                        → Core
EliteButler.App         composition root, configuration, user interface                      → all
EliteButler.Tests / EliteButler.Evals

workers/tts-python/   Python text-to-speech worker, if the spike justifies it (AP-18)
tools/                Python build-time tools: variant generator, evaluation analysis, index builder
```

Dependency rule: every module depends on Core; Core depends on nothing; modules do not depend on each other except where shown. Workers depend only on the published message schema.

### The Python prototype

The prototype is frozen and becomes an **executable specification**: its sample session and test expectations are ported as the first replay tests of the .NET solution, so the new implementation starts by reproducing known behaviour. Its reusable parts (persona loading, template rendering) can seed the Python build-time tools.

## 5. Decisions

### Taken

| # | Decision | Consequences |
|---|---|---|
| D1 | **Personal side project and learning lab, in a public repository.** Community adoption possible, not required. | Design for one commander; no installer or auto-update for now; Python workers may use a managed environment (AP-18); experiments are encouraged at the edges (AP-17); strict hygiene for secrets and personal data (AP-19) |

### Open

| # | Question | Why it matters |
|---|---|---|
| D2 | User interface: tray icon only, desktop window, in-game overlay? Which UI framework (WPF, WinUI 3, Avalonia)? | Affects the App module and platform reach |
| D3 | Windows only, or also Linux (the game runs there through Proton)? | Avalonia and cross-platform audio keep Linux possible; WPF and WinUI do not |
| D4 | Priority of local language models (fully offline T2/T3)? | GPU budget, packaging size, AP-11 |
| D5 | Adopt ADRs in `docs/adr/` from now on? | Recommended by §1 |
