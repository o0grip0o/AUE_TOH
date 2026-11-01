# AUE TOH — Unreal Autonomous Agent

A UE-focused development agent built with LangChain/LangGraph, OpenAI development specialists, and local
Ollama/Nimble gameplay decisions. The first integration target is **Unreal Engine 5.8.3 on macOS**.

**Current status:** the Python foundation runs an offline multi-agent demo and creates OpenAI task plans for an
existing `.uproject`. The new supervisor, Ollama policy, and Unreal editor panel are **not connected yet**.
There is no command that launches the complete autonomous development agent inside Unreal in this build.
The existing **Autopilot** panel can still run the legacy playtesting service with its original provider setup.
Native UE 5.8.3/macOS builds and live gameplay remain to be validated.

See the [project specification](docs/UE_AGENT_SPEC.md) and [implementation status](docs/UE_AGENT_IMPLEMENTATION.md).

**Next experiment:** run the [guarded-door benchmark](docs/GUARDED_DOOR_BENCHMARK.md) in local Codex with
Unreal's native MCP server, using the [result template](bench/guarded_door/result.template.md). This baseline
measures existing tooling before adding more custom agent infrastructure. It does not require the Python harness.

- [Prerequisites](#prerequisites)
- [Run the Python foundation](#run-the-python-foundation)
- [Run the existing plugin in Unreal on macOS](#run-the-existing-plugin-in-unreal-on-macos)
- [Configure local gameplay decisions](#configure-local-gameplay-decisions)
- [Troubleshooting](#development-setup-troubleshooting)
- [Legacy Autopilot instructions](#legacy-autopilot)

## Prerequisites

| Component | When it is needed |
| --- | --- |
| Git and Python **3.12+** | All source installations. |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | The environment and installation commands below. |
| macOS, **UE 5.8.3**, and an existing `.uproject` | Native plugin setup; the offline demo needs no engine or project. |
| Full Xcode with the compatible macOS SDK | Building the native Unreal plugin. Match the installed engine to [Epic's macOS requirements](https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine). Epic's UE 5.8 table lists macOS 14.5 minimum and Xcode 26.0 minimum, with Xcode 26.1.1 recommended. |
| `OPENAI_API_KEY` and an enabled OpenAI chat model | The `plan` command and OpenAI development agents; the offline demo needs no credentials. |
| [Ollama](https://ollama.com/download) with `/v1/systemone` support and a locally installed Nimble model | Exercising the local gameplay decision adapter; neither the offline demo nor `plan` needs it. |
| Git LFS | Game repositories that store Unreal binary assets in LFS. |
| Bun | The legacy playtester's default OpenCode coding backend; the new Python demo and planner do not need it. |
| Legacy Autopilot provider/account setup | Only for running the existing in-editor playtester; see the Unreal steps below. |

The new development-agent distribution's processor, RAM, and macOS support matrix is not finalized. Python
portability does not establish native plugin compatibility. Measure Unreal and Nimble together on the target Mac
before choosing hardware or claiming real-time gameplay performance.

## Run the Python foundation

### 1. Install from this branch

Run in Terminal. These commands install the Python dependencies declared by this repository; the source
installation still includes inherited Autopilot dependencies.

```bash
git clone --branch feat/ue-agent-foundation-20261031 --single-branch https://github.com/o0grip0o/AUE_TOH.git
cd AUE_TOH
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[ue-agent]"
python -m ue_agent --help
```

For an existing checkout, switch to `feat/ue-agent-foundation-20261031` and use the same environment/install steps.
All subsequent Python commands assume this activated environment and the repository as the working directory.

### 2. Try the offline supervisor demo

```bash
python -m ue_agent --db .ue_agent/demo.sqlite3 demo
```

The demo coordinates researcher, C++, behavior, and reviewer roles through the real LangGraph scheduler using
fake workers. It makes no model calls, starts no editor, and changes no Unreal assets. The expected final job
status is **`awaiting_verification`** because no compile, asset, PIE, or packaged-game checks have run.

Copy the returned `job.id` to inspect its persisted state:

```bash
python -m ue_agent --db .ue_agent/demo.sqlite3 status "<job-id>"
```

Keep `.ue_agent/` local; it is ignored by Git. Reuse the same `--db` path for a job's status and controls.

### 3. Create a plan for an Unreal project

Set your credentials in the terminal environment and choose an OpenAI chat model available to your account.
Replace the values and project path below. This step makes a paid OpenAI request.

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export UE_AGENT_MODEL="<your-enabled-openai-chat-model>"

python -m ue_agent --db .ue_agent/state.sqlite3 plan \
  --project "/absolute/path/DoorEncounter/DoorEncounter.uproject" \
  --goal "Plan a guarded locked door with C++ interaction logic, a UI prompt, and an NPC encounter" \
  --criterion "A locked door refuses interaction until the key is acquired" \
  --criterion "The UI prompt reflects the current interaction state" \
  --criterion "The guard detects and pursues the player"
```

The `.uproject` must already exist. This command plans from the request, criteria, and project reference; it does
not index the project, read editor state, implement the feature, or run tests. The saved job remains an unapproved
Plan-mode job. `pause`, `resume`, and `cancel` manage persisted job state; `resume` does not approve a plan or start
an editor worker. The UE gateway and docked supervisor UI are future implementation slices.

## Run the existing plugin in Unreal on macOS

These steps build and launch the retained **legacy Autopilot playtester**. They do not connect the new supervisor
or Ollama decision adapter. The following native build procedure is based on this repository's packaging path;
it has not yet been exercised on the target Mac/UE 5.8.3 combination.

### 1. Build and install the plugin

Close the Unreal Editor and run from the repository root. Replace both paths with your actual engine and game
folders. The engine folder must contain `Engine/Build/BatchFiles/RunUAT.sh`; the game folder contains your `.uproject`.
For a fresh installation:

```bash
UE_ENGINE_DIR="/Users/Shared/Epic Games/UE_5.8"
GAME_PROJECT_DIR="/absolute/path/DoorEncounter"

"$UE_ENGINE_DIR/Engine/Build/BatchFiles/RunUAT.sh" BuildPlugin \
  -Plugin="$PWD/plugin/unreal/Autopilot/Autopilot.uplugin" \
  -Package="$PWD/dist/Autopilot-Mac" \
  -TargetPlatforms=Mac -Rocket

mkdir -p "$GAME_PROJECT_DIR/Plugins"
ditto "$PWD/dist/Autopilot-Mac" "$GAME_PROJECT_DIR/Plugins/Autopilot"
```

This example uses an Epic Launcher engine. For an engine built from source, replace
`-TargetPlatforms=Mac -Rocket` with `-NoTargetPlatforms` to build editor binaries for that engine. Build against the
same engine installation that opens the project. A Blueprint-only project also needs these compiled plugin binaries.
The installed descriptor should be `<Game>/Plugins/Autopilot/Autopilot.uplugin`.

### 2. Start the legacy service

In an activated terminal at the repository root:

```bash
python -m autopilot serve
```

Keep this terminal open. The default bridge URL is `ws://127.0.0.1:8765/v1/bridge`.
`python -m ue_agent` has no `serve` command and cannot be substituted here.

### 3. Open the Unreal panel

1. Open your `.uproject`, enable **Autopilot** in **Edit > Plugins** if necessary, and restart when prompted.
   The plugin declares Enhanced Input as a dependency.
2. Open **Window > Tools > Autopilot**, or click the orange Autopilot toolbar icon.
3. Connect to the service above. If Unreal cannot find a service, use the panel's **Agent service command** setting
   with the absolute path to this checkout's `.venv/bin/autopilot`; the plugin appends its own `serve` arguments.
   Starting the service manually avoids relying on Unreal inheriting your shell's environment.
4. Complete the legacy account/provider setup and privacy settings. A source checkout does not bundle a service
   installer. Real legacy playtests still require Aura or the original BYOK decision-provider configuration,
   including TypeSafe/Jev; selecting Codex as the coding agent alone does not replace Jev. If using Codex,
   install its additional Python extra with `uv pip install -e ".[ue-agent,codex]"` before starting the service.
   The default OpenCode backend needs Bun; see [contributor setup](CONTRIBUTING.md).
5. Open a playable map, then submit a verification such as “Verify that the door stays locked until I collect the
   key.” The legacy service can start PIE and show its report in the panel.

The `UE_AGENT_GAMEPLAY_*` variables below apply to the new Python policy only. They do **not** reconfigure
`python -m autopilot serve` or the legacy panel. See the [Unreal plugin guide](plugin/unreal/Autopilot/README.md)
for its settings, logs, and full legacy setup.

## Configure local gameplay decisions

This prepares the new policy adapter for integration. It does not enable Ollama inside the legacy Unreal panel.
Install Ollama separately, then start the Ollama app or run `ollama serve` in another terminal. Install the model
only when you are ready to download its weights:

```bash
ollama pull nimble
ollama list

export UE_AGENT_GAMEPLAY_PROVIDER="ollama"
export UE_AGENT_GAMEPLAY_MODEL="nimble"
export UE_AGENT_OLLAMA_URL="http://127.0.0.1:11434"
```

Ollama must expose the decision endpoint, not just `/api/chat`. To check it independently:

```bash
curl --fail http://127.0.0.1:11434/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"model":"nimble","state":{"health":20},"questions":{"next_action":{"type":"choice","instructions":"Choose a legal action for a wounded player.","criteria":{"guard":"Block incoming damage","retreat":"Move away from danger"}}}}'
```

A successful response contains `answers.next_action.choice`. See [Ollama's Nimble documentation](https://ollama.com/library/nimble).
The generic `nimble` tag is **not verified as Bespoke-Nimble-9B-v2**. Confirm checkpoint provenance and record the
installed model digest, quantization, and Ollama version before pinning a tested release configuration.

The adapter uses loopback HTTP, supports 2–26 choices per request, validates returned actions and deadlines, and
never falls back to OpenAI automatically. To explicitly use OpenAI Decisions instead, set
`UE_AGENT_GAMEPLAY_PROVIDER=openai` and `UE_AGENT_GAMEPLAY_MODEL=gpt-6-luna`, plus your OpenAI credentials.
The Python API is `ue_agent.decisions.choose_action()`; there is no integrated gameplay CLI command yet.

## Development setup troubleshooting

| Symptom | What to check |
| --- | --- |
| `No module named ue_agent` | Activate this checkout's `.venv` and install `.[ue-agent]` from the development branch. |
| Missing `OPENAI_API_KEY` or `UE_AGENT_MODEL` | Set them in the terminal running `plan`; the offline demo does not need either. |
| `.uproject` validation error | Pass the absolute path to an existing `.uproject` file, rather than its parent directory. |
| Demo ends at `awaiting_verification` | Expected: the demo does not run Unreal verification gates. |
| Unreal reports missing/incompatible plugin modules | Rebuild the plugin for your engine and Mac, and check Xcode against Epic's requirements. |
| Autopilot panel cannot connect | Confirm the legacy service is running, use its actual bridge URL, and inspect the terminal plus Unreal's `LogPlaytest` output. |
| Ollama returns 404 or an unavailable model | Check `/v1/systemone` support and the exact installed model tag; a running chat endpoint is insufficient. |
| New supervisor or Nimble does not appear in the panel | That integration is pending; installing the legacy plugin does not expose the new development agent. |

---

## Legacy Autopilot

The upstream instructions below describe the retained Autopilot runtime, its original providers, release downloads,
and additional engines. Upstream downloads do not include this fork's new `ue_agent` foundation.

> By the developers of Aura, [www.tryaura.dev](https://www.tryaura.dev/)

![Aura by Ramen](./assets/aura-logo.png)

Autopilot is a continually learning real-time general playtesting system. It supports Unreal Engine 5, Unity 6, and Godot 4 on both Windows and MacOS.

Install Autopilot into your project and let it learn your game, explore your levels, and improve its gameplay run after run.

## Installation

You can find the installation instructions in the [Autopilot docs](https://www.tryaura.dev/documentation/autopilot/)

### Installing pre-built packages

1. Download the latest Autopilot build for your game engine and OS from https://www.tryaura.dev/autopilot/.

2. Install Autopilot into your project.

   **Unreal** (v5.4-5.8)
   1. Unzip the download. Move `Autopilot/` into your project's `Plugins/` folder (create a `Plugins/` folder yourself if your project doesn't have one yet). You should therefore have `<YourProject>/Plugins/Autopilot/Autopilot.uplugin`.
   2. Open your project. Click the orange Autopilot icon to open Autopilot.

   **Unity** (v6 or later)
   1. Unzip the download. It should contain the file `com.ramenvr.autopilot-<version>.tgz`.
   2. Open your project. In Window > Package Management > Package Manager, choose + > Install package from tarball..., and pick that file.
   3. Open Window > Autopilot.

   **Godot** (v4.7 or later)
   1. Unzip the download. Move `autopilot/` into your project's `addons/` folder.
   2. Open your project. Enable Autopilot in Project > Project Settings > Plugins. The Autopilot dock appears on the right.

3. Follow the Autopilot setup flow.
   1. We recommend using Autopilot with your Aura account. Click `Create Account` if you don't yet have an Aura account, or `Sign in` if you are a returning user.
   2. Autopilot runs its setup, and finally redirects you to the signup/signin page. Complete your signin/signup process.
   3. Upon successful authentication, you should see the "Agent service ready" page. Click Continue.
   4. You have the option to enable/disable sharing your runs to improve Autopilot. As the developers of Autopilot, we would of course appreciate your enabling this!
   5. (Optional) Run the 10-minute exploration run to populate your Autopilot project memory. It is safe to skip this and jump straight to sending your own prompt.
   6. Prompt Autopilot! See the types of prompts you can try in [Usage](./README.md#usage).

### Installing from source

You can install Autopilot from source. This is supported for Unreal Engine only. This method allows you to build Autopilot against an Unreal source build, and places the Autopilot plugin into your Unreal project's Plugins folder automatically.

```powershell
git clone https://github.com/ramenvr/autopilot.git
cd autopilot
powershell -ExecutionPolicy Bypass -File tools\build_unreal.ps1 `
  -EngineDir "C:\path\to\UnrealEngine" `
  -PluginsDir "C:\path\to\YourProject\Plugins"
```

Once that has completed, follow the Autopilot setup flow as shown in Step 3 of [Installing pre-built packages](./README.md#installing-pre-built-packages).

## Usage

The main way to use Autopilot is through the **Autopilot plugin** in your editor. This works in Unreal Engine 5, Unity 6, and Godot 4 on both Windows and MacOS. This path uses your Aura plan, or your BYOK API keys.

Alternative ways to use Autopilot include:

- **In Aura**: You can also use Autopilot in Aura. Only Unreal and Unity are supported through this path. This path uses your Aura plan.
- **In Claude Code / Codex**: You can use Autopilot through Claude Code and Codex via Autopilot's skills and MCP server. To set this up, run `autopilot connect claude` and/or `autopilot connect codex` in your terminal, then prompt Claude Code / Codex to "Use Autopilot to ...". This path uses your own Claude/ChatGPT subscription.

An Autopilot prompt is one of 4 types:

- **Exploration**, e.g. "Explore the crafting system in Lvl_Main."
- **Testing**, e.g. "Go through the currently open level and tell me everything that looks wrong."
- **Verification**, e.g. "Verify that the tree shakes when you hit it with an axe."
- **Goal**, "Kill the boss while keeping your health above 20% of its maximum value."

For every prompt, Autopilot will automatically launch a PIE window and start reading your project's source code, probe PIE, and start playing according to your prompt. Autopilot plays by using an LLM coding agent to craft harnesses for a decision model according to what it knows about your game, and requests decisions (action choices) from the decision model during gameplay. Once Autopilot is done, the PIE window will close automatically, and Autopilot generates a report for you.

Your first few runs allow Autopilot to learn about your game as it gradually populates its memory. Expect some suboptimal behavior for the first few harness attempts. **Autopilot visibly improves the more it plays your game**, and later harness attempts and runs both take a shorter time to complete a given task, as well as exhibit more intelligent behavior (e.g. faster dodging, equipping better weapons, playing smarter strategies, better aiming).

## Uninstallation

1. In Autopilot, go to Settings and click Uninstall. By default, Autopilot keeps your project's memories; you can choose to delete memories instead (this is a destructive action).
2. Remove the plugin from each project: Unreal, close the editor and delete `Plugins/Autopilot/`; Unity, remove the Autopilot package in the Package Manager; Godot, disable Autopilot in Project > Project Settings > Plugins, then delete `addons/autopilot/`.

---

## Contributing

Contributions are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to set up a development environment, run the tests, and add support for a new engine. Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[Apache License 2.0](LICENSE). The plugins bundle fonts under the SIL Open Font License; see each font's `OFL` file.
