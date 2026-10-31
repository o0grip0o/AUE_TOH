"""The real LangGraph runtime with offline workers and durable SQLite state."""

import asyncio
import sqlite3

import pytest
from pydantic import ValidationError

from ue_agent.agents.registry import AgentRegistry, AgentSpec, builtin_registry
from ue_agent.domain import (
    Effect,
    Gate,
    JobSpec,
    JobStatus,
    Mode,
    Outcome,
    Plan,
    TaskSpec,
    TaskStatus,
    Verification,
    WorkerReport,
)
from ue_agent.orchestration import TaskBlocked, TaskScheduler, execute_job
from ue_agent.storage import JobStore


def task(name="inspect", **kwargs):
    return TaskSpec(id=name, role="researcher", instruction=f"Inspect {name}", **kwargs)


def job_spec(**kwargs):
    return JobSpec(project_path="/fixture/Game.uproject", goal="Implement the agreed feature",
                   criteria=("The observed result matches the requirement",),
                   **{"mode": Mode.AGENT, "approved": True, **kwargs})


@pytest.fixture
def store(tmp_path):
    with JobStore(tmp_path / "state.sqlite3") as value:
        yield value


def add(store, tasks=None, **spec_kwargs):
    return store.create_job(job_spec(**spec_kwargs), Plan(summary="Test plan", tasks=tuple(tasks or [task()])))


async def report(_):
    return WorkerReport(summary="Assignment finished; no engine verification claimed")


@pytest.mark.parametrize("tasks", [
    [task("a"), task("a")],
    [task("a", dependencies=("missing",))],
    [task("a", dependencies=("b",)), task("b", dependencies=("a",))],
])
def test_invalid_dependency_graphs_are_rejected(tasks):
    with pytest.raises(ValidationError):
        Plan(summary="Invalid", tasks=tasks)


@pytest.mark.parametrize("target", ["../secret", "/etc/file", "C:\\Source\\file", "Source/../file", "Source/*"])
def test_write_scopes_reject_ambiguous_or_escaping_targets(target):
    with pytest.raises(ValidationError):
        task(effect=Effect.DRAFT, write_targets=(target,))


def test_case_aliases_read_writes_and_unscoped_editor_mutations_are_rejected():
    for kwargs in ({"write_targets": ("Source/A.cpp",)}, {"effect": Effect.EDITOR},
                   {"effect": Effect.DRAFT, "write_targets": ("Source/A.cpp", "source/a.cpp")}):
        with pytest.raises(ValidationError):
            task(**kwargs)


@pytest.mark.parametrize("mode,approved", [(Mode.ASK, True), (Mode.PLAN, True), (Mode.AGENT, False)])
def test_execution_requires_approved_agent_mode(store, mode, approved):
    job_id = add(store, mode=mode, approved=approved)
    with pytest.raises(PermissionError):
        asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), report), job_id))
    assert store.snapshot(job_id).tasks[0].attempts == 0


def test_parallel_dispatch_dependency_context_and_unverified_completion(store):
    async def run():
        entered = set()
        both_started = asyncio.Event()
        finished = set()

        async def worker(context):
            name = context.task.id
            if name in ("native", "behavior"):
                entered.add(name)
                if len(entered) == 2:
                    both_started.set()
                await asyncio.wait_for(both_started.wait(), 2)
            else:
                assert finished == {"native", "behavior"}
                assert set(context.dependencies) == finished
            finished.add(name)
            return WorkerReport(summary=name)

        job_id = add(store, [task("native"), task("behavior"),
                             task("review", dependencies=("native", "behavior"))])
        result = await execute_job(TaskScheduler(store, builtin_registry(), worker, max_workers=2), job_id)
        assert result.status == JobStatus.AWAITING_VERIFICATION
        assert not result.verification and result.candidate_hash is None
        assert all(t.status == TaskStatus.SUCCEEDED for t in result.tasks)
        return job_id

    job_id = asyncio.run(run())
    assert [e["kind"] for e in store.events(job_id)].count("task.started") == 3


def test_worker_limit_and_same_target_ownership(store):
    async def run():
        active = peak = 0

        async def worker(_):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.005)
            active -= 1
            return WorkerReport(summary="Draft")

        tasks = [task(f"t{i}", effect=Effect.DRAFT, write_targets=(f"Source/{i % 2}.cpp",)) for i in range(6)]
        job_id = add(store, tasks)
        await execute_job(TaskScheduler(store, builtin_registry(), worker, max_workers=2), job_id)
        assert peak == 2

    asyncio.run(run())


def test_editor_mutations_serialize_even_for_distinct_assets(store):
    job_id = add(store, [task("one", effect=Effect.EDITOR, write_targets=("asset:/Game/A",)),
                         task("two", effect=Effect.EDITOR, write_targets=("asset:/Game/B",))])
    first = store.claim_ready(job_id, 3)
    assert len(first) == 1
    assert store.claim_ready(job_id, 3) == ()
    store.finish_task(job_id, first[0].spec.id, first[0].owner, TaskStatus.SUCCEEDED,
                      report=WorkerReport(summary="Observed receipt"))
    assert len(store.claim_ready(job_id, 3)) == 1


def test_atomic_claims_across_connections_and_stale_owners(tmp_path):
    path = tmp_path / "state.sqlite3"
    with JobStore(path) as one, JobStore(path) as two:
        job_id = add(one)
        claim = one.claim_ready(job_id, 1)[0]
        assert two.claim_ready(job_id, 1) == ()
        with pytest.raises(RuntimeError):
            two.finish_task(job_id, claim.spec.id, "wrong-owner", TaskStatus.SUCCEEDED,
                            report=WorkerReport(summary="Cannot steal this result"))
        assert two.snapshot(job_id).tasks[0].owner == claim.owner


def test_resources_are_shared_across_jobs_and_case_aliases(store):
    one = add(store, [task(effect=Effect.DRAFT, write_targets=("Source/Actor.cpp",))])
    two = add(store, [task(effect=Effect.DRAFT, write_targets=("source/actor.cpp",))])
    claim = store.claim_ready(one, 1)[0]
    assert store.claim_ready(two, 1) == ()
    store.finish_task(one, "inspect", claim.owner, TaskStatus.SUCCEEDED, report=WorkerReport(summary="Done"))
    assert len(store.claim_ready(two, 1)) == 1


def test_pause_resume_does_not_replay_completed_work(store):
    calls = []

    async def worker(context):
        calls.append(context.task.id)
        if context.task.id == "one":
            store.control(job_id, "pause")
        return WorkerReport(summary="Done")

    job_id = add(store, [task("one"), task("two", dependencies=("one",))])
    scheduler = TaskScheduler(store, builtin_registry(), worker)
    assert asyncio.run(execute_job(scheduler, job_id)).status == JobStatus.PAUSED
    assert calls == ["one"]
    store.control(job_id, "resume")
    assert asyncio.run(execute_job(scheduler, job_id)).status == JobStatus.AWAITING_VERIFICATION
    assert calls == ["one", "two"]


def test_resuming_a_plan_does_not_approve_it_or_label_it_running(store):
    job_id = add(store, mode=Mode.PLAN, approved=False)
    assert store.control(job_id, "pause") == JobStatus.PAUSED
    assert store.control(job_id, "resume") == JobStatus.PLANNED
    assert store.snapshot(job_id).spec.approved is False
    assert store.snapshot(job_id).tasks[0].attempts == 0


def test_cancel_propagates_to_active_worker_and_prevents_dependent_work(store):
    async def run():
        started, released = asyncio.Event(), asyncio.Event()

        async def worker(_):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                released.set()

        job_id = add(store, [task("one"), task("two", dependencies=("one",))])
        running = asyncio.create_task(execute_job(TaskScheduler(store, builtin_registry(), worker), job_id))
        await asyncio.wait_for(started.wait(), 2)
        store.control(job_id, "cancel")
        result = await asyncio.wait_for(running, 2)
        assert released.is_set()
        assert result.status == JobStatus.CANCELLED
        assert all(t.status == TaskStatus.CANCELLED for t in result.tasks)
        assert result.tasks[1].attempts == 0

    asyncio.run(run())


def test_retry_is_bounded_and_does_not_prevent_independent_work(store, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sensitive-test-key")
    calls = []

    async def worker(context):
        calls.append(context.task.id)
        if context.task.id == "fail":
            raise RuntimeError("sensitive-test-key must not reach the journal")
        return WorkerReport(summary="Done")

    job_id = add(store, [task("fail", max_attempts=2), task("independent"),
                         task("dependent", dependencies=("fail",))])
    result = asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), worker), job_id))
    assert result.status == JobStatus.FAILED
    assert calls.count("fail") == 2 and calls.count("independent") == 1
    assert "dependent" not in calls
    assert "sensitive-test-key" not in result.model_dump_json()
    assert "[redacted]" in result.tasks[0].error


def test_cancellation_before_coroutines_start_releases_their_claims(store, monkeypatch):
    job_id = add(store, [task(effect=Effect.DRAFT, write_targets=("Source/Actor.cpp",))])
    claim_ready = store.claim_ready

    def cancel_on_claim(job_id, limit):
        claims = claim_ready(job_id, limit)
        store.control(job_id, "cancel")
        return claims

    monkeypatch.setattr(store, "claim_ready", cancel_on_claim)
    result = asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), report), job_id))
    assert result.status == JobStatus.CANCELLED
    assert result.tasks[0].status == TaskStatus.CANCELLED
    another = add(store, [task(effect=Effect.DRAFT, write_targets=("Source/Actor.cpp",))])
    assert len(claim_ready(another, 1)) == 1


def test_editor_exception_is_not_blindly_retried(store):
    async def worker(_):
        raise RuntimeError("Outcome uncertain after mutation")

    job_id = add(store, [task(effect=Effect.EDITOR, write_targets=("asset:/Game/Actor",))])
    result = asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), worker), job_id))
    assert result.status == JobStatus.BLOCKED
    assert result.tasks[0].attempts == 1


def test_missing_capability_is_blocked_not_retried(store):
    async def worker(_):
        raise TaskBlocked("A new dependency needs approval")

    job_id = add(store)
    result = asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), worker), job_id))
    assert result.status == JobStatus.BLOCKED
    assert result.tasks[0].attempts == 1


def test_interrupted_claims_survive_restart_until_reconciled(tmp_path):
    path = tmp_path / "state.sqlite3"
    with JobStore(path) as store:
        job_id = add(store)
        claim = store.claim_ready(job_id, 1)[0]
    with JobStore(path) as store:
        result = asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), report), job_id))
        assert result.status == JobStatus.RUNNING and result.tasks[0].attempts == 1
        store.reconcile_interrupted(job_id, owner=claim.owner)
        result = store.snapshot(job_id)
        assert result.status == JobStatus.BLOCKED
        assert "reconciliation" in result.tasks[0].error
        with pytest.raises(RuntimeError):
            store.finish_task(job_id, "inspect", claim.owner, TaskStatus.SUCCEEDED,
                              report=WorkerReport(summary="Stale completion"))


def test_idempotent_job_creation_rejects_changed_payload(store):
    spec, plan = job_spec(), Plan(summary="Plan", tasks=(task(),))
    store.create_job(spec, plan, job_id="same-request")
    store.create_job(spec, plan, job_id="same-request")
    assert len(store.events("same-request")) == 1
    with pytest.raises(ValueError):
        store.create_job(spec.model_copy(update={"goal": "Different goal"}), plan, job_id="same-request")


def test_foreign_database_is_not_initialized_over(tmp_path):
    path = tmp_path / "foreign.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated(value TEXT)")
        db.execute("INSERT INTO unrelated VALUES('keep this')")
    with pytest.raises(ValueError, match="does not belong"):
        JobStore(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT * FROM unrelated").fetchall() == [("keep this",)]
        assert db.execute("PRAGMA application_id").fetchone()[0] == 0
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == [("unrelated",)]


def test_verification_is_required_for_exact_candidate_and_invalidated_by_changes(store):
    job_id = add(store)
    asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), report), job_id))
    candidate = "a" * 64
    receipt = Verification(gate=Gate.BUILD, outcome=Outcome.PASS, candidate_hash=candidate, evidence=("build.log",))
    with pytest.raises(ValueError):
        store.record_verification(job_id, receipt)
    store.set_candidate(job_id, candidate)
    for gate in Gate:
        store.record_verification(job_id, receipt.model_copy(update={"gate": gate}))
    assert store.snapshot(job_id).status == JobStatus.COMPLETED
    store.set_candidate(job_id, "b" * 64)
    assert store.snapshot(job_id).status == JobStatus.AWAITING_VERIFICATION
    assert not store.snapshot(job_id).verification
    with pytest.raises(ValueError):
        store.record_verification(job_id, receipt)


@pytest.mark.parametrize("outcome", [Outcome.FAIL, Outcome.INCONCLUSIVE])
def test_nonpassing_gate_prevents_completion(store, outcome):
    job_id = add(store)
    asyncio.run(execute_job(TaskScheduler(store, builtin_registry(), report), job_id))
    store.set_candidate(job_id, "a" * 64)
    for gate in Gate:
        verdict = outcome if gate == Gate.PACKAGE else Outcome.PASS
        store.record_verification(job_id, Verification(gate=gate, outcome=verdict,
                                                      candidate_hash="a" * 64, evidence=("test receipt",)))
    assert store.snapshot(job_id).status != JobStatus.COMPLETED


def test_temporary_roles_cannot_expand_tools():
    registry = AgentRegistry([AgentSpec("researcher", "Inspect", ("inspect",))])
    child = registry.temporary("focused", "Inspect a narrow concern", parent="researcher", tools=("inspect",))
    assert child.temporary
    with pytest.raises(ValueError):
        registry.temporary("unsafe", "Mutate", parent="researcher", tools=("execute_python",))
    with pytest.raises(ValueError):
        registry.validate(Plan(summary="Bad permissions", tasks=(task(tools=("execute_python",)),)))
