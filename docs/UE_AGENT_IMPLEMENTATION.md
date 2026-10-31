# AUE TOH implementation status

This branch starts the [development-agent specification](UE_AGENT_SPEC.md). It contains a working Python
orchestration foundation and a developer harness. The docked Unreal interface, editor mutations, and complete
Aura-like feature set are not implemented yet.

## Available now

- Centralized OpenAI model/client getter functions in `ue_agent/llm/openai_models.py`.
- A bounded-choice gameplay policy defaulting to local Ollama/Nimble, with explicit OpenAI Decisions selection,
  legal-action checks, deadlines, and no cloud fallback or decision retries.
- Typed specifications, task DAG validation, scopes, worker results, and verification contracts.
- Built-in specialist definitions, custom registration, and temporary roles with inherited tool restrictions.
- A real LangGraph execution loop over an asynchronous scheduler with bounded concurrency, resource ownership,
  dependencies, timeouts, bounded retries, and pause/resume/cancel state.
- A persistent SQLite task/event journal, atomic task claims across connections, and explicit reconciliation of
  interrupted claims. A restarted graph reads the journal rather than replaying completed tasks.
- An isolated LangChain planner and research/draft worker adapter using the centralized model functions.
- Exact-candidate verification gates: worker completion alone never marks an implementation job complete.
- An offline demo, persisted status/control commands, and an optional OpenAI planning command.

## Run the developer harness

```bash
uv venv
uv pip install -e ".[dev,ue-agent]"
python -m ue_agent --help
python -m ue_agent --db .ue_agent/demo.sqlite3 demo
python -m ue_agent --db .ue_agent/demo.sqlite3 status <job-id>
```

The demo runs deterministic workers through the actual LangGraph scheduler. It makes no OpenAI requests,
connects to no editor, changes no project assets, and ends at `awaiting_verification`. It is an orchestration
exercise, not a generated game or a successful gameplay test.

This slice has no live usage/cost accounting, dependency-approval interface, or automatic editor recovery yet.
Those must be connected before unattended implementation jobs are enabled. Custom/temporary role registration
is currently application code; persisting user-defined role definitions is also a follow-up slice.

For a real model-generated **plan only**, set `OPENAI_API_KEY` and `UE_AGENT_MODEL` in the environment. Select an
OpenAI chat model enabled for your account; planning has no default model and tests make no paid calls. The separate
gameplay policy defaults to local Ollama/Nimble through `/v1/systemone`, without an OpenAI key. Selecting
`UE_AGENT_GAMEPLAY_PROVIDER=openai` uses `gpt-6-luna` through `/v1/decisions` via the central OpenAI getter.
The caller supplies legal actions and a monotonic deadline and must recheck observation freshness before applying any returned action. Live Autopilot integration remains pending.

```bash
python -m ue_agent plan --project /path/to/Game.uproject \
  --goal "Describe the feature to implement" \
  --criterion "Describe an observable acceptance condition"
```

The result is persisted as an unapproved Plan-mode job. It cannot execute itself. The `resume` control changes
an existing execution job's control state; it does not authorize a plan or launch a background service.

Tests and lint:

```bash
ruff check .
pytest -q
```

For this Linux container, regression checks use `AUTOPILOT_SANDBOX=process` and remove inherited HTTP/SOCKS
proxy variables. The legacy runtime's auto-selected bubblewrap path did not initialize its MCP fixture here;
the explicit process mode passed that fixture and matches the legacy plain-child mode used on macOS.
This is Autopilot's Python execution sandbox, separate from Unreal's asset filesystem sandbox. Production
defaults and CI sandbox settings are unchanged. The full regression run recorded 500 passes, five skips, and one
legacy process-listing failure (`test_the_listing_has_this_process_and_what_started_it`); that environment-sensitive
assertion is not changed by this branch. Live macOS/UE integration still needs its own validation.

## Gameplay backend configuration

`choose_action()` reads `GameplaySettings` independently from chat-model configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `UE_AGENT_GAMEPLAY_PROVIDER` | `ollama` | `ollama` for local decisions or explicit `openai`. |
| `UE_AGENT_GAMEPLAY_MODEL` | `nimble` locally, `gpt-6-luna` for OpenAI | Exact configured decision model/tag. |
| `UE_AGENT_OLLAMA_URL` | `http://127.0.0.1:11434` | Loopback HTTP service; proxies and redirects are disabled. |

Ollama and model weights must already be installed and approved. This adapter never installs packages, pulls
weights, or starts a service. HTTP transport uses the existing `httpx` dependency; no Ollama SDK is required.
The generic `nimble` tag is not verified as the v2 checkpoint. Record provenance and pin the actual model digest
and serving version before release. The implementation enforces 2–26 local choices and a 64 KiB request body;
Ollama enforces its effective 8,192-token prompt limit. Invalid responses, missing models, and timeouts yield no
action and never trigger a cloud fallback. Backend confidence values are not assumed comparable or calibrated.

Tests use a fake HTTP transport and fake OpenAI endpoint. No local service, model weights, or Mac gameplay
performance have been tested. Live Autopilot session/report migration remains outstanding.

## Execution and trust boundaries

The SQLite journal is the authority for job/task state. LangGraph currently carries only a job ID and routing
flags; native LangGraph checkpoint integration is not added in this slice. In-flight claims survive a restart
and remain reserved until their executor is confirmed stopped and their actual effects are reconciled.
`reconcile_interrupted` is an internal trusted boundary, not automatic crash recovery or an exposed user tool.

The built-in LangChain worker currently supports analysis and draft proposals. Its tools are trusted,
application-supplied read-only callables. It blocks live-editor tasks before invoking a model. Scope and lease
records coordinate work; they are not an operating-system sandbox. The editor/filesystem adapters must enforce
the recorded scopes when actual mutations are connected.

Task success describes the assignment's result, not implemented UE behavior. Only trusted test adapters may
select an integrated candidate and record build, asset, PIE, and package evidence. There are no real UE test
adapters in this slice, and LLM worker reports cannot submit verification receipts.

The new `ue_agent` path does not import the legacy `autopilot` runtime or invoke its Aura/TypeSafe/Anthropic
integrations. The legacy commands and installation dependencies remain available. Removing/replacing those
paths for the final supported distribution remains a separate migration.

## Next implementation slices

1. Connect a project-bound UE MCP inspection adapter and capability preflight on UE 5.8.3/macOS.
2. Implement a mutation gateway, operation receipts, native asset sandbox integration, and source patch application.
3. Add the docked panel/local service and external MCP clients using the same persisted jobs and editor queue.
4. Build trusted candidate materialization, compile, asset, PIE, and packaged-game test adapters.
5. Adapt Autopilot's controls/observations to the selected gameplay decision policy and remove Jev-specific report gates.
6. Add behavior/Blueprint/level workflows, generation/rigging, Niagara, audio/MetaSounds, and profiling fixtures.

These slices implement the specification incrementally; they do not remove required features from release scope.
