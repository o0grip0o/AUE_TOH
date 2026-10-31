"""SQLite task journal with atomic claims and explicit verification receipts.

This persists the scheduler's authoritative state between LangGraph invocations.
It is not an Unreal rollback mechanism or a replacement for editor reconciliation.
"""

import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from ue_agent.domain import (
    Effect,
    Gate,
    JobSnapshot,
    JobSpec,
    JobStatus,
    Mode,
    Outcome,
    Plan,
    TaskRecord,
    TaskSpec,
    TaskStatus,
    Verification,
)


def _resources(project, task):
    root = str(Path(project).resolve()).casefold()
    values = [f"{root}::{target.casefold()}" for target in task.write_targets]
    if task.effect == Effect.EDITOR:
        values.append(f"editor::{root}")
    return values


def _overlap(a, b):
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


class JobStore:
    APPLICATION_ID = 0x55454147  # UEAG: do not initialize over another application's database.

    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, timeout=10, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        application = self._db.execute("PRAGMA application_id").fetchone()[0]
        tables = self._db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if application != self.APPLICATION_ID and (application or version or tables):
            self._db.close()
            raise ValueError("This database does not belong to the UE agent")
        if version not in (0, 1):
            self._db.close()
            raise ValueError(f"Unsupported state schema version: {version}")
        self._db.execute(f"PRAGMA application_id={self.APPLICATION_ID}")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, spec TEXT NOT NULL, plan TEXT NOT NULL,
                status TEXT NOT NULL, control TEXT NOT NULL, candidate TEXT
            );
            CREATE TABLE IF NOT EXISTS tasks (
                job_id TEXT NOT NULL, id TEXT NOT NULL, spec TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                owner TEXT, report TEXT, error TEXT, PRIMARY KEY (job_id, id)
            );
            CREATE TABLE IF NOT EXISTS leases (
                resource TEXT PRIMARY KEY, job_id TEXT NOT NULL, task_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS verification (
                job_id TEXT NOT NULL, gate TEXT NOT NULL, receipt TEXT NOT NULL,
                PRIMARY KEY (job_id, gate)
            );
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL
            );
            PRAGMA user_version=1;
        """)

    def close(self):
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def _transaction(self):
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                yield
                self._db.commit()
            except BaseException:
                self._db.rollback()
                raise

    def _event(self, job_id, kind, **payload):
        self._db.execute("INSERT INTO events(job_id,kind,payload,created) VALUES(?,?,?,?)",
                         (job_id, kind, json.dumps(payload), time.time()))

    def _snapshot(self, job_id):
        job = self._db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if job is None:
            raise KeyError(f"Unknown job: {job_id}")
        tasks = []
        for row in self._db.execute("SELECT * FROM tasks WHERE job_id=? ORDER BY rowid", (job_id,)):
            tasks.append(TaskRecord(spec=TaskSpec.model_validate_json(row["spec"]), status=row["status"],
                                    attempts=row["attempts"], owner=row["owner"], error=row["error"],
                                    report=json.loads(row["report"]) if row["report"] else None))
        receipts = tuple(Verification.model_validate_json(row[0]) for row in self._db.execute(
            "SELECT receipt FROM verification WHERE job_id=? ORDER BY gate", (job_id,)))
        return JobSnapshot(id=job_id, spec=JobSpec.model_validate_json(job["spec"]),
                           plan=Plan.model_validate_json(job["plan"]), status=job["status"],
                           control=job["control"], tasks=tuple(tasks), candidate_hash=job["candidate"],
                           verification=receipts)

    def snapshot(self, job_id):
        with self._transaction():
            return self._snapshot(job_id)

    def create_job(self, spec: JobSpec, plan: Plan, *, job_id=None):
        job_id = job_id or uuid.uuid4().hex
        with self._transaction():
            found = self._db.execute("SELECT spec,plan FROM jobs WHERE id=?", (job_id,)).fetchone()
            if found:
                if found["spec"] != spec.model_dump_json() or found["plan"] != plan.model_dump_json():
                    raise ValueError("A job ID cannot be reused for a different specification or plan")
                return job_id
            self._db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,NULL)",
                             (job_id, spec.model_dump_json(), plan.model_dump_json(), JobStatus.PLANNED, "run"))
            self._db.executemany("INSERT INTO tasks(job_id,id,spec,status) VALUES(?,?,?,?)",
                                 [(job_id, t.id, t.model_dump_json(), TaskStatus.PENDING) for t in plan.tasks])
            self._event(job_id, "job.created", revision=spec.revision)
        return job_id

    def claim_ready(self, job_id, max_workers):
        if max_workers < 1:
            raise ValueError("Worker limit must be positive")
        claimed = []
        with self._transaction():
            job = self._snapshot(job_id)
            if job.spec.mode != Mode.AGENT or not job.spec.approved:
                raise PermissionError("Execution requires an approved Agent-mode specification")
            if job.control != "run" or job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
                return ()
            done = {t.spec.id for t in job.tasks if t.status == TaskStatus.SUCCEEDED}
            capacity = max_workers - sum(t.status == TaskStatus.RUNNING for t in job.tasks)
            leased = [r[0] for r in self._db.execute("SELECT resource FROM leases")]
            for task in job.tasks:
                if capacity <= 0:
                    break
                if task.status != TaskStatus.PENDING or not set(task.spec.dependencies) <= done:
                    continue
                resources = _resources(job.spec.project_path, task.spec)
                if any(_overlap(a, b) for a in resources for b in leased):
                    continue
                owner = uuid.uuid4().hex
                self._db.execute("UPDATE tasks SET status=?,attempts=attempts+1,owner=?,error=NULL "
                                 "WHERE job_id=? AND id=?", (TaskStatus.RUNNING, owner, job_id, task.spec.id))
                self._db.executemany("INSERT INTO leases VALUES(?,?,?)",
                                     [(r, job_id, task.spec.id) for r in resources])
                self._event(job_id, "task.started", task_id=task.spec.id, attempt=task.attempts + 1)
                claimed.append(task.model_copy(update={"status": TaskStatus.RUNNING,
                                                       "attempts": task.attempts + 1, "owner": owner}))
                leased.extend(resources)
                capacity -= 1
            if claimed:
                self._db.execute("UPDATE jobs SET status=? WHERE id=?", (JobStatus.RUNNING, job_id))
        return tuple(claimed)

    def finish_task(self, job_id, task_id, owner, status, *, report=None, error=None):
        status = TaskStatus(status)
        if status not in (TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.CANCELLED):
            raise ValueError("A task must finish with a terminal result")
        if status == TaskStatus.SUCCEEDED and report is None:
            raise ValueError("A successful task needs a report")
        with self._transaction():
            task = self._db.execute("SELECT status,owner FROM tasks WHERE job_id=? AND id=?",
                                    (job_id, task_id)).fetchone()
            if task is None or task["status"] != TaskStatus.RUNNING or task["owner"] != owner:
                raise RuntimeError("Task claim is missing, stale, or owned by another worker")
            self._db.execute("UPDATE tasks SET status=?,owner=NULL,report=?,error=? WHERE job_id=? AND id=?",
                             (status, report.model_dump_json() if report else None, error, job_id, task_id))
            self._db.execute("DELETE FROM leases WHERE job_id=? AND task_id=?", (job_id, task_id))
            self._event(job_id, "task.finished", task_id=task_id, status=status)

    def retry_safe_failures(self, job_id):
        with self._transaction():
            job = self._snapshot(job_id)
            if job.control != "run":
                return
            for task in job.tasks:
                if (task.status == TaskStatus.FAILED and task.spec.effect != Effect.EDITOR
                        and task.attempts < task.spec.max_attempts):
                    self._db.execute("UPDATE tasks SET status=? WHERE job_id=? AND id=?",
                                     (TaskStatus.PENDING, job_id, task.spec.id))
                    self._event(job_id, "task.retry", task_id=task.spec.id)

    def control(self, job_id, action):
        if action not in ("pause", "resume", "cancel"):
            raise ValueError("Unknown job control")
        with self._transaction():
            job = self._snapshot(job_id)
            if job.status in (JobStatus.COMPLETED, JobStatus.CANCELLED):
                raise ValueError("A terminal job cannot be controlled")
            if job.control == "cancel" and action != "cancel":
                raise ValueError("Cancellation cannot be reversed")
            value = "run" if action == "resume" else action
            self._db.execute("UPDATE jobs SET control=? WHERE id=?", (value, job_id))
            if action == "cancel":
                self._db.execute("UPDATE tasks SET status=? WHERE job_id=? AND status=?",
                                 (TaskStatus.CANCELLED, job_id, TaskStatus.PENDING))
            self._event(job_id, f"job.{action}")
            return self._refresh(job_id)

    def _refresh(self, job_id):
        job = self._snapshot(job_id)
        statuses = {task.status for task in job.tasks}
        if job.control == "cancel":
            status = JobStatus.CANCELLING if TaskStatus.RUNNING in statuses else JobStatus.CANCELLED
        elif job.control == "pause":
            status = JobStatus.PAUSING if TaskStatus.RUNNING in statuses else JobStatus.PAUSED
        elif job.spec.mode != Mode.AGENT or not job.spec.approved:
            status = JobStatus.PLANNED
        elif TaskStatus.RUNNING in statuses:
            status = JobStatus.RUNNING
        elif TaskStatus.FAILED in statuses:
            status = JobStatus.FAILED
        elif TaskStatus.BLOCKED in statuses:
            status = JobStatus.BLOCKED
        elif TaskStatus.CANCELLED in statuses:
            status = JobStatus.BLOCKED
        elif statuses == {TaskStatus.SUCCEEDED}:
            passed = {v.gate for v in job.verification if v.outcome == Outcome.PASS
                      and v.candidate_hash == job.candidate_hash}
            failed = any(v.outcome == Outcome.FAIL for v in job.verification)
            status = (JobStatus.COMPLETED if job.candidate_hash and passed == set(Gate)
                      else JobStatus.FAILED if failed else JobStatus.AWAITING_VERIFICATION)
        else:
            status = JobStatus.RUNNING
        self._db.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
        return status

    def refresh(self, job_id):
        with self._transaction():
            return self._refresh(job_id)

    def set_candidate(self, job_id, candidate_hash):
        if len(candidate_hash) != 64 or any(c not in "0123456789abcdef" for c in candidate_hash):
            raise ValueError("A candidate needs a SHA-256 content-manifest hash")
        with self._transaction():
            job = self._snapshot(job_id)
            if any(task.status != TaskStatus.SUCCEEDED for task in job.tasks):
                raise ValueError("All tasks must succeed before selecting a candidate")
            if job.control != "run":
                raise ValueError("A paused or cancelled job cannot select a candidate")
            if candidate_hash != job.candidate_hash:
                self._db.execute("DELETE FROM verification WHERE job_id=?", (job_id,))
                self._db.execute("UPDATE jobs SET candidate=? WHERE id=?", (candidate_hash, job_id))
                self._event(job_id, "candidate.selected", candidate_hash=candidate_hash)
            self._refresh(job_id)

    def record_verification(self, job_id, receipt: Verification):
        """Record a trusted runner's receipt, never an LLM worker's self-reported pass."""
        with self._transaction():
            job = self._snapshot(job_id)
            if not job.candidate_hash or receipt.candidate_hash != job.candidate_hash:
                raise ValueError("Verification does not match the selected candidate")
            if any(t.status != TaskStatus.SUCCEEDED for t in job.tasks) or job.control != "run":
                raise ValueError("Job is not ready for verification")
            self._db.execute("INSERT OR REPLACE INTO verification VALUES(?,?,?)",
                             (job_id, receipt.gate, receipt.model_dump_json()))
            self._event(job_id, "verification.recorded", gate=receipt.gate, outcome=receipt.outcome)
            self._refresh(job_id)

    def reconcile_interrupted(self, job_id, *, owner, reports=None):
        """Reconcile a confirmed-stopped executor's claims; uncertain work stays blocked.

        The caller must establish that this owner is no longer executing. Until then,
        its claims/leases must remain intact. Report keys identify inspected successes.
        """
        reports = reports or {}
        with self._transaction():
            job = self._snapshot(job_id)
            for task in job.tasks:
                if task.status != TaskStatus.RUNNING or task.owner != owner:
                    continue
                report = reports.get(task.spec.id)
                self._db.execute("UPDATE tasks SET status=?,owner=NULL,report=?,error=? "
                                 "WHERE job_id=? AND id=?",
                                 (TaskStatus.SUCCEEDED if report else TaskStatus.BLOCKED,
                                  report.model_dump_json() if report else None,
                                  None if report else "Interrupted operation needs project-state reconciliation",
                                  job_id, task.spec.id))
                self._db.execute("DELETE FROM leases WHERE job_id=? AND task_id=?", (job_id, task.spec.id))
                self._event(job_id, "task.reconciled", task_id=task.spec.id)
            self._refresh(job_id)

    def events(self, job_id, *, after=0):
        with self._transaction():
            return [{"sequence": row["sequence"], "kind": row["kind"],
                     "payload": json.loads(row["payload"]), "created": row["created"]}
                    for row in self._db.execute("SELECT * FROM events WHERE job_id=? AND sequence>? "
                                                "ORDER BY sequence", (job_id, after))]
