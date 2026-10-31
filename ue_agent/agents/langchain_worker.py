"""LangChain agents with isolated task briefs and centrally configured OpenAI models.

This first adapter produces research/drafts. Live-editor mutation tools are not
connected yet; requesting one is a blocker, never a simulated implementation.
"""

import json

from langchain.agents import create_agent

from ue_agent.domain import Effect, JobSpec, Plan, WorkerReport
from ue_agent.llm import openai_models
from ue_agent.orchestration import TaskBlocked


class LangChainWorker:
    def __init__(self, registry, settings, *, read_tools=None):
        self.registry, self.settings = registry, settings
        # Entries are trusted, application-supplied read-only tools, not model-defined callables.
        self.read_tools = read_tools or {}

    async def __call__(self, context):
        task = context.task
        if task.effect == Effect.EDITOR:
            raise TaskBlocked("The live Unreal editor adapter is not connected in this foundation")
        agent_spec = self.registry.get(task.role)
        if not set(task.tools) <= set(agent_spec.tools):
            raise TaskBlocked("Task exceeds the specialist's registered tool permissions")
        if not set(task.tools) <= self.read_tools.keys():
            raise TaskBlocked("A requested read-only tool is not connected")
        model = openai_models.get_specialist_model(task.role, self.settings)
        agent = create_agent(
            model=model,
            tools=[self.read_tools[name] for name in task.tools],
            system_prompt=(agent_spec.instructions + "\nReturn findings and draft proposals only. "
                           "Do not claim files were changed, tools ran, or tests passed without actual evidence."),
            response_format=WorkerReport,
        )
        brief = {"goal": context.job.goal, "criteria": context.job.criteria,
                 "task": task.model_dump(mode="json"),
                 "dependencies": {key: value.model_dump(mode="json")
                                  for key, value in context.dependencies.items() if value is not None}}
        result = await agent.ainvoke({"messages": [{"role": "user", "content": json.dumps(brief)}]},
                                    config={"recursion_limit": 20})
        return WorkerReport.model_validate(result["structured_response"])


async def create_plan(spec: JobSpec, registry, settings):
    """Propose a validated task DAG without authorizing or executing its changes."""
    model = openai_models.get_supervisor_model(settings)
    roles = [{"name": a.name, "instructions": a.instructions, "tools": a.tools} for a in registry.all()]
    agent = create_agent(
        model=model, tools=[], response_format=Plan,
        system_prompt=("Plan Unreal work as a bounded dependency graph using the supplied specialists. "
                       "READ means analysis, DRAFT means proposals, EDITOR means live mutations. "
                       "Declare explicit write targets for changes and dependencies between integrations. "
                       "Do not claim implementation or verification has happened. "
                       "Approval is controlled by the caller and cannot be supplied by this plan."),
    )
    response = await agent.ainvoke({"messages": [{"role": "user", "content": json.dumps(
        {"specification": spec.model_dump(mode="json"), "specialists": roles})}]},
        config={"recursion_limit": 20})
    plan = Plan.model_validate(response["structured_response"])
    registry.validate(plan)
    return plan
