"""Specialists receive explicit tool subsets, including temporary roles."""

from dataclasses import dataclass

from ue_agent.domain import Plan


@dataclass(frozen=True)
class AgentSpec:
    name: str
    instructions: str
    tools: tuple[str, ...] = ()
    temporary: bool = False


class AgentRegistry:
    def __init__(self, agents=()):
        self._agents = {}
        for agent in agents:
            self.register(agent)

    def register(self, agent):
        if not agent.name.strip() or not agent.instructions.strip():
            raise ValueError("A specialist needs a name and instructions")
        if agent.name in self._agents:
            raise ValueError(f"Specialist already exists: {agent.name}")
        self._agents[agent.name] = agent

    def get(self, name):
        if name not in self._agents:
            raise ValueError(f"Unknown specialist: {name}")
        return self._agents[name]

    def all(self):
        return tuple(self._agents.values())

    def temporary(self, name, instructions, *, parent, tools=()):
        parent_spec = self.get(parent)
        if not set(tools) <= set(parent_spec.tools):
            raise ValueError("A temporary specialist cannot expand its parent's tools")
        agent = AgentSpec(name, instructions, tuple(tools), temporary=True)
        self.register(agent)
        return agent

    def validate(self, plan: Plan):
        for task in plan.tasks:
            agent = self.get(task.role)
            if not set(task.tools) <= set(agent.tools):
                raise ValueError(f"Task {task.id} exceeds specialist {agent.name}'s tool permissions")


def builtin_registry():
    instructions = {
        "researcher": "Inspect relevant project context and report referenced findings and unresolved questions.",
        "cpp": "Develop native Unreal gameplay code and diagnose compiler errors. Return scoped proposals.",
        "behavior": ("Own NPC decisions: Behavior Trees, Blackboards, StateTree, AI Controllers, Perception, "
                     "navigation, and EQS. Define transitions, interfaces, and observable failure cases."),
        "blueprint_ui": "Develop Blueprint and UMG logic, native interfaces, references, and runtime UI behavior.",
        "level_material": "Develop level layouts, collision, navigation, materials, and asset references.",
        "asset": "Find or generate assets and document provenance, import settings, rigging, and animation quality.",
        "vfx": "Develop Niagara systems and their materials, parameters, and gameplay triggers.",
        "performance": "Investigate captures and report measured hotspots and data-coverage limitations.",
        "audio": "Develop audio, MetaSounds, and playback triggers; verify generated output and packaged playback.",
        "tester": "Derive tests from the agreed criteria and report actual observations, never invented passes.",
        "reviewer": "Review changes and evidence against the agreed criteria; distinguish missing proof from failure.",
    }
    return AgentRegistry(AgentSpec(name, body) for name, body in instructions.items())
