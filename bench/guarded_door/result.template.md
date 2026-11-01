# Guarded-door benchmark result

**Status: NOT RUN.** This template contains no engine observations or successful verification claims.
Copy it to the disposable game's `.ue_agent/benchmarks/<run-id>/result.md` for each attempt.
Keep logs, video, manifests, and usage exports beside that report; do not commit credentials or raw environment dumps.
See the [benchmark procedure](../../docs/GUARDED_DOOR_BENCHMARK.md).

## Environment and configuration

| Field | Observed value |
| --- | --- |
| Run ID and baseline variant | NOT RECORDED; baseline = local Codex + native UE MCP |
| Date/time, including timezone | NOT RECORDED |
| Mac model, processor, RAM, macOS | NOT RECORDED |
| UE full version/build and Xcode | NOT RECORDED |
| Project path and baseline Git commit | NOT RECORDED |
| Codex version, model, reasoning setting | NOT RECORDED |
| Enabled MCP toolsets and project instructions | NOT RECORDED; link discovery output |
| Assets/plugins/dependencies already present | NOT RECORDED |
| Final candidate Git commit | NOT RECORDED |
| Candidate manifest and SHA-256 | NOT RECORDED; include Source, Content, Config, project/plugin descriptors |
| Final working-tree status | NOT RECORDED; explain any uncommitted differences |

## Effort and outcomes

| Metric | Observed value |
| --- | --- |
| Prerequisite/setup time | NOT MEASURED |
| Task start/end and total elapsed time | NOT MEASURED |
| Repair iterations and final stopping reason | NOT MEASURED |
| Unassisted completion | NOT RUN; requires all gates/criteria and zero task-phase human rescues |
| Human intervention count and active minutes | NOT MEASURED; retain a dated list of interventions below |
| Model/API usage and billable cost | UNKNOWN; record actual usage/source, never assume zero |
| Editor crashes, restarts, recovery actions | NOT OBSERVED; distinguish untested recovery from successful recovery |
| Resource contention/peak memory | NOT MEASURED |

Each acceptance row starts NOT RUN. Allowed outcomes after execution: PASS, FAIL, INCONCLUSIVE, or BLOCKED.
For PASS, cite the observation and its actual artifact. A tool's success message or an agent's summary alone is insufficient.
Record artifact paths relative to this report, command/tool invocation, timestamps, and the tested candidate identity.
If the candidate changes after a check, mark that check stale and rerun it before claiming overall completion.

## Acceptance results

| ID | Required observable result | Outcome | Observation and evidence |
| --- | --- | --- | --- |
| CXX-01 | Interaction behavior is implemented in C++, integrated with the player and door | NOT RUN | None |
| DOOR-01 | Without the key, interacting leaves the door closed and impassable | NOT RUN | None |
| DOOR-02 | After key acquisition, interacting opens the door and the player passes through | NOT RUN | None |
| UI-01 | Prompt appears in range, reflects key/lock state, and hides out of range | NOT RUN | None |
| AI-01 | AI Controller uses a Behavior Tree and Blackboard to patrol reachable points | NOT RUN | None |
| AI-02 | Guard detects the player under the specified sight conditions and pursues | NOT RUN | None |
| AI-03 | Guard loses the target under the specified conditions and resumes patrol | NOT RUN | None |
| LEVEL-01 | Third-person player can traverse the encounter, collect the key, and reach the exit | NOT RUN | None |
| GATE-BUILD | Native editor/game build succeeds for this candidate | NOT RUN | None |
| GATE-ASSETS | Modified Blueprints compile, references validate, and required assets are saved | NOT RUN | None |
| GATE-PIE | The fixture's runtime acceptance checks pass without new relevant errors | NOT RUN | None |
| GATE-PACKAGE | This candidate's packaged Mac Development build launches and passes critical smoke checks | NOT RUN | None |

## Interventions, failures, and gaps

List every human action needed after the agreed request, failed attempt, missing native tool, workaround,
and dependency request. Keep the original acceptance criteria fixed. Record declined actions and unresolved blockers.
If a custom script was necessary, retain it and distinguish an existing tool from newly authored test code.

NOT RECORDED.

## Conclusion and follow-up

Overall outcome: **NOT RUN**. All required criteria and gates must pass against the same candidate for a completed attempt.
Required missing evidence remains BLOCKED or INCONCLUSIVE; it cannot be replaced by an LLM verdict.
Repeat with three independently reset project copies before drawing a repeatability conclusion. Summarize success count,
total developer effort, failures, and unknown measurements. A successful fixture does not establish full Aura parity
or autonomous production of a multi-hour game.

Smallest custom addition justified by the observed gap: **UNDETERMINED UNTIL RUN**.
