"""Versioned contracts for planning, scheduling, and evidence-gated completion."""

from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True, str_min_length=1)


class Mode(StrEnum):
    ASK = "ask"
    PLAN = "plan"
    AGENT = "agent"


class Effect(StrEnum):
    READ = "read"
    DRAFT = "draft"
    EDITOR = "editor"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    FAILED = "failed"
    AWAITING_VERIFICATION = "awaiting_verification"
    COMPLETED = "completed"


class Gate(StrEnum):
    BUILD = "build"
    ASSETS = "assets"
    PIE = "pie"
    PACKAGE = "package"


class Outcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class JobSpec(Record):
    schema_version: int = Field(default=1, ge=1, le=1)
    project_path: str = Field(min_length=1)
    goal: str = Field(min_length=1, max_length=20000)
    criteria: tuple[str, ...] = Field(min_length=1)
    revision: int = Field(default=1, ge=1)
    mode: Mode = Mode.PLAN
    approved: bool = False


def validate_target(target):
    if target.startswith("asset:/Game/"):
        relative = target.removeprefix("asset:/Game/")
    else:
        relative = target
    path = PurePosixPath(relative)
    if (not relative or relative.startswith("/") or "\\" in relative or ":" in relative
            or any(part in ("", ".", "..") for part in relative.split("/"))
            or any(c in relative for c in ("*", "?", "[", "]")) or path.is_absolute()):
        raise ValueError("Write targets must be explicit relative files or asset:/Game/ paths")
    return target


class TaskSpec(Record):
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
    role: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    dependencies: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    effect: Effect = Effect.READ
    write_targets: tuple[str, ...] = ()
    max_attempts: int = Field(default=2, ge=1, le=5)

    @model_validator(mode="after")
    def check_scope(self):
        for values in (self.dependencies, self.tools, self.write_targets):
            if len(set(values)) != len(values):
                raise ValueError("Task dependencies, tools, and targets must be unique")
        if self.id in self.dependencies:
            raise ValueError("A task cannot depend on itself")
        if self.effect == Effect.READ and self.write_targets:
            raise ValueError("Read-only tasks cannot declare writes")
        if self.effect == Effect.EDITOR and not self.write_targets:
            raise ValueError("Editor tasks must declare their write targets")
        if len({target.casefold() for target in self.write_targets}) != len(self.write_targets):
            raise ValueError("Write targets must not alias on case-insensitive filesystems")
        for target in self.write_targets:
            validate_target(target)
        return self


class Plan(Record):
    summary: str = Field(min_length=1)
    tasks: tuple[TaskSpec, ...] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def check_graph(self):
        by_id = {task.id: task for task in self.tasks}
        if len(by_id) != len(self.tasks):
            raise ValueError("Task IDs must be unique")
        done = set()
        for task in self.tasks:
            if not set(task.dependencies) <= by_id.keys():
                raise ValueError("Task references an unknown dependency")
        while len(done) != len(by_id):
            ready = {key for key, task in by_id.items() if key not in done and set(task.dependencies) <= done}
            if not ready:
                raise ValueError("Task dependencies contain a cycle")
            done.update(ready)
        return self


class WorkerReport(Record):
    summary: str = Field(min_length=1)
    findings: tuple[str, ...] = ()
    proposals: tuple[str, ...] = ()


class TaskRecord(Record):
    spec: TaskSpec
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    owner: str | None = None
    report: WorkerReport | None = None
    error: str | None = None


class Verification(Record):
    gate: Gate
    outcome: Outcome
    candidate_hash: str = Field(min_length=1)
    evidence: tuple[str, ...] = Field(min_length=1)


class JobSnapshot(Record):
    id: str
    spec: JobSpec
    plan: Plan
    status: JobStatus
    control: str
    tasks: tuple[TaskRecord, ...]
    candidate_hash: str | None = None
    verification: tuple[Verification, ...] = ()
