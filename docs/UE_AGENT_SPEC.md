# AUE TOH Unreal Autonomous Agent Specification Draft

Version 0.5. November 1, 2026.

Revision 0.5 adds a native Codex + UE MCP baseline experiment before further standalone harness work. Long-term product requirements remain unchanged.

Revision 0.4 approves local Ollama/Nimble for gameplay decisions as the explicit exception to OpenAI-backed development agents.

AUE TOH is a local Unreal Engine development agent for one developer. A supervisor turns conversational requests or supplied specifications into coordinated work by specialist agents, applies changes through Unreal tooling, runs verification, repairs failures, and produces local Git commits with evidence. Its functional benchmark is Aura's Unreal development experience: project-aware conversation, planning, editor execution, specialist delegation, verification, and recovery.

The first release targets UE 5.8.3 on macOS and uses OpenAI for development agents, vision, and AI content generation, with local Ollama/Nimble for gameplay decisions. It supports C++, Blueprints, NPC behavior, widgets, levels, materials, visual and audio asset creation, MetaSounds, Niagara editing, performance investigation, and external IDE access, with Aura-style Ask, Plan, and Agent modes. The guarded-door encounter is the integration benchmark. Building a complete multi-hour game remains a long-term capability goal.

**Status:** Requirements and architecture draft. The confirmed decisions below reflect the product requirements. Sections labelled proposed define implementation defaults for review. Experimental engine features and generated asset quality have explicit release gates.

# Confirmed product decisions

| Area | Requirement |
| --- | --- |
| User | One developer. Multiple AI agents cooperate within that developer's local session. |
| Interface | Docked Unreal chat plus external IDE/MCP access to the same local supervisor, Ask/Plan/Agent modes, context, job state, and controls. |
| Functional benchmark | Similar user-facing functionality to Aura for the required Unreal workflows in the Aura functional baseline matrix. |
| Framework | LangChain model and tool integration with LangGraph orchestration and persistent workflow state. |
| Engine | UE 5.8.3 is the first supported engine version. |
| Platform | macOS is the first required tested platform. Keep the Python core portable; other platforms need their own integration validation. |
| AI provider | OpenAI for supervisor reasoning, specialists, visual evaluation, and AI image/audio generation. Local Ollama/Nimble is the selected gameplay decision backend; OpenAI Decisions remains an explicitly selectable alternative. Replace Jev as an active dependency. |
| Provider boundary | LangChain OpenAI objects live in a dedicated file and are accessed through functions. |
| Agent team | Built-in specialists, developer-defined specialists, and supervisor-created temporary specialists. |
| Autonomy | Execute independently against an agreed specification; ask when blocked or when a new dependency needs approval. |
| Input | Support both an interactive requirements interview and an existing specification. |
| Controls | Show progress; support pause, resume, and cancel. |
| Implementation | Support both C++ and Blueprints. No global C++-first or Blueprint-first rule was selected. |
| Behavior | Dedicated specialist covering Behavior Trees, Blackboards, AI Controllers, Perception, navigation, EQS, and StateTree. |
| Other workflows | C++ implementation and debugging; Blueprint and widget editing; level, material, asset, Niagara, and performance-investigation workflows are all in release scope. |
| Assets | Search current project content, configured local folders/projects, shared repositories/network folders, and the developer's Fab library. Import suitable free assets and generate missing assets. |
| Generated assets | Textures, UI images, procedural meshes, materials, level layouts, rigged characters, animations, sound effects, ambience, music, and synthetic voice. |
| Audio workflows | Generate/import audio, create/edit MetaSounds, connect playback to gameplay, and verify PIE and packaged behavior. |
| External IDE workflows | Expose inspection, planning, job execution, progress, controls, and evidence through a local MCP interface; validate VS Code and a Codex client first. |
| Dependencies | Ask before adding each new dependency. |
| Editing model | Reference Aura's use of Unreal asset sandboxing in the active editor. Coordinate operations on shared editor state. |
| Source control | Git plus Git LFS. Commit locally to an agent-owned branch. |
| Completion | Compile, validate assets, run automated PIE tests, and run a packaged-game smoke test. |
| Recovery | Automatically recover after editor or worker crashes, reconcile actual project state, and resume when the state is consistent. |
| Cost | Measure prototype usage before selecting monetary limits. Record usage from the beginning. |
| Installation | Source installation and a packaged Unreal plugin with its worker-service setup. |
| Benchmark | Guarded locked door, C++ interaction logic, UI prompts, and an encounter level; single-player, starting from an empty Unreal project. |

Shared team coordination, remote job dispatch, multi-user permissions, and shared developer conversations were removed when the scope changed to one developer. A configured shared asset folder remains a valid asset source.

A developer may use a personal or organization-owned OpenAI API key. This is credential configuration for one local user, not a shared coordinator feature.

# Product scope and release boundary

The tool must manage development work, rather than only produce text, code snippets, or testing reports. It must inspect the connected project, identify relevant existing systems, delegate work, integrate dependent changes, and verify observable results.

All confirmed workflow areas and required rows of the Aura functional baseline matrix belong in the first-release specification. Internal milestones may implement them incrementally. A partial milestone must identify its supported subset; it cannot be described as satisfying the full release.

The initial release does not include shared team orchestration, other game engines, multiplayer-game acceptance, automatic Git pushes, pull-request creation, merging into the developer's original branch, paid asset purchases, or automatic installation of newly requested dependencies. Windows and Linux validation, provider-agnostic execution, public distribution signing/notarization, and advanced live redirection are later work.

A job may reference a larger game's specifications and work across sessions. The release benchmark measures tool reliability on a bounded encounter. It does not establish a general guarantee of complete-game delivery, production art quality, or exhaustive bug detection.

# Aura functional baseline

Functional similarity to Aura is a product requirement. It means the developer can perform comparable Unreal tasks through the tool and inspect the resulting changes and evidence. The baseline is Aura's documented Unreal functionality reviewed on October 31, 2026; later Aura updates require an explicit baseline revision.

The table defines required outcomes for this release. Each row needs its own reproducible scenario and evidence. The guarded-door encounter remains the integration fixture; it is not the entire functionality test.

| Area and reference | Required outcome | Acceptance evidence |
| --- | --- | --- |
| [Ask Plan and Agent modes](https://www.tryaura.dev/documentation/) | Answer project questions without edits; produce and refine a stored plan; execute an agreed plan autonomously. | Mode-policy tests, plan artifact, and implementation report. |
| [Project understanding](https://www.tryaura.dev/documentation/project-understanding/) | Search code/assets immediately, build a project index, relate classes/assets/references, and refresh changed entries. | Correct referenced answers before indexing completes and after a rename or source change. |
| [Context selection](https://www.tryaura.dev/documentation/giving-aura-context/) | Add assets/files, selected editor objects, images, and design documents to a focused task. | Correct target resolution from context and correct extraction of a supplied specification. |
| [C++ and editor operations](https://www.tryaura.dev/documentation/) | Implement native logic, compile/repair it, and perform scoped editor operations and batch edits. | Successful build plus read-back of the requested changes. |
| [Blueprints and widgets](https://www.tryaura.dev/documentation/blueprints/) | Create, inspect, review, and edit graphs, functions/events, components, data definitions, Timelines, and UMG connections. | Asset compilation, reference checks, targeted review, and runtime tests. |
| [NPC behavior](https://www.tryaura.dev/documentation/behavior-trees/) | Create and edit Behavior Trees, Blackboards, and EQS; also meet this project's explicit StateTree, Perception, and navigation requirements. | Transition, target-validity, and navigation fixtures. |
| [Levels materials and art](https://www.tryaura.dev/documentation/) | Build and edit level content, materials, and assets using project context and the approved library/generation pipeline. | Imports, compiled materials, references, and visible/reachable scene results. |
| [Niagara VFX](https://www.tryaura.dev/documentation/vfx-agent/) | Create/edit a representative effect and connect it to a gameplay event. | Particle/material compilation, parameter read-back, runtime capture, and packaged inclusion. |
| [Audio and MetaSounds](https://www.tryaura.dev/documentation/audio/) | Generate/import sound effects, ambience, music, and voice; create/edit MetaSounds and connect playback to gameplay. | Generated files, graph/asset validation, playback capture, and packaged audio checks. |
| [External IDE access](https://www.tryaura.dev/documentation/aura-ide-mcp/) | Inspect, plan, and start/control jobs from compatible external clients using the same local supervisor and editor gateway. | Client setup, synchronized job IDs/events, reconnect, mode enforcement, and end-to-end execution. |
| [Performance investigation](https://www.tryaura.dev/documentation/performance-profiling/) | Capture supported runtime measurements and explain evidenced hotspots. | Trace/counter artifacts, reproducible capture conditions, and measured comparison for an optimization claim. |
| [Custom agents and workflows](https://www.tryaura.dev/documentation/custom-agents/) | Delegate independent work concurrently, honor dependencies, integrate results, and expose agent progress. | Scheduler, isolation, ownership, and dependency tests. |
| [Sandbox review](https://www.tryaura.dev/documentation/filesystem-sandbox/) | Stage asset changes, inspect affected assets, and persist verified job-owned changes while handling C++ separately. | Saved delta, candidate manifest, conflict checks, and local commit. |
| [Gameplay verification](https://www.tryaura.dev/documentation/verification-agent/) | Run the game, exercise the feature, examine runtime evidence, and repair/retest failures. | Requirement-linked observations and results, including captured visual evidence where relevant. |
| [Crash recovery](https://www.tryaura.dev/documentation/crash-recovery/) | Restore a consistent job after editor/service failure and resume eligible work. | Fault-injection results and reconciled operation receipts. |
| [Conversation and progress](https://www.tryaura.dev/documentation/) | Preserve threads, show current work/agent activity and usage, and export results. | Restart/reconnect test, progress events, and a saved report. |

## Mode and context rules

Ask mode is read-only with respect to project code/assets. It may maintain tool-owned indexes and caches. Plan mode may write tool-owned specification/plan artifacts but does not implement project changes. Agent mode executes the agreed specification under the existing autonomy and dependency-approval policy. Starting an already authorized job must not create repeated approval prompts for ordinary tool operations.

Context selection supports named asset/file lookup, current editor selection, and Content Browser drag-and-drop or an equivalent native control. Support image references and extraction from Markdown, PDF, DOCX, PPTX, XLSX, and HTML through the approved dependency set. Keep context scoped and visible per conversation/job; refresh referenced targets after changes.

Quick search must work before a semantic index is ready. Indexing is cancellable and configurable by included/excluded folders, records freshness, and yields editor resources. Embedding clients, if used, are OpenAI-backed and obtained through the centralized model module.

## Explicit differences and remaining gaps

The required baseline is scoped to Unreal on the selected engine/platform and to OpenAI. It does not include Unity/Godot support, Aura's hosted billing/model marketplace, or its proprietary internal architecture. The docked interface and external IDE/MCP access are required. A separate standalone desktop application, headless editor execution, and browser-based Slices remain deferred.

Audio generation, MetaSound authoring, and external IDE/MCP access are required release workflows. Their detailed contracts, feasibility gates, and client tests are defined below. They are no longer deferred functionality.

Niagara editing, performance investigation, audio workflows, and external IDE/MCP access are included in the required baseline. Any unsupported engine operation, platform-specific profiler category, or generation-quality limit must be visible in the capability matrix. A missing required outcome blocks completion of the full release; an implementation milestone can only claim its tested subset.

## Functional comparison procedure

Maintain representative prompts and observable expected outcomes for every required row. Measure this tool on those fixtures and link the produced assets, operation receipts, tests, captures, and known gaps. Documentation establishes the reference feature set; claims of equal speed, reliability, visual quality, or success rate require a separate measured comparison. New engine or Aura features do not silently expand this versioned release contract.

# Repository baseline and reuse

The implementation base is [o0grip0o/AUE_TOH](https://github.com/o0grip0o/AUE_TOH), an Autopilot fork. The reference commit is [48966d174939487cc759fdf8560f2bed6e717676](https://github.com/o0grip0o/AUE_TOH/tree/48966d174939487cc759fdf8560f2bed6e717676).

| Existing component | Intended reuse |
| --- | --- |
| `autopilot/mcp.py` | Stateful external-agent testing interface, including long-operation handling. |
| `autopilot/agents/external.py` | Research, harness writing, episode execution, and reporting controlled by an external agent. |
| `autopilot/agents/session.py` | Episode management, test evidence, and report handling after removing Jev-specific assumptions. |
| `autopilot/kit/` | Gameplay observations, controllers, navigation helpers, and the harness contract. |
| `autopilot/engines/unreal.py` | Unreal adapter and exported project context. |
| `autopilot/bridge.py` | Plugin communication and connection lifecycle. |
| `autopilot/media.py` and `autopilot/memory.py` | Evidence capture and local memory, subject to provider and data-flow review. |
| `plugin/unreal/Autopilot/` | Existing Unreal plugin modules and useful UI/service plumbing. |

The existing agent selector chooses an implementation backend; it is not the proposed development supervisor. Its provider integrations, Jev decision calls, visual-model paths, and report gates need adaptation. Preserve usable components behind adapters and keep upstream-derived code distinguishable from the new development-agent package.

The supported distribution must not silently call Aura, TypeSafe, Anthropic, or another AI service. Retire their active runtime paths and mandatory dependencies from this application's supported execution path. An existing upstream feature is not evidence that the new provider-restricted path already works. Local Ollama gameplay decisions are the only approved non-OpenAI model path.

# Proposed system architecture

Use a local Python service for orchestration and a native Unreal plugin for the docked interface and engine-specific integrations. Keep model calls, filesystem work, and long-running jobs off the editor game thread.

| Component | Responsibility |
| --- | --- |
| Docked Unreal panel | Conversation, specification review, job progress, agents/tasks, dependency requests, controls, and evidence. |
| External MCP frontend | Authenticated project-bound client access to inspection, plans, jobs, events, approvals, and artifacts without creating a second supervisor. |
| Local service | Session lifecycle, LangGraph execution, background workers, events, persistence, and process supervision. |
| Supervisor graph | Requirements, planning, delegation, result integration, verification routing, and blocker escalation. |
| Deterministic scheduler | Dependency checks, bounded concurrency, resource ownership, task lifecycle, and deadlines. |
| Specialist registry | Built-in/custom/temporary definitions with explicit tool access and output contracts. |
| Editor gateway | Sole route for coordinated live-editor operations, project identity checks, capability discovery, and mutation receipts. |
| Filesystem and build tools | Scoped patch application, source inspection, builds, packaging, process tracking, and local Git operations. |
| Testing adapter | Autopilot-derived observation, harness execution, gameplay input, and evidence. |
| Local state and artifact stores | Workflow checkpoints, task events, project knowledge, candidate snapshots, and reports. |

The default connection is local. The panel and service use a versioned, authenticated loopback protocol with request identifiers and reconnect support. The service validates project and editor identity before tools run. Do not expose Unreal MCP directly as a remote service.

UE MCP is experimental and its available capabilities depend on enabled toolsets. Discover the actual catalog, record supported operations, and extend missing workflows with approved custom toolsets. Keep one serialized live-editor request queue initially. [Epic Unreal MCP documentation](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor)

# Specialist agents and ownership

| Role | Owns | Expected outputs |
| --- | --- | --- |
| Supervisor | Agreed requirements, plan, task dependencies, delegation, integration decisions, and final status. | Versioned specification, task graph, progress, blockers, final evidence summary. |
| Project researcher | Existing project structure, relevant assets/classes, conventions, tool capabilities, and implementation options. | Referenced findings and resolved object/class/asset paths. |
| C++ specialist | Native gameplay classes, components, interfaces, build configuration, and compiler-error repair. | Scoped code patches, diagnostics, and implementation notes. |
| UE behavior specialist | NPC decision logic and the behavior systems listed below. | Behavior plan, asset/configuration changes, task contracts, transition tests. |
| Blueprint and UI specialist | Blueprint graphs, components, defaults, UMG widgets, and C++/Blueprint connections. | Asset-operation plans, compiled assets, and interaction/UI checks. |
| Level and material specialist | Encounter layout, navigation requirements, asset placement, materials, lighting, and references. | Level/material changes, dependency inventory, and validation results. |
| Asset specialist | Asset discovery, free-source retrieval, generation, conversion, import, rigging/animation workflows, and provenance. | Importable assets, generation recipes, source records, and quality checks. |
| Audio specialist | Sound effects, ambience, music, synthetic voice, audio imports, MetaSound graphs, and gameplay playback connections. | Audio files/recipes, configured sound assets, and playback evidence. |
| VFX specialist | Niagara systems, emitters, effect materials, parameters, and gameplay connections. | Effect asset changes and compile/runtime evidence. |
| Performance specialist | Reproducible captures, supported engine counters/traces, and evidence-based bottleneck investigation. | Referenced captures, measurements, coverage limitations, and verified optimization results. |
| Test specialist | Test design from the agreed contract, harnesses, runtime assertions, packaged execution, and reproduction steps. | Structured test results and evidence. |
| Reviewer | Independent assessment of implementation and evidence against the agreed contract. | Pass, fail, or inconclusive findings tied to requirements. |

Each worker gets a focused brief and the minimum tools required. Return structured results and artifact references rather than adding every worker transcript to the supervisor conversation. LangChain's supervisor/subagent pattern supplies context isolation; the application must add the scheduler and resource policy. [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)

Custom specialists are project-local definitions of role, instructions, input/output schema, and permitted tools. Temporary specialists inherit a subset of the supervisor's permissions and expire with their assignment. Creating a role does not authorize dependency installation or unrestricted shell/editor access.

The supervisor owns delegation. Workers request additional help through it. A global worker limit and task budget prevent recursive agent creation from escaping scheduler control.

# UE behavior specialist requirements

The behavior specialist must create, inspect, modify, and explain Behavior Trees, Blackboards, StateTrees, AI Controller configuration, AI Perception, navigation-dependent behavior, and EQS queries.

It owns decision structure: priorities, transition conditions, cancellation/abort behavior, cooldowns, target validity, loss-of-target handling, and recovery from unreachable destinations. It defines Blackboard key names/types and the contract between sensors, native logic, and decision assets.

The C++ specialist supplies native tasks, services, controllers, evaluators, or components when required. The Blueprint/UI specialist supplies Blueprint implementations and presentation connections. The behavior specialist validates the final connections rather than assuming that separately generated pieces are compatible.

Required failure cases include invalid or destroyed targets, missing keys, unreachable positions, interrupted movement, loss of perception, state re-entry, and empty EQS results. Tests must inspect observable state transitions and resulting movement/interaction, not just the shape of a graph.

The first release needs a Behavior Tree benchmark plus separate StateTree and EQS fixtures. Creating one guarded-door encounter does not exercise every behavior capability.

If a required operation is missing from the enabled UE MCP toolsets, the task must identify the missing capability. It may implement an approved extension or report a blocker; it must not fabricate an asset or tool result.

# Proposed job and task lifecycle

The supervisor converts an agreed specification into a directed acyclic task graph. It identifies interfaces before parallel implementation, schedules independent tasks together, and waits for required outputs before dependent integration.

A typical job follows: establish requirements, inspect/preflight, plan, research and draft in parallel, apply changes through scoped gateways, build, validate, playtest, package, independently review, then persist verified results and commit locally. Failures route to bounded diagnosis and repair; missing decisions become blockers.

| Control | Required semantics |
| --- | --- |
| Pause | Stop scheduling new work and reach a safe tool boundary. Show pausing until in-flight operations stop or settle. |
| Resume | Recheck project identity, candidate hashes, ownership, and tool health before dispatching more work. |
| Cancel | Stop new work, propagate cancellation, release gameplay inputs/owned processes, and preserve recoverable artifacts. |
| Blocked task | Record the exact missing decision/capability and continue unrelated tasks when their assumptions remain valid. |
| Failed task | Record diagnostics, the affected requirements, and allowed recovery attempts. |
| Completed job | Every required check passes for the exact candidate delivered; all required work is resolved. |

The scheduler, rather than model instructions alone, enforces allowed paths, tool access, ownership, dependency readiness, and resource limits. Workers may reason concurrently; source application and live-editor mutations require ownership checks.

Proposed prototype defaults are three active AI workers, one live-editor operation, one build/package process, and three repair attempts per failed task. These are configurable starting values, not measured capacity or confirmed user limits. A task reaching its limit becomes blocked or failed with a diagnostic report.

Do not change an agreed requirement or weaken a failing acceptance test to manufacture a pass. A specification change requires explicit developer agreement and a new specification revision.

# Proposed state and contracts

Use typed, versioned records. Keep large logs, screenshots, code patches, and videos outside graph state and reference them by artifact ID, relative path, and content hash.

| Record | Minimum fields |
| --- | --- |
| JobSpec | Goal, scope, requirement IDs, constraints, acceptance criteria, approved dependencies, specification revision. |
| ProjectContext | Canonical project path, engine version, editor identity, source branch/base commit, content/config hashes, tool catalog, sandbox ID. |
| TaskSpec | ID, role, goal, dependencies, read/write targets, input references, acceptance criteria, budget, attempt, and status. |
| AgentSpec | Role, instructions, tool allowlist, model role, input/output schemas, lifetime, and parent job. |
| TaskResult | Status, changed targets, artifact references, diagnostics, unmet criteria, evidence, usage, and remaining blockers. |
| OperationReceipt | Operation ID, task, target, precondition, requested change, observed result, before/after hash, and timestamps. |
| VerificationResult | Requirement ID, check type, pass/fail/inconclusive, candidate hash, steps, observations, expected result, and artifacts. |
| DependencyRequest | Name, version, source, reason, direct/transitive installation plan, project impact, and approval status. |
| JobReport | Specification revision, candidate/commit, completed tasks, test results, known limitations, usage, and recovery history. |

A checkpointer persists thread/workflow state. A separate local store holds project knowledge. Checkpoints do not restore assets, undo source changes, or establish that an external operation failed. [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

Every mutation uses a stable operation ID and a checked precondition. After an ambiguous timeout or crash, inspect the target and receipt before retrying. Avoid duplicate actor creation, repeated imports, or repeated commits caused by replay.

# Centralized OpenAI model access

**Required module:** `ue_agent/llm/openai_models.py`.

All construction and configuration of LangChain OpenAI models lives in this module. Other modules obtain instances through functions and may bind task-specific tools to the returned model. They must not instantiate `ChatOpenAI` directly.

Proposed access functions are `get_supervisor_model()`, `get_specialist_model(role)`, `get_gameplay_decision_model()`, `get_vision_model()`, `get_image_client()`, `get_audio_client()`, and `get_embedding_model()` when semantic retrieval uses embeddings. Image and audio generation may require separate OpenAI clients; their construction belongs behind the same centralized provider boundary.

The factory reads model-role settings, credential references, timeouts, retry policy, output schema requirements, and supported features from configuration. Model IDs and parameters are configurable. The prototype must select and pin tested model/API combinations rather than promise arbitrary model interchangeability.

Credentials come from a local secret store or environment configuration. Never serialize raw keys into jobs, prompts, project memory, committed files, or logs. Cache client/model objects only against the relevant credential reference and configuration.

Tests replace the factory with injected fakes. Enforce the construction boundary with a repository check and runtime/provider tests.

Keep OpenAI construction centralized and provide a separate local Ollama gameplay client getter. Provider selection is explicit, with no automatic cross-provider fallback. Other AI workloads remain OpenAI-backed. This boundary does not imply that vision, image generation, reasoning, and fast gameplay decisions use one model or one endpoint.

# Editor sandboxing and source changes

The required editing reference is Aura's use of UE asset sandboxing in the active editor. Aura documents staged asset saves, acceptance back into project files, shared capture of manual edits, and exclusion of C++ changes. It also identifies overwrite and dependency-chain limitations. Treat these as constraints on the design, not as independent workspaces for each agent. [Aura filesystem sandbox](https://www.tryaura.dev/documentation/filesystem-sandbox/)

## Proposed coordinated editing policy

Create an agent-owned local job branch from a recorded baseline before project modifications. Preserve the original branch reference. If pre-existing changes or unsaved editor state cannot be attributed safely, pause for the developer to establish the baseline. Do not silently stash, commit, overwrite, or discard their work.

Use a named asset sandbox for the job. Queue editor mutations through one gateway with explicit file/asset ownership. Manual edits to unrelated targets may continue; edits affecting an agent-owned target or dependency invalidate the corresponding preconditions and require reconciliation.

C++ specialists draft patches independently. Apply those patches only through checked filesystem operations on the job branch, record before/after hashes, and run the appropriate build. Do not assume Unreal's asset sandbox isolates source files.

Display the active project, branch, sandbox, current editor operation, and affected targets in the docked panel. Independent agent contexts must not be described as independent engine worlds.

## Candidate verification and persistence

External cooking/packaging may not automatically see staged sandbox assets. Before packaging, materialize the exact source/configuration/content candidate, including the sandbox delta, into a disposable validation workspace. An alternative sandbox-aware cook path is acceptable only after its behavior is demonstrated on UE 5.8.3.

The validation workspace is a testing artifact, not the normal interactive editing mode. Keep its build outputs separate, resolve real Git LFS content, and preserve project-relative asset identities. The manifest records additions, modifications, deletions, and the relevant dependency closure.

Run packaging and packaged-game checks against that manifest. Before final persistence, confirm the editor candidate is still identical. Persist only the job-owned, dependency-consistent asset changes and commit those changes with the job's C++/configuration changes. Developer edits outside the job must stay outside its commit.

Native sandbox operations, source snapshots, and Git commits form separate mechanisms. A crash between them must be recoverable through recorded receipts and hashes. Do not claim transactionality or reliable per-file rollback without testing it.

If native sandboxing, candidate materialization, or state attribution fails the platform gate, the default behavior is to stop affected mutations and report the blocker. A direct-write fallback requires a separately agreed execution policy.

# C++ Blueprint UI and level capabilities

The tool supports both C++ and Blueprints as first-class implementation targets. The supervisor chooses a combination from the job specification and project conventions and documents the boundary between them.

| Workflow | Required operations and checks |
| --- | --- |
| C++ | Inspect source, create/modify gameplay code, update module dependencies through approval policy, compile, parse errors, repair, and rebuild. Use full rebuild/restart when a change cannot safely use an incremental path. |
| Blueprints | Inspect classes/graphs/defaults/components, create/edit graphs and references, connect native functions, support functions/events, interfaces, structs, enums, data tables, and Timeline workflows, compile, and validate references. |
| Widgets | Create/edit UMG widgets, bindings/events, visibility, interaction prompts, and viewport placement; verify runtime behavior. |
| Levels | Create/edit encounter maps, transforms, collision, references, navigation requirements, lighting, and material assignments. |
| Materials and assets | Create/edit materials and instances, import/reuse assets, configure references, and verify visible results and import diagnostics. |
| Niagara | Create/edit a representative particle system, configure emitters/materials/parameters, connect it to gameplay, compile, and inspect runtime output. |
| Performance investigation | Capture supported runtime measurements, identify an evidenced hotspot, document unavailable categories, and verify a proposed improvement without changing acceptance behavior. |
| Audio and MetaSounds | Generate/import audio, configure sound assets and MetaSound graphs, connect triggers/parameters, and verify actual playback in PIE and the packaged candidate. |

Resolve targets by stable object/asset paths and verified properties, using labels and source references as discovery clues. Cache resolutions within a job and invalidate them after renames, map changes, reloads, or object destruction. Ambiguous matches must be resolved before mutation.

Maintain an operation capability matrix for UE 5.8.3: available native tool, required extension, tested status, and known limits. A Blueprint-looking asset or successful tool response is insufficient; read back and compile the resulting asset.

# Gameplay control and Autopilot adaptation

Replace Jev's decision-making with an explicit decision-policy interface. The selected default is local Ollama/Nimble through `POST /v1/systemone`. OpenAI Decisions (`POST /v1/decisions`, `gpt-6-luna`) remains an explicitly selectable alternative, never an automatic fallback. Both require gameplay accuracy and latency measurements. See the [Ollama Nimble documentation](https://ollama.com/library/nimble) and [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions).

The `nimble` tag does not establish that the installed weights are Bespoke-Nimble-9B-v2. Verify checkpoint provenance, license, exact installed model digest, quantization, and serving version before calling it v2 or declaring a tested release configuration. The adapter must not install Ollama or download models automatically. Use loopback transport without inherited proxies, credentials, redirects, or implicit remote endpoints. The documented Ollama interface supports 2–26 choices, a 64 KiB request body, and an 8,192-token effective prompt limit; the server enforces tokenization limits. Keep structured game observations compact and benchmark alongside Unreal on the reference Mac. Treat backend confidence as a provider-specific signal, not a calibrated chance of correctness. Audit prompt classification, reporting, frame evaluation, memory processing, and all alternate agent paths as well as the obvious runtime calls.

The model chooses among structured, currently legal gameplay actions. Code performs movement, aiming, button timing, observation sampling, and other fast control locally. Do not place a network model call on every Unreal frame.

A decision includes action ID, bounded arguments, expected effect, expiration, and relevant observation version. Validate outputs against a schema and current legal actions before execution. Late responses are discarded when their preconditions have expired.

Local controllers continue a valid bounded action or select a safe idle behavior while awaiting a decision. Enforce action timeouts, cancellation, input release, and stall detection. Record decision latency, stale/invalid responses, action outcomes, token usage, and cost estimates.

Measure the policy on the benchmark and on a time-sensitive combat fixture. The prototype gate determines which interactions it can control reliably; no response-rate or real-time-combat guarantee is assumed.

The existing harness contract and observation/controller utilities may remain. Refactor session/report rules that require a minimum number of Jev decisions so deterministic assertions and model-driven episodes can be evaluated on their own evidence. Preserve the distinctions between test failure, control-policy failure, an unplayable environment, and inconclusive evidence.

Autopilot's MCP frontend keeps run state and exposes long-call continuation. Keep its session alive during an episode and honor the wait protocol. A still-running response must not cause the job to start the same episode again.

Vision review uses OpenAI and evidence from the run. Give a visual reviewer neutral observation questions where practical, then compare the observations with the agreed criterion. LLM visual interpretation supplements runtime assertions; it is not an exhaustive correctness proof.

# Asset discovery generation and quality

Search suitable existing project assets first, then the configured libraries and free sources. The developer can override this preference in a specification. Record the chosen source, original identifier/URL where available, local path, usage terms/attribution metadata, and imported/generated asset paths.

Reading a configured library authorizes scoped discovery. Importing into the job does not authorize editing the original library. A missing Fab item or download that needs authentication becomes a clear user action; do not invent an entitlement or treat a paid item as free.

Generation must cover the requested asset classes:

| Asset type | Proposed path | Minimum verification |
| --- | --- | --- |
| Textures and UI images | OpenAI image generation followed by import and asset configuration. | Valid files, dimensions, transparency/color settings where required, correct references, and visible placement. |
| Procedural meshes | OpenAI-authored generation code using Unreal geometry tools or an approved local content tool. | Geometry imports, scale/orientation, normals, collision as required, and material slots. |
| Materials | UE material/instance tools and generated textures where useful. | Successful compilation, correct parameter assignments, and visual checks in the target scene. |
| Level layouts | Structured layout plans plus UE placement/navigation tools. | Reachability, collision, spawn/interaction access, and referenced assets. |
| Rigged characters | Reuse suitable rigs/assets or generate geometry and rigging through an approved local pipeline driven by OpenAI-authored scripts. | Skeleton hierarchy, skin weights, scale, supported poses, and visible deformation checks. |
| Animations | Procedural keyframes, suitable library reuse/retargeting, and approved local animation tooling. | Import/playback, skeleton compatibility, transitions, foot placement where applicable, and root-motion settings. |
| Sound effects ambience and music | OpenAI-supported generation where validated, or OpenAI-authored deterministic local synthesis using approved tools. | Decodable non-silent output, requested duration/loop behavior, no unacceptable clipping, and successful UE import/playback. |
| Synthetic voice | A tested OpenAI speech-generation interface with configured voice/output settings. | Correct spoken content, usable format/duration, and runtime playback. |

The OpenAI policy for content generation does not require every transformation to be performed by an AI service. Deterministic local geometry, rigging, image, and animation tools are permitted after dependency approval.

Rigged-character and animation creation are required workflows, but output quality is a release gate. Start with a documented functional style/complexity target. A failed generation attempt must remain a failed or blocked criterion rather than silently becoming an unrigged/static substitute.

Audio generation and MetaSound authoring are required. Final visual style, character complexity, texture budgets, audio style, loudness/loop requirements, and quality thresholds must be defined in each job specification.

# Audio generation and MetaSound workflows

An audio specialist must support sound effects, ambience, music loops, synthetic voice, UE audio imports, MetaSound authoring, and gameplay playback connections. It can reuse approved assets, generate alternatives, and make targeted changes to existing graphs.

Specify audio category, duration, loop points, variation count, intended trigger, spatial/attenuation requirements, and quality criteria in the job contract. Save generation settings, source/provenance, output format, sample rate/channel configuration, and resulting UE asset paths.

All AI generation and analysis use OpenAI through `get_audio_client()` or the appropriate central role getter. Validate the selected API/model's output capabilities; an interface documented for speech is not evidence that arbitrary music or sound-effect generation is supported. [OpenAI audio documentation](https://developers.openai.com/api/docs/guides/audio)

Where a requested non-speech sound cannot be produced directly by a tested OpenAI interface, an OpenAI specialist may author deterministic local synthesis or a MetaSound-based procedure using approved tools. Such a path must meet the same job criteria and be labelled with its method. Do not silently introduce another AI provider, replace requested music with a speech clip, or accept low-quality output as a pass. Failure to meet a required audio category is a release blocker until the pipeline or requirement is explicitly revised.

Create and configure sound assets and MetaSounds with referenced sources, trigger/control inputs, looping, gain/pitch, and variation selection as required. Expose relevant parameters to C++ or Blueprints and connect them to real game events. The reference workflow includes importing/generating audio and composing playback controls in MetaSounds. [Aura audio workflow](https://www.tryaura.dev/documentation/audio/)

Validate file decoding, non-silence, duration, excessive clipping, loop continuity, graph validity, correct source references, triggers, spatial settings, and stop/retrigger behavior. Capture actual playback or an audio loopback/test-render signal; a successful graph compile or transcript alone is insufficient. Specify capture conditions so a muted output device does not become a false product failure.

The fixture creates a door/unlock effect, a short ambient/music loop, and a synthetic voice prompt; it verifies those assets in PIE and in the exact packaged candidate. Retain generated samples and recipes for regression tests, and separately run a live generation capability check. Document voice/sound style and quality rather than assuming production-quality results from the presence of an API.

# Dependency approvals and autonomous boundaries

The tool asks before adding each new tool, Python package, Unreal plugin, or other dependency. Show the reason, exact source/version, installation scope, expected transitive packages, project-file changes, and whether a restart/build is needed. An initial installer can present its complete bundled dependency manifest as the installation decision.

Persist decisions by dependency identity/version and scope. A newly requested dependency or changed version is a new approval condition. Declining one does not authorize substitution with another unapproved dependency; the supervisor may use an existing approved alternative or report a blocker.

Operate within the selected project, configured read-only libraries, and tool-owned working directories. Apply scoped C++ patches and UE operations through validated gateways. Keep source-control actions limited to local job branches and commits.

Temporary specialists cannot expand these boundaries. Downloaded asset metadata, project files, retrieved documents, and tool output are context, not permission to execute unrelated instructions.

Requests that require a paid asset, unresolved access, an unapproved installation, a changed game requirement, or a destructive conflict with manual work become blockers. Continue independent tasks only when their assumptions remain valid.

The autonomy goal is low-intervention execution inside the agreed job. Approvals required by the dependency policy remain explicit even when the job is otherwise unattended.

# Docked interface and developer controls

The plugin provides an editable conversation with the supervisor, a specification/acceptance view, a task graph or task list, worker status, the current editor operation, and an evidence/report view. Provide Ask/Plan/Agent mode selection, an asset/file context picker, Content Browser drag-and-drop or equivalent selection, image/document attachments, thread history, and exportable reports.

Show meaningful job states: gathering requirements, planned, running, waiting for editor, waiting for developer, verifying, pausing, paused, recovering, completed, failed, and cancelled. Explain the active state and next action in plain language.

The developer can inspect task ownership, dependencies, attempted changes, model/tool activity summaries, compiler diagnostics, test outcomes, usage, and the active branch/sandbox. Show a proposed dependency with approve/decline controls when needed.

Pause, resume, and cancel must remain responsive while model requests or builds run. Distinguish requesting cancellation from confirming that a tool/process has actually stopped. Preserve completed artifacts and identify any operation whose outcome is uncertain.

Requirement revision and live reprioritization during an active job are outside the initial control set. A substantive change is handled by pausing/ending the current job and establishing a new specification revision. Direct conversations with individual specialists are not required.

Support switching between persisted local conversations and viewing prior job reports. Keep the panel usable after the service or editor reconnects; the local service is the authority for job status. External IDE clients attach to the same jobs and durable state; closing either interface does not duplicate or cancel work by itself.

# External IDE and MCP access

Expose the local tool service through a project-bound MCP frontend so the developer can use it from an IDE or compatible coding client. VS Code and a Codex client are the proposed first tested integrations; generic MCP compatibility is an interface goal, not a promise that every client version is validated. Aura's external-client tooling is the functional reference. [Aura IDE and MCP workflow](https://www.tryaura.dev/documentation/aura-ide-mcp/)

The docked panel and external clients connect to one persistent local supervisor, scheduler, editor gateway, and artifact store. An external request must not bypass sandboxing, tool permissions, dependency approvals, job ownership, source-control limits, or the requirement for OpenAI-backed internal agents with the approved local gameplay-policy exception.

Provide a read-only inspection/planning surface and a mutating job-execution surface. Inspection covers project discovery, source/asset lookup, context, diagnostics, plans, status, and evidence. Mutation occurs through the managed jobs and scoped operations already defined in this specification.

Proposed client actions are inspect project, propose/refine plan, start job, get status/events, pause, resume, cancel, answer a dependency request, and retrieve artifact/report references. Return stable project/job/operation IDs and structured errors. Long jobs acknowledge quickly and expose progress; reconnecting clients resume event consumption without restarting the job.

Generate project-local client configuration using the actual managed interpreter, executable, paths, and transport. Preview configuration changes and preserve unrelated MCP entries. Test the chosen stdio adapter and/or authenticated loopback transport for each supported client. Keep OpenAI credentials in the local service; do not copy raw keys into IDE configuration or expose arbitrary artifact paths.

Asset editing, PIE, and editor-dependent validation require a reachable compatible Unreal instance. Code inspection and planning can work offline against local project context with that status visible. Starting the editor uses the recorded project and the existing recovery/lifecycle policy; this feature does not promise unattended headless rendering or cooking behavior beyond the tested build pipeline.

A client that cannot display an approval must return an actionable waiting state and allow the developer to resolve it in the docked panel. Disconnecting a client must not approve a request or cancel an ongoing job. Duplicate start/control requests require idempotent handling.

Acceptance tests attach both interfaces to the same benchmark, verify identical state/evidence, exercise mode restrictions and approval delivery, interrupt/reconnect the client, and issue overlapping requests to prove editor mutation ordering. A third-party coding client's own model/account is outside this service's inference boundary; adding that client does not authorize a different provider for the tool's internal AI work.

# Persistence project memory and recovery

Use persistent local storage for conversation threads, graph checkpoints, task records, operation receipts, approvals, job reports, and a separate project knowledge store. SQLite with a versioned schema is the proposed first implementation; evidence/media stays in referenced artifact directories.

Project memory contains verified conventions, implementation decisions, asset/class mappings, useful recipes, and successful test harnesses. Record source references and the project revision/capability assumptions. Invalidate stale knowledge when the relevant code, assets, or engine version changes.

Do not store raw API keys or silently upload project memory to a shared service. Only job-relevant content is sent to OpenAI for configured AI tasks. Disable inherited training/data-sharing paths in the supported distribution unless separately introduced as an explicit feature.

Recovery is automatic when consistent state can be established:

1. Detect editor/service loss and stop new mutations.

2. Preserve checkpoints and receipts; release gameplay inputs and owned process resources where reachable.

3. Reconnect to the intended editor or restart the recorded project when appropriate.

4. Restore the recorded sandbox context and inspect Git, files, assets, and in-flight operation outcomes.

5. Mark completed operations, invalidate stale evidence, and retry only when the result is known or the operation is safely repeatable.

6. Resume ready tasks. If manual/unsaved work creates an unresolved conflict, present a precise blocker rather than discarding it.

A recovered graph checkpoint alone does not establish project consistency. Recovery must cover failures during asset persistence, compilation, PIE, packaging, and final commit.

Provide documented export and cleanup for local history/media. Artifact retention duration and disk quotas remain configurable values to set during prototype measurements.

# Verification and completion contract

Every implementation job must satisfy four gates: successful compilation, asset validation, automated PIE testing, and a packaged-game smoke test. A task-level pass is provisional until the job's required integration checks pass.

| Gate | Required evidence |
| --- | --- |
| Build | Exact target/configuration, engine/toolchain identity, command outcome, compiler diagnostics, and candidate hash. |
| Asset validation | Blueprint/material compilation, required references, maps/assets loading, import diagnostics, and dependency checks. |
| PIE tests | Named assertions derived from the specification, observed state/input sequence, expected result, pass/fail/inconclusive, and reproduction evidence. |
| Packaged execution | Cook/package result for the same candidate, standalone launch, intended map/player/UI, a representative interaction, no fatal crash, and clean termination. |
| Independent review | Requirement-to-evidence mapping, any missing checks, and a final pass/fail/inconclusive decision. |

Use UE automation/functional testing and targeted assertions for reproducible behavior. Autopilot-derived playtesting exercises interactions and finds additional failures. Keep control-policy errors separate from product defects. [Epic automation framework](https://dev.epicgames.com/documentation/unreal-engine/automation-test-framework-in-unreal-engine)

The proposed first packaging target is a local macOS Development build. The packaged test runs without relying on the editor's MCP connection. Editor-only inspection tools cannot prove packaged behavior. A runtime test helper must be included in the tested Development configuration if that helper is used.

“Packaged-game smoke test” here means a bounded launch and interaction check; it does not imply Unreal's specific one-second Smoke Test classification. Signing/notarization for public distribution and Shipping-build verification require later explicit requirements.

Acceptance tests exercise the normal player interaction path. Direct state writes may establish a documented test setup, but changing a success flag, teleporting past a required obstacle, or unlocking the door through an inspection tool cannot satisfy the gameplay criterion.

Freeze the job's acceptance contract before implementation. The reviewer checks independent observations and test outcomes. Passing a generated test suite establishes only the behavior it actually checks. Mark untested, unsupported, skipped, and inconclusive criteria explicitly; required skipped/inconclusive criteria prevent a completed status.

The final report includes specification revision, tested candidate and local commit, changed files/assets, all gate results, screenshots/video where useful, remaining limitations, recovery history, and measured usage.

# Guarded door integration benchmark

The confirmed scenario combines a guarded locked door, C++ interaction logic, UI prompts, and an encounter level. The following fixture details are proposed acceptance criteria for that scenario.

## Fixture

Start from a clean, empty UE 5.8.3 project. Create a small single-player third-person map with a functioning player/controller/camera/input setup, a player spawn, one locked door, a discoverable key, a guard patrol route, an investigation/search area, and an exit trigger. Include collision, navigation, required lighting/materials, and the necessary imported or generated assets.

Implement the interaction contract and door/key state in C++ and expose appropriate functions/events to Blueprints. Implement the prompt widget and scene connections in Blueprints/UMG. Use a Behavior Tree and Blackboard for the main guard fixture. Exercise StateTree in a separate equivalent behavior fixture and EQS in a focused investigation fixture.

## Functional assertions

| ID | Required observed result |
| --- | --- |
| BENCH 01 | The intended map loads, the player is possessed, and input works. |
| BENCH 02 | Entering interaction range shows the appropriate prompt; leaving range hides it. |
| BENCH 03 | Interacting without the key leaves the door locked and reports the unmet condition. |
| BENCH 04 | Collecting the key updates the C++ inventory/state and makes that state visible to the interaction logic. |
| BENCH 05 | Interacting with the correct key unlocks/opens the door and updates collision/passage correctly. |
| BENCH 06 | Repeated interaction does not duplicate unlock events, key objects, or exit rewards. |
| BENCH 07 | The guard patrols configured reachable points. A configured hearing stimulus starts investigation. |
| BENCH 08 | Player detection causes chase; target loss leads to search/return behavior according to the agreed fixture rules. |
| BENCH 09 | Closed-door or unreachable-path conditions produce bounded recovery rather than an endless movement loop. |
| BENCH 10 | The EQS fixture selects a valid point when available and handles an empty result. |
| BENCH 11 | The StateTree fixture starts, transitions, recovers, and stops correctly without a competing Behavior Tree driving the same controller. |
| BENCH 12 | The exit trigger produces the expected completion state after the door interaction. |
| BENCH 13 | Asset references and Blueprint/material compilation pass; runtime logs contain no unhandled error caused by the fixture. |
| BENCH 14 | A package built from the same candidate launches independently, shows the UI, permits the representative door interaction, and terminates successfully. |
| BENCH 15 | Key pickup/door/guard events trigger the intended generated audio through configured sound/MetaSound assets; loop and stop conditions work and the packaged candidate includes the audio. |
| BENCH 16 | The same benchmark can start from the external IDE interface and continue under the same job identity and controls in the docked panel. |

Distance, perception range, cooldowns, search duration, and recovery timeouts are explicit fixture configuration, not values invented during a test run. Set and version them before implementation.

The workflow must visibly delegate at least two independent tasks, serialize conflicting editor changes, integrate C++ with Blueprint/behavior assets, and produce requirement-linked evidence.

Inject one controlled compiler failure and one gameplay assertion failure. The supervisor must diagnose, assign a bounded repair, and rerun affected verification without weakening the acceptance contract. Recovery and dependency-approval behavior have separate fault tests.

The benchmark is a regression fixture for the tool. Broader workflow coverage additionally requires the StateTree, EQS, generation/rigging, installation, and lifecycle tests below.

# Tool acceptance and reliability tests

The following tests are release requirements. Fixture-specific values and quantitative performance thresholds are finalized during the prototype.

| Area | Acceptance test |
| --- | --- |
| Delegation | A task graph with independent and dependent tasks completes in correct dependency order; ownership conflicts do not produce concurrent writes. |
| Agent registry | Built-in, developer-defined, and temporary specialists run with the assigned context, schema, and tool subset; spawning limits are enforced. |
| Provider boundary | Development, vision, and content-generation AI calls use OpenAI; only gameplay decisions may use local Ollama. Provider selection is explicit, never a silent fallback; role getters are injectable and LangChain OpenAI construction stays centralized. |
| Editor identity | With two editors/projects available, operations target the selected instance and reject mismatched project/engine identity. |
| Sandbox | Asset saves are staged, native source edits are tracked separately, and manual changes are detected without being included in the agent commit. |
| Candidate packaging | A staged asset change is present in the packaged candidate and matches the final committed content manifest. |
| Build repair | A compiler diagnostic reaches the responsible task and is repaired within the configured attempt limit or reported as blocked/failed. |
| Behavior | Behavior Tree, StateTree, EQS, perception, target validity, navigation, and recovery fixtures satisfy their assertions. |
| Content generation | Every requested asset class has an import/use fixture, including a rigged character and a working animation. Record recipes and provenance. |
| Approval | An unapproved dependency never installs; approval permits only the specified scope/version; denial leaves a clear alternative or blocker. |
| UI controls | Pause/resume/cancel work while models, PIE, and builds are active; the UI distinguishes pending controls from completed controls. |
| Crash recovery | Interrupt editor/service during mutation, build, PIE, packaging, and commit. Reconcile outcomes without duplicate actors/imports/commits or lost developer edits. |
| Source control | Agent changes produce local branch commits; no push, pull request, merge into the original branch, or unrelated user change is included automatically. |
| State persistence | Restarting the service preserves conversation, task ownership, approvals, job evidence, and resumable state. |
| Installation | Source and packaged installations launch the correct service and pass preflight on the declared macOS/processor matrix. |
| Aura modes | Ask and Plan cannot mutate project code/assets; an agreed plan can start Agent mode and retain its specification and context. |
| Project context | Context selection, an image, and a design document affect the correct task; quick search works while indexing runs, and renames invalidate stale index entries. |
| Niagara | A gameplay-triggered effect is created, edited, compiled, played, and included in the validated candidate. |
| Profiling | A reproducible capture yields referenced measurements and coverage limits; a claimed improvement is checked against a comparable baseline. |
| Audio | Generate a sound effect, an ambient/music loop, and a synthetic voice clip; import them, create/configure MetaSound playback, and verify audible output and gameplay triggers in PIE and a package. |
| External IDE access | A VS Code MCP client and a Codex client inspect/plan/start jobs; progress, pause/resume/cancel, dependency approvals, and evidence match the docked panel. |
| Client reconnect and concurrency | IDE disconnect/reconnect preserves jobs; duplicate requests do not duplicate work; requests from both interfaces share editor ownership and mutation ordering. |
| Functional baseline | Every required row of the Aura matrix has a passing scenario and evidence. Unsupported subfeatures are visible; deferred differences are named in release notes. |
| End to end | The guarded-door job passes every gate and produces the report and exact local commit. Repeatability trials disclose success rate and failures. |

Test the scheduler, policy, state migrations, and provider routing without a live editor where practical. Use live UE fixtures for actual tool/asset semantics, and standalone runtime checks for packaging. A mock MCP server cannot validate engine behavior.

Cost, job duration, packaging duration, peak memory, decision latency, UI responsiveness, repair count, and token usage are measured for each benchmark. Publish the actual reference machine and configuration with results. Select worker limits and time/cost thresholds from those measurements.

Proposed release repeatability gate: three consecutive clean-baseline runs of the integration benchmark on the declared reference setup. This is a candidate threshold for review, not a measured result.

# Proposed package and module boundaries

Add the development harness under a new `ue_agent/` package while retaining reusable Autopilot pieces behind explicit adapters.

| Path | Responsibility |
| --- | --- |
| `ue_agent/llm/openai_models.py` | Central model/client objects and getter functions. |
| `ue_agent/config.py` | Validated runtime, model-role, path, budget, and capability settings. |
| `ue_agent/domain/` | Versioned job/task/result/operation/verification contracts. |
| `ue_agent/orchestration/` | Supervisor graph, deterministic scheduling, budgets, and lifecycle. |
| `ue_agent/agents/` | Specialist definitions, registry, isolated context, and temporary roles. |
| `ue_agent/tools/` | Scoped filesystem, process/build, dependency, and Git operations. |
| `ue_agent/unreal/` | MCP client, editor gateway, target resolution, sandbox adapter, and candidate materialization. |
| `ue_agent/testing/` | Autopilot adapter, decision policy, test runners, evidence, and review. |
| `ue_agent/assets/` | Library adapters, source inventory, visual/audio generation, conversion, rigging/animation, and import recipes. |
| `ue_agent/storage/` | Checkpoints, event/receipt log, project memory, artifacts, and migrations. |
| `ue_agent/audio/` | Audio generation/synthesis adapters, analysis, imports, MetaSound operation plans, and playback validation. |
| `ue_agent/clients/` | MCP-facing inspection/job/control/artifact adapters and tested external-client configuration. |
| `ue_agent/service/` | Local API/events, service startup, authenticated connection, and process recovery. |
| `plugin/unreal/` | Docked panel, native integrations, and appropriate development-only runtime test helpers. |
| `tests/` | Core tests and explicitly separated live-engine fixtures. |
| `docs/` | Specification, setup, supported capabilities, operation contracts, and benchmark results. |

Local user secrets and caches stay outside Git. Versionable project settings/specifications may live under a project-owned configuration directory. Worker artifacts, sandbox files, logs, generated test packages, and local databases must have explicit ignore/cleanup rules.

Keep runtime gameplay test helpers separate from editor UI modules. The packaged application must not require the Python supervisor to function as the game. Distinguish tool installation artifacts from generated game packages.

# Installation and platform validation

Provide source setup and a packaged Unreal plugin distribution with an explicit managed-worker installation manifest. Source installation must document the exact tested Python minor version and locked dependencies. The existing repository declares Python 3.12 or newer, but that declaration does not validate every Python/platform combination.

The macOS preflight checks the selected UE 5.8.3 installation, compatible native plugin build, required toolsets, project identity, build toolchain, Git/Git LFS, OpenAI credentials, writable working paths, and approved dependency availability. Verify native video/image and other binary dependencies as part of packaging.

Parameterize Windows-oriented defaults and build scripts inherited from the fork. Do not claim cross-platform support solely because the coordinator is written in Python.

Keep service/plugin protocol versions explicit. On upgrade, migrate supported local state or provide a clear incompatibility message without discarding active jobs. Supply worker/service cleanup and uninstall instructions.

The supported macOS version range, processor architectures, minimum RAM/storage, and reference test machine remain release-matrix decisions. They must be declared and tested before publishing a compatibility claim. Other operating systems remain architectural portability targets until their native integration tests pass.

# Implementation milestones and feasibility gates

Before extending the standalone coding harness, run the [guarded-door benchmark](GUARDED_DOOR_BENCHMARK.md)
using local Codex and Unreal's native MCP tools. Compare actual completion, evidence, human intervention,
and recovery across independently reset attempts. Use the [result template](../bench/guarded_door/result.template.md)
and add custom UE execution/verification components only for demonstrated gaps. The existing LangGraph foundation
remains experimental; this baseline does not depend on it and does not establish full product parity.

| Milestone | Deliverable and exit criterion |
| --- | --- |
| 0 Feasibility | Demonstrate UE 5.8.3/macOS tool discovery, native sandbox staging and persistence, C++ build/restart, exact-candidate packaging, local Ollama/Nimble gameplay decisions and explicit OpenAI selection, a basic generated rig/animation pipeline, OpenAI-only audio generation/synthesis, MetaSound playback, and external-client connectivity. Record concrete gaps and measurements. |
| 1 Harness foundation | Centralized models, typed contracts, persistent supervisor, scheduler, agent registry, local service, and docked Ask/Plan/Agent modes, context selection, indexing/search, history, and progress/controls. External MCP access uses the same service state. Core lifecycle tests pass. |
| 2 Development workflows | C++ plus Blueprint/UI integration, Behavior Tree/Blackboard, Perception/navigation, StateTree, EQS, level/material tooling, Niagara, and MetaSound/gameplay-audio workflows. Targeted live-engine fixtures pass. |
| 3 Asset workflows | Library discovery, free-source imports, image/procedural generation, character rigging/animation, audio generation/import, provenance, and dependency approvals. Every required asset class has a passing fixture. |
| 4 Verification and recovery | Adapted Autopilot runtime with OpenAI development agents and local Ollama gameplay decisions, independent review, packaged checks, performance investigation, exact candidate receipts, fault recovery, and local commit delivery. |
| 5 Release validation | Source and packaged installation, guarded-door repeatability, declared platform matrix, measured usage/performance, VS Code/Codex integration, audio fixtures, and Aura functional-baseline scenarios pass the release gates. |

No milestone automatically removes a confirmed feature from the release scope. If a feasibility gate fails, record the blocker and the concrete redesign or scope decision needed before continuing affected work.

Native sandbox coverage, packaging staged assets, generated rig quality, OpenAI-only audio generation quality, and gameplay-policy latency/memory contention are the highest-risk gates. Treat tool ownership rules as application coordination; they do not create an operating-system security sandbox for arbitrary native or Python code.

Numeric task budgets, monetary limits, and reference performance targets are chosen from prototype measurements. The tool must still enforce bounded requests, action timeouts, worker limits, and repair attempts during the prototype.

# Decisions to finalize during implementation

| Decision | Current position | Needed before release |
| --- | --- | --- |
| Mac support matrix | macOS required; exact processor/version minimums unspecified. | Declare and validate the tested machine/OS/architecture combinations. |
| Model configurations | Central OpenAI factory; local Ollama/Nimble gameplay default; explicit OpenAI Decisions alternative. | Pin tested reasoning, vision, image-generation, gameplay checkpoint/digest, and serving configurations. |
| Audio generation quality | Sound effects, ambience, music, voice, and MetaSounds required under the OpenAI-only AI policy. | Prove suitable generation or approved local synthesis paths, quality, API/model compatibility, and packaged playback. |
| IDE compatibility | External MCP access required; proposed first tested clients are VS Code and Codex. | Pin client versions/transports, setup flows, approval delivery, and reconnect behavior. |
| Gameplay responsiveness | Local Ollama decisions select actions; explicit OpenAI alternative; local code executes fast control. | Measure latency, stale decisions, and success on interaction and combat fixtures. |
| Art quality | Requested asset classes confirmed; final visual style unspecified. | Define functional generation fixtures and job-specific visual acceptance criteria. |
| Dependency set | New dependencies require approval. | Validate and present the base installation manifest and any local content-tool additions. |
| Sandbox adapter | Native asset staging in the active editor is the chosen reference. | Prove UE 5.8.3/macOS APIs, persistence behavior, and exact candidate export. |
| Spending and resource caps | Meter usage now; monetary limits follow measurements. | Choose defaults and expose configurable pause thresholds. |
| Retention | Local history and project memory required by the proposed persistence design. | Choose artifact/media cleanup defaults and disk quotas. |
| Distribution hardening | Source and packaged plugin installation required. | Select the release signing/update strategy appropriate to its distribution. |

These decisions affect implementation parameters or feasibility. The confirmed product scope remains the source of truth until the developer agrees to a revision.

# Source references

The external references establish existing engine/framework behavior and the repository baseline. The proposed architecture and acceptance fixtures above are project design choices.

- [AUE TOH reference commit](https://github.com/o0grip0o/AUE_TOH/tree/48966d174939487cc759fdf8560f2bed6e717676)

- [Autopilot MCP frontend](https://github.com/o0grip0o/AUE_TOH/blob/48966d174939487cc759fdf8560f2bed6e717676/autopilot/mcp.py)

- [External-agent integration](https://github.com/o0grip0o/AUE_TOH/blob/48966d174939487cc759fdf8560f2bed6e717676/autopilot/agents/external.py)

- [Testing session and report rules](https://github.com/o0grip0o/AUE_TOH/blob/48966d174939487cc759fdf8560f2bed6e717676/autopilot/agents/session.py)

- [Current gameplay runtime and Jev dependency](https://github.com/o0grip0o/AUE_TOH/blob/48966d174939487cc759fdf8560f2bed6e717676/autopilot/runtime.py)

- [Unreal plugin descriptor](https://github.com/o0grip0o/AUE_TOH/blob/48966d174939487cc759fdf8560f2bed6e717676/plugin/unreal/Autopilot/Autopilot.uplugin)

- [Dependency manifest](https://github.com/o0grip0o/AUE_TOH/blob/48966d174939487cc759fdf8560f2bed6e717676/pyproject.toml)

- [Aura filesystem sandbox](https://www.tryaura.dev/documentation/filesystem-sandbox/)

- [Epic Unreal MCP](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor)

- [LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)

- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

- [Epic automation framework](https://dev.epicgames.com/documentation/unreal-engine/automation-test-framework-in-unreal-engine)

- [Running Unreal automation tests](https://dev.epicgames.com/documentation/unreal-engine/run-automation-tests-in-unreal-engine)