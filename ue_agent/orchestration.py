"""A LangGraph execution loop around a deterministic, journaled task scheduler."""

import asyncio
import os
from dataclasses import dataclass
from typing import Awaitable, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from ue_agent.agents.registry import AgentRegistry
from ue_agent.domain import Effect, JobSpec, JobStatus, Mode, TaskSpec, TaskStatus, WorkerReport
from ue_agent.storage import JobStore


class TaskBlocked(Exception):
    """A capability, approval, or decision is missing; blindly retrying will not fix it."""


@dataclass(frozen=True)
class TaskContext:
    job: JobSpec
    task: TaskSpec
    dependencies: dict[str, WorkerReport]


Worker = Callable[[TaskContext], Awaitable[WorkerReport]]


def _error_message(error):
    message = f"{type(error).__name__}: {error}"
    key = os.environ.get("OPENAI_API_KEY")
    return message.replace(key, "[redacted]") if key else message


class TaskScheduler:
    def __init__(self, store: JobStore, registry: AgentRegistry, worker: Worker, *, max_workers=3, task_timeout=300):
        if max_workers < 1 or task_timeout <= 0:
            raise ValueError("Worker count and task timeout must be positive")
        self.store, self.registry, self.worker = store, registry, worker
        self.max_workers, self.task_timeout = max_workers, task_timeout

    async def _execute(self, job_id, claim):
        snapshot = self.store.snapshot(job_id)
        dependencies = {t.spec.id: t.report for t in snapshot.tasks if t.spec.id in claim.spec.dependencies}
        context = TaskContext(snapshot.spec, claim.spec, dependencies)
        try:
            report = await asyncio.wait_for(self.worker(context), timeout=self.task_timeout)
            report = WorkerReport.model_validate(report)
        except asyncio.CancelledError:
            self.store.finish_task(job_id, claim.spec.id, claim.owner, TaskStatus.CANCELLED,
                                   error="Worker acknowledged cancellation; no rollback is implied")
            raise
        except TaskBlocked as error:
            self.store.finish_task(job_id, claim.spec.id, claim.owner, TaskStatus.BLOCKED,
                                   error=_error_message(error))
        except Exception as error:
            status = TaskStatus.BLOCKED if claim.spec.effect == Effect.EDITOR else TaskStatus.FAILED
            self.store.finish_task(job_id, claim.spec.id, claim.owner, status, error=_error_message(error))
        else:
            self.store.finish_task(job_id, claim.spec.id, claim.owner, TaskStatus.SUCCEEDED, report=report)

    async def tick(self, job_id):
        snapshot = self.store.snapshot(job_id)
        self.registry.validate(snapshot.plan)
        self.store.retry_safe_failures(job_id)
        claims = self.store.claim_ready(job_id, self.max_workers)
        futures = {asyncio.create_task(self._execute(job_id, task)): task for task in claims}
        try:
            pending = set(futures)
            while pending:
                if self.store.snapshot(job_id).control == "cancel":
                    for future in pending:
                        future.cancel()
                _, pending = await asyncio.wait(pending, timeout=0.05, return_when=asyncio.FIRST_COMPLETED)
            # Retrieving every result surfaces journal errors, and consumes cancellation exceptions.
            outcomes = await asyncio.gather(*futures, return_exceptions=True)
            self._acknowledge_cancellations(job_id, futures)
            for outcome in outcomes:
                if isinstance(outcome, BaseException) and not isinstance(outcome, asyncio.CancelledError):
                    raise outcome
        except BaseException:
            for future in futures:
                future.cancel()
            await asyncio.gather(*futures, return_exceptions=True)
            self._acknowledge_cancellations(job_id, futures)
            self.store.refresh(job_id)
            raise
        status = self.store.refresh(job_id)
        return bool(claims), status

    def _acknowledge_cancellations(self, job_id, futures):
        # A task cancelled before its coroutine starts cannot run _execute's cleanup.
        records = {t.spec.id: t for t in self.store.snapshot(job_id).tasks}
        for future, claim in futures.items():
            current = records[claim.spec.id]
            if future.cancelled() and current.status == TaskStatus.RUNNING and current.owner == claim.owner:
                self.store.finish_task(job_id, claim.spec.id, claim.owner, TaskStatus.CANCELLED,
                                       error="Worker acknowledged cancellation before execution")


class ExecutionState(TypedDict):
    job_id: str
    did_work: bool
    status: str


def build_execution_graph(scheduler: TaskScheduler):
    """Compile the graph; SQLite is authoritative, so a new invocation resumes saved tasks.

    Only IDs and current routing flags live in the graph. Worker reports/claims are
    saved as they finish, before a graph node completes. Interrupted running claims
    require reconciliation instead of automatic replay.
    """

    def guard(state):
        job = scheduler.store.snapshot(state["job_id"])
        if job.spec.mode != Mode.AGENT or not job.spec.approved:
            raise PermissionError("Ask/Plan modes cannot execute tasks; approve an Agent-mode specification")
        scheduler.registry.validate(job.plan)
        return {"status": job.status, "did_work": False}

    async def dispatch(state):
        did_work, status = await scheduler.tick(state["job_id"])
        return {"did_work": did_work, "status": status}

    def route(state):
        job = scheduler.store.snapshot(state["job_id"])
        if not state["did_work"] or job.control != "run":
            return END
        retryable = any(t.status == TaskStatus.FAILED and t.spec.effect != Effect.EDITOR
                        and t.attempts < t.spec.max_attempts for t in job.tasks)
        done = {t.spec.id for t in job.tasks if t.status == TaskStatus.SUCCEEDED}
        ready = any(t.status == TaskStatus.PENDING and set(t.spec.dependencies) <= done for t in job.tasks)
        return "dispatch" if retryable or ready else END

    builder = StateGraph(ExecutionState)
    builder.add_node("guard", guard)
    builder.add_node("dispatch", dispatch)
    builder.add_edge(START, "guard")
    builder.add_edge("guard", "dispatch")
    builder.add_conditional_edges("dispatch", route)
    return builder.compile()


async def execute_job(scheduler, job_id):
    # Each task has at most five attempts; allow worst-case serialized execution plus guard/exit.
    count = sum(t.spec.max_attempts for t in scheduler.store.snapshot(job_id).tasks)
    graph = build_execution_graph(scheduler)
    await graph.ainvoke({"job_id": job_id, "did_work": False, "status": JobStatus.PLANNED},
                       config={"recursion_limit": count + 5})
    return scheduler.store.snapshot(job_id)
