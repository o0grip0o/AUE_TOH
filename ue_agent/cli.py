"""Developer harness for the foundation; the docked UI and IDE transport come later."""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=".ue_agent/state.sqlite3", help="Local task journal (never commit it)")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Run deterministic offline workers through the real graph")
    demo.add_argument("--project", default=".")
    plan = commands.add_parser("plan", help="Ask OpenAI for a task plan; do not execute it")
    plan.add_argument("--project", required=True, help="An existing .uproject file")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--criterion", action="append", required=True, help="Repeat for each acceptance criterion")
    for command in ("status", "pause", "resume", "cancel"):
        sub = commands.add_parser(command)
        sub.add_argument("job_id")
    return parser


async def _demo(store, project):
    from ue_agent.agents.registry import builtin_registry
    from ue_agent.domain import Effect, JobSpec, Mode, Plan, TaskSpec, WorkerReport
    from ue_agent.orchestration import TaskScheduler, execute_job

    spec = JobSpec(project_path=str(Path(project).resolve()), goal="Demonstrate specialist task coordination",
                   criteria=("Respect dependencies and retain explicit unverified completion gates",),
                   mode=Mode.AGENT, approved=True)
    plan = Plan(summary="Offline orchestration example, without Unreal or model calls", tasks=(
        TaskSpec(id="research", role="researcher", instruction="Identify the required interfaces"),
        TaskSpec(id="native", role="cpp", instruction="Draft the native interface", effect=Effect.DRAFT,
                 dependencies=("research",)),
        TaskSpec(id="behavior", role="behavior", instruction="Draft the decision-state contract", effect=Effect.DRAFT,
                 dependencies=("research",)),
        TaskSpec(id="review", role="reviewer", instruction="Review the interface proposals",
                 dependencies=("native", "behavior")),
    ))

    async def worker(context):
        await asyncio.sleep(0)
        return WorkerReport(summary=f"Offline example: {context.task.instruction}",
                            findings=("No model, Unreal editor, files, or gameplay tests were invoked",))

    job_id = store.create_job(spec, plan)
    snapshot = await execute_job(TaskScheduler(store, builtin_registry(), worker), job_id)
    return {"demo": True, "unreal_connected": False, "job": snapshot.model_dump(mode="json"),
            "note": "Task coordination finished; implementation and all four verification gates remain unverified"}


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        from ue_agent.storage import JobStore

        with JobStore(args.db) as store:
            if args.command == "demo":
                result = asyncio.run(_demo(store, args.project))
            elif args.command == "plan":
                from ue_agent.agents.langchain_worker import create_plan
                from ue_agent.agents.registry import builtin_registry
                from ue_agent.config import ModelSettings
                from ue_agent.domain import JobSpec

                project = Path(args.project).expanduser().resolve()
                if not project.is_file() or project.suffix.lower() != ".uproject":
                    raise ValueError("--project must name an existing .uproject file")
                spec = JobSpec(project_path=str(project), goal=args.goal, criteria=tuple(args.criterion))
                plan = asyncio.run(create_plan(spec, builtin_registry(), ModelSettings.from_env()))
                job_id = store.create_job(spec, plan)
                result = store.snapshot(job_id).model_dump(mode="json")
            else:
                if args.command != "status":
                    store.control(args.job_id, args.command)
                result = store.snapshot(args.job_id).model_dump(mode="json")
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, PermissionError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except ImportError:
        print('Install the development-agent extra: pip install -e ".[ue-agent]"', file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
