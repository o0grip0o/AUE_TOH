"""LangChain adapters receive isolated briefs and cannot authorize their own execution."""

import asyncio
import json

import pytest

from ue_agent.agents import langchain_worker
from ue_agent.agents.registry import AgentRegistry, AgentSpec, builtin_registry
from ue_agent.cli import main
from ue_agent.config import ModelSettings
from ue_agent.domain import Effect, JobSpec, Mode, Plan, TaskSpec, WorkerReport
from ue_agent.llm import openai_models
from ue_agent.orchestration import TaskBlocked, TaskContext
from ue_agent.storage import JobStore


def spec():
    return JobSpec(project_path="/fixture/Game.uproject", goal="Implement the feature",
                   criteria=("The intended behavior is observed",), mode=Mode.PLAN)


def fake_agent(monkeypatch, output):
    calls = {}

    class Agent:
        async def ainvoke(self, payload, config):
            calls["payload"], calls["config"] = payload, config
            return {"structured_response": output}

    def create(**kwargs):
        calls["construction"] = kwargs
        return Agent()

    monkeypatch.setattr(langchain_worker, "create_agent", create)
    return calls


def test_planner_returns_validated_dag_without_approving_job(monkeypatch):
    plan = Plan(summary="Plan", tasks=(TaskSpec(id="inspect", role="researcher", instruction="Inspect context"),))
    calls = fake_agent(monkeypatch, plan)
    model = object()
    monkeypatch.setattr(openai_models, "get_supervisor_model", lambda settings: model)
    job = spec()
    result = asyncio.run(langchain_worker.create_plan(job, builtin_registry(), ModelSettings("model")))
    assert result == plan and not job.approved and job.mode == Mode.PLAN
    assert calls["construction"]["model"] is model
    assert calls["construction"]["tools"] == []
    assert calls["construction"]["response_format"] is Plan
    assert json.loads(calls["payload"]["messages"][0]["content"])["specification"]["approved"] is False


def test_planner_rejects_unknown_roles(monkeypatch):
    plan = Plan(summary="Plan", tasks=(TaskSpec(id="inspect", role="unregistered", instruction="Inspect"),))
    fake_agent(monkeypatch, plan)
    monkeypatch.setattr(openai_models, "get_supervisor_model", lambda settings: object())
    with pytest.raises(ValueError, match="Unknown specialist"):
        asyncio.run(langchain_worker.create_plan(spec(), builtin_registry(), ModelSettings("model")))


def test_worker_gets_only_its_task_and_dependency_reports(monkeypatch):
    calls = fake_agent(monkeypatch, WorkerReport(summary="Reviewed the supplied findings"))
    monkeypatch.setattr(openai_models, "get_specialist_model", lambda role, settings: role)
    registry = AgentRegistry([AgentSpec("reviewer", "Review only", ("inspect",))])
    read_tool = object()
    worker = langchain_worker.LangChainWorker(registry, ModelSettings("model"), read_tools={"inspect": read_tool})
    task = TaskSpec(id="review", role="reviewer", instruction="Review the interface", tools=("inspect",))
    context = TaskContext(spec(), task, {"research": WorkerReport(summary="Focused findings")})
    output = asyncio.run(worker(context))
    assert output.summary == "Reviewed the supplied findings"
    brief = json.loads(calls["payload"]["messages"][0]["content"])
    assert brief["task"]["id"] == "review"
    assert set(brief["dependencies"]) == {"research"}
    assert "messages" not in brief and "tasks" not in brief
    assert calls["construction"]["tools"] == [read_tool]
    assert calls["construction"]["model"] == "reviewer"


@pytest.mark.parametrize("effect,tools,targets", [
    (Effect.EDITOR, (), ("asset:/Game/Object",)),
    (Effect.READ, ("missing_tool",), ()),
])
def test_unconnected_tools_block_before_a_model_call(monkeypatch, effect, tools, targets):
    def no_model(*args):
        pytest.fail("Missing capabilities must not invoke a model")

    monkeypatch.setattr(openai_models, "get_specialist_model", no_model)
    worker = langchain_worker.LangChainWorker(builtin_registry(), ModelSettings("model"))
    task = TaskSpec(id="work", role="researcher", instruction="Inspect", effect=effect,
                    tools=tools, write_targets=targets)
    with pytest.raises(TaskBlocked):
        asyncio.run(worker(TaskContext(spec(), task, {})))


def test_cli_demo_is_offline_persistent_and_explicitly_unverified(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("UE_AGENT_MODEL", raising=False)
    path = tmp_path / "state.sqlite3"
    assert main(["--db", str(path), "demo"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["demo"] is True and result["unreal_connected"] is False
    assert result["job"]["status"] == "awaiting_verification"
    assert result["job"]["verification"] == []
    job_id = result["job"]["id"]
    assert main(["--db", str(path), "status", job_id]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == job_id
    with JobStore(path) as store:
        assert len(store.snapshot(job_id).tasks) == 4


def test_cli_rejects_missing_project_before_planning(tmp_path, capsys):
    assert main(["--db", str(tmp_path / "state.sqlite3"), "plan", "--project", "missing.uproject",
                 "--goal", "Implement", "--criterion", "Works"]) == 2
    assert "existing .uproject" in capsys.readouterr().err
