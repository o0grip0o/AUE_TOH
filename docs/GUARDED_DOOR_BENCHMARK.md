# Guarded-door benchmark: local Codex + native Unreal MCP

This experiment measures what Codex and Unreal's existing tools can deliver before adding a custom agent harness.
It does not reduce the long-term requirements in [UE_AGENT_SPEC.md](UE_AGENT_SPEC.md), prove Aura parity, or certify a release.
The baseline excludes Aura, the AUE runtime, legacy Autopilot, and Nimble; evaluate their adapters only as measured follow-ups.

## Prepare a disposable baseline

1. Work on the developer's Mac with UE **5.8.3**, compatible Xcode, and Codex already installed.
2. Create a fresh **Blank C++**, single-player project named `GuardedDoorBenchmark`, without starter content.
   Use primitive meshes and existing engine resources; imported art, generated assets, and additional packages are unnecessary.
3. Initialize the project's Git repository and exclude generated/build/user-state files, including `.ue_agent/`.
   Configure Git LFS if already available and used for binary assets. Finish the connection setup below, then commit
   the untouched, configured baseline before starting any trial. Do not install dependencies during a run.
4. Create a separate local branch per trial, such as `benchmark/guarded-door-01`. Keep all C++ edits on this branch.
   Start each repeatability trial from the same clean baseline in a fresh disposable project copy/worktree.
5. The native `ModelContextProtocol` server and toolsets must be available in this engine. Enable the existing
   **Unreal MCP** and **All Toolsets** plugins in **Edit > Plugins** for this disposable project, then restart.
   If absent, record **BLOCKED**. Do not install dependencies, plugins, alternate agents, or the `ue_agent` harness.
6. Run Codex locally on that Mac. Keep the native MCP server on loopback; do not tunnel it or expose it remotely.
   A ChatGPT/Desktop connection or a cached tool list alone does not prove local Codex has editor access.

## Connect and inspect before writing

- If Codex already has one working Unreal connection, reuse it; do not create a duplicate.
- Otherwise, with the existing native plugin enabled, start its server using the editor console command
  `ModelContextProtocol.StartServer`. Use its actual endpoint, which may differ from the default.
- For a manually managed Codex connection, the existing engine command
  `ModelContextProtocol.GenerateClientConfig Codex` generates configuration only when the destination is absent.
  Preserve existing Codex configuration and unrelated MCP entries; review any required connection edit.
  Launcher builds write beside the `.uproject`; source builds write at the workspace root beside `Engine/`.
- Open Codex's `/mcp` view, discover the advertised Unreal toolsets/schemas, and make a **read-only editor call**.
  Confirm absolute project identity, engine patch/build, current map, PIE state, dirty assets, and compilation state.
  Read relevant registered project Agent Skills and conventions using the actually exposed tools.
- If identity differs from the intended disposable project, or live inspection fails, stop with **BLOCKED**.
  Record unavailable preflight fields explicitly; do not infer their values from client settings or filenames.
- Save a recovery point before changes. Use native asset sandbox staging only if this build exposes and verifies it.
  That sandbox is experimental and does not isolate C++; the disposable project and Git branch remain necessary.

## Fixed acceptance contract

Use centimeters, single-player, a controllable third-person pawn, and a small encounter map.
Implement C++ interaction/state logic, real Behavior Tree/Blackboard assets, and a visible UI widget.

| ID | Observable requirement |
| --- | --- |
| LEVEL-01 | The map starts at PlayerStart with the controllable pawn, a collidable door, a reachable key, a guard, and navigation coverage. The exit cannot be reached through the closed door or surrounding geometry. |
| CXX-01 | C++ owns key possession and door lock/open state. Interactions are range-checked at 200 cm, idempotent, and reset correctly for a fresh session. |
| DOOR-01 | Within range, pressing E without the key leaves the door locked and collision blocking the exit; interacting beyond 200 cm has no effect. |
| DOOR-02 | Interacting with the key within 200 cm grants possession once and removes/disables further pickup. Interacting with the door then unlocks/opens it once and allows the pawn to reach a marked exit volume. |
| UI-01 | The widget shows `Locked - key required` near the locked door, `Open door [E]` after key pickup, and `Door open` after opening. It hides the interaction prompt out of range. No stale prompt survives restarting PIE. |
| AI-01 | The guard's AI Controller runs an assigned Behavior Tree using a Blackboard with typed `TargetActor` and `HomeLocation` keys, and visibly patrols between two reachable points before detection. |
| AI-02 | Configure sight radius 1,500 cm, lose-sight radius 1,800 cm, and peripheral half-angle 45 degrees. A player 1,000 cm directly ahead with clear sight is acquired and pursued. Record target/movement evidence. |
| AI-03 | On losing sight, the guard clears its target within 5 s after full visual occlusion, returns home, and resumes patrol. Destroying/invalidating the target produces no accessed-none error, endless chase, or stuck task. |

Record runtime values/events or deterministic assertions for state, distances, transitions, and exit entry.
Screenshots/video establish visible behavior; a plausible graph or an agent's narrative alone does not establish these outcomes.
StateTree, EQS, combat depth, content generation, and campaign scope remain separate long-term fixtures.

## Bound execution and editor ownership

- Use the same proposed budget for each trial: **60 minutes of active agent work**, **120 minutes total elapsed time**, and at most **three repair iterations in total**.
  Record setup and waiting time separately; record natural recovery events without deliberately crashing the editor.
  Limit an individual build/PIE operation to 15 minutes and packaging to 30 minutes.
  A timed-out operation must be inspected/reconciled before retrying; never start a duplicate build or PIE session.
- Keep **one editor writer**. Helpers may research or draft C++, but all editor mutations, asset saves, PIE transitions,
  and compilation must pass through one coordinator and complete before the next dependent operation starts.
- Do not edit assets while PIE or compilation is active. Recheck project identity after reconnection/restart.
- Do not silently install dependencies, weaken the acceptance criteria, substitute fake behavior assets, or switch to another agent harness.
  Missing tools/capabilities become named **BLOCKED** items; actual assertion failures are **FAIL**.

## Evidence tied to the exact candidate

Save artifacts outside project `Content/`, in a per-trial directory such as `<project>/.ue_agent/benchmarks/<run-id>/`. This is only an artifact folder; no AUE runtime is needed.
The report must identify the local Git commit, dirty tracked files, untracked source/assets, engine/tool versions,
map, test commands/settings, and hashes of the source/config/assets used to build the candidate.
Save all edited assets before selecting this manifest. A build-relevant code/asset/config change invalidates prior candidate evidence; regenerate the manifest and rerun the required gates.
If staging assets in the native sandbox, prove that the materialized candidate includes those exact assets.

| Gate | Required artifact |
| --- | --- |
| GATE-BUILD | Editor/game build command, exit code, and full diagnostics; native code and dependent Blueprints compile. A Live Coding success alone does not prove packaged compilation. |
| GATE-ASSETS | Blueprint/widget compilation, Behavior Tree/Blackboard validation, references, assigned controller/tree/Blackboard, map/default-mode configuration, and navigation coverage evidence. |
| GATE-PIE | Three fresh sessions reproduce every criterion with logs/assertions and screenshots/video. Each session resets key/door state. Include failures and repairs. |
| GATE-PACKAGE | Cook/build/package command, exit code, logs, artifact path/hash, and standalone smoke evidence for the same candidate: locked rejection, key/unlock/exit, prompts, and guard detection. An editor screenshot is not package evidence. |

Use **PASS**, **FAIL**, **INCONCLUSIVE**, **BLOCKED**, or **NOT RUN** for each criterion/gate. Never claim PASS without an artifact.
If launch/input/observation is unsupported for the packaged game, retain its build artifact and mark the smoke test BLOCKED.
A candidate is accepted only when every required criterion and gate passes; otherwise report the remaining gap.

## Report measurements and decide what to build

Use the [result template](../bench/guarded_door/result.template.md) for each trial.
Run three independent trials from the clean baseline; preserve unsuccessful trials in the results.
For each trial record: elapsed/active/wait times, repair counts, human interventions with reasons/minutes,
tool-call failures/timeouts, model/API identifiers, available token usage and billed API cost, and peak memory if measurable.
Record tool/model latency samples (median/p95 only with sample count), including editor waits and any unavailable metrics.
The benchmark-specific monetary limit remains undecided until prototype costs are measured.
Subscription allocation or missing billing telemetry is **UNAVAILABLE**, not zero cost. Do not invent cost estimates.
Report per-criterion success, whole-run success, and unassisted completion separately. Manual gameplay, builds,
or repairs after the request count as interventions; assisted success is not autonomous completion. Compare the same hardware, engine, settings, and budgets.
Add custom tooling only for a repeated measured gap, such as mutation ownership, evidence collection, or project conventions.

## Copy-paste prompt for local Codex

Replace the two absolute paths and the trial ID below. Have the disposable project open in the intended UE 5.8.3 editor.

```text
Read /absolute/path/AUE_TOH/docs/GUARDED_DOOR_BENCHMARK.md as the acceptance contract.
Target project: /absolute/path/GuardedDoorBenchmark/GuardedDoorBenchmark.uproject
Trial ID: guarded-door-01

Use this local Codex session and the already configured native Unreal MCP connection.
First discover its actual available tools and read their current schemas and relevant project Agent Skills.
Make read-only calls to confirm the target project's absolute identity, UE build, map, PIE/compile state,
and dirty assets before editing. Stop BLOCKED if live identity cannot be established or differs.
Do not invent tool names or arguments; invoke only operations confirmed by the discovered schemas.
Do not install dependencies, start another agent harness, expose MCP remotely, or overwrite Codex configuration.
Use the separate local benchmark Git branch and a saved recovery point. Do not modify the acceptance contract. Keep one coordinator as the editor writer.
Use an experimental native asset sandbox only if it is available and its candidate export can be verified.
Implement CXX-01, DOOR-01/02, UI-01, AI-01/02/03, and LEVEL-01 with real code/assets and observable behavior.
Follow the fixed run/repair limits. Preserve all failures, human interventions, and unavailable measurements.
Verify compile, assets, three fresh PIE sessions, and the exact packaged candidate's standalone smoke test.
Create the candidate manifest and artifact-linked criterion/gate report described in the benchmark.
If an operation is unsupported, report it as BLOCKED with the missing capability; never fabricate a passing result.
Do not push, merge, or change unrelated files. End with local candidate identity, evidence paths, results, and gaps.
```

## Reference documentation

- [Epic Unreal MCP](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor)
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
