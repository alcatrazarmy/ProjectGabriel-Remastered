# Yelena Xiomora - Project Yelena Remastered setup on Deauxma

Current voice status, 2026-10-21: local Lisa Reichert XTTS is now the default,
per the user's choice. The isolated A:/Tools/yelena-tts runtime and localhost
server generated a verified 5.53-second sample on cuda:0. No microphone or
companion session was started. ElevenLabs remains a manual alternative.
See LOCAL-SERVICES.md; Lisa Ann authentication is still unresolved.

Latest voice update, 2026-10-21: ElevenLabs Jessica is now selected using the
user-supplied Pip dotenv file. Its API key was accepted and Jessica is labeled
female. Pip's original voice/settings remain unchanged. This supersedes the
XTTS voice choice below; Lisa Ann still needs a valid saved API key. See
[LOCAL-SERVICES.md](LOCAL-SERVICES.md). No live speech was generated.

2026-10-21 service integration update: this checkout now targets the existing
Lisa Ann llama.cpp server and includes an adapter for the existing local
Companion XTTS service. See [LOCAL-SERVICES.md](LOCAL-SERVICES.md). The saved
Lisa Ann API key is missing and XTTS port 8095 is not listening. Earlier plans
to provision a new LLM/Pocket TTS stack are superseded. End-to-end startup
remains unverified.

LATEST VERIFIED STATUS: User approved the two offline navigation test files; 29 tests passed. Initial two fixture errors were resolved by a fresh task-specific D:/Temp basetemp, without changing project logic. Device/network guards recorded zero attempts. Yelena Xiomora requires a female avatar; none is selected yet. Live startup and capture remain unapproved. Earlier pending-test notes below are historical and superseded. See AVATAR-SETUP.md and offline-navigation-tests.txt.
Status: staged installation; the companion has NOT been launched or verified end to end.

## Source and placement
- Host verified by hostname: Deauxma.
- Official repository: https://github.com/HoppouAI/ProjectGabriel-Remastered
- Checkout: D:\Projects\ProjectGabriel-Remastered
- Branch main, commit 203e1fd449ee6a345b3cd6bcc659330d778828e5.
- Latest release inspected: v2.0.1 (2026-06-13). Chose current main because it includes newer motion and Parakeet integration.
- `git branch --contains origin/motion-server` returned main: the README's separate-branch warning is outdated.
- Python 3.12.15: A:\Tools\Python. Dedicated venv: A:\Tools\gabriel-venv.
- Downloads/caches: D:\Caches\uv and D:\Caches\Gabriel; temp: D:\Temp.
- A:\AGENTS.md and D:\AGENTS.md require applications/runtimes on A:, projects/data/caches on D:. Existing C: executables were reused; no migration or global PATH changes performed.

## Newly confirmed features
- Standalone WebUI and Discord support; VRChat is optional.
- Configurable personas and voices, persistent SQLite memory, optional local semantic retrieval through LM Studio embeddings and Chroma.
- Drop-in tools, STT/TTS and event plugins; OBS overlay, soundboard/music, optional generated music.
- Avatar movement/chatbox through OSC; VRChat account APIs; raycast sensing, voxel mapping, exploration and waypoints.
- Generated full-body motion is already in main: DART and NVIDIA ARDY backends, with avatar rig/Unity setup needed separately.
- Separate social messaging server; Vencord plugin can control Discord calls (left untouched).

## Completed
- Cloned official source and inspected README, release notes, branches, setup/run/supervisor/main code, config, local STT implementation and relevant motion/Unity/plugin/social/WebUI docs.
- Installed 157 binary dependencies plus development tools in the isolated venv, excluding source-only discord-protos.
- Prepared config.yml for local mode, blank credentials, SQLite memory, and inactive vision/tracking/motion/plugins/Discord/social services.
- Configured the user-selected character/build name Yelena Xiomora in config/prompts. Personality and voice details remain unspecified. NOTICE.md restricts operation under the project's Gabriel identity. No upstream persona was copied.
- Disabled 143 statically identified named tools in config/tools.yml. This is NOT a security sandbox: upstream auto-enables newly discovered tools, and startup creates audio/OSC objects independently of tool switches.
- environment.ps1 sets process-local non-C caches and offline HF defaults. Dot-sourcing it does not launch anything.
- No project Python module was imported or executed, no mic/screen capture, OSC, login, cloud inference, social message, security change or service listener was activated.
- Existing ComfyUI processes and listener 8188 were observed and left running. True Up environment was not modified.

## Verification
- 219 Python source files parsed with ast.parse successfully, without executing their code.
- Config YAML read/written successfully; setup-verification.json records static results.
- Python 3.12.15 and PyYAML import verified.
- Initial torch 2.12.0+cu126 import and CPU 2x2 matrix multiplication passed. Its architecture list omitted Blackwell; CUDA availability alone is not proof it can compute on RTX 5070.
- GPU inventory returned AMD Radeon Graphics and two NVIDIA RTX 5070 entries; no cross-node inventory inferred.
- dependency inventory: installed-packages.json. pip check found missing discord-protos, required by discord-py-self.
- GPU replacement and final verification will be recorded in gpu-verification.json / dependency-check.txt if completed.

## Approval required via parent
1. Source-only build: `uv pip install --python A:\Tools\gabriel-venv\Scripts\python.exe --no-deps D:\Temp\discord-protos-0.0.2.tar.gz` with environment.ps1 applied. Source https://files.pythonhosted.org/packages/3a/7c/4b9eaf1f85caa5ff93caa948ee47a2fc5be2d2bbd4b60d3f989da84c8140/discord-protos-0.0.2.tar.gz ; SHA256 23953a05f32beedb40b708ec4b457530a6196a49c8d75d337ae9282a2a41c997. Inspected setup.py reads requirements/version/README and calls setuptools; pyproject uses setuptools/wheel. Risk: source build executes third-party code as Brandon. No source build has run.
2. Project execution: reviewed/mock-only tests (e.g. tests/test_pathfinder_and_waypoints.py) execute HoppouAI Python code from the pinned checkout; request explicit action-time approval before running these or any application entry point. Review imports before selecting tests, as main imports tracker which preinitializes desktop duplication even with tracking disabled.
3. Local speech: src/local_live/parakeet_assets.py auto-downloads a native DLL bundle from https://github.com/HoppouAI/ProjectGabriel-Plugin-Resources/raw/main/parakeet_cpp_asr/parakeet-cpp-vulkan-win64.zip (CPU variant also exists), and GGUF models from mudler/parakeet-cpp-gguf on Hugging Face. Source does not check a pinned hash for the DLL. Must download/inspect/hash and obtain explicit approval before loading it.
4. Actual runtime capture/OSC/desktop/account/social behavior needs its own explicit permissions. main.py binds dashboard to 0.0.0.0:8766; change to loopback before any local-only launch. No listener has been opened.

## Remaining functional choices and limitations
- No LM Studio/Ollama process or listeners on 1234/11434 found. A local LLM must be provisioned or an existing approved endpoint supplied.
- Local backend refuses to start without external TTS. Built-ins are cloud Hoppou, Google Chirp and TikTok; a reviewed local TTS plugin is needed for an offline goal. Current tts.provider is deliberately unconfigured, not a working voice.
- Current config comments say local mode retains Gemini memory/summary sub-agents; do not promise fully offline until code paths are audited/replaced.
- Main startup is not a safe smoke-test even with feature toggles disabled; it constructs audio/OSC managers.
- run.bat/supervisor.py expect repo-local .venv. Our venv follows machine policy on A:. Do not use those launchers. After approval/config completion, use the explicit A: python executable with environment.ps1 and reviewed main entry point, or adapt supervisor path.
- Full-body motion not installed: separate environment, models, checkpoint execution and avatar Unity rig required. DART body models require registration/terms; ARDY text encoder docs suggest a community quant of gated Llama. Do not treat a mirror as permission to bypass upstream licensing.
- Code is AGPL-3.0 with NOTICE persona terms; use a distinct identity. User needs rights to any chosen avatar and model assets.

Suggested focused question: May I complete the inspected discord-protos source build and run the pinned repository's local mocked tests, while leaving all capture, VRChat and external services inactive?

## GPU override reproducibility
The upstream lock selects CUDA 12.6. The reviewed Deauxma override is:
`uv pip install --python A:\Tools\gabriel-venv\Scripts\python.exe --only-binary :all: --no-deps --index-url https://download.pytorch.org/whl/cu128 torch==2.9.1+cu128 torchvision==0.24.1+cu128 torchaudio==2.9.1+cu128`
These are official matching wheels and satisfy the project's lower version bounds. `uv sync --frozen` will restore upstream CUDA 12.6, so reapply this override after a sync. No GPU driver or CUDA toolkit was installed globally.

Exact initial dependency installation command, with environment.ps1 applied:
`uv sync --frozen --no-install-project --no-install-package discord-protos --no-build`
This installs dependency wheels only; no editable build of the repository itself was executed. Config and prompt files are gitignored upstream and local to this installation.

## Final checkpoint
GPU correction completed: torch 2.9.1+cu128, torchvision 0.24.1+cu128, torchaudio 2.9.1+cu128. All three imports passed. Both detected RTX 5070 devices report compute capability 12.0; sm_120 is compiled in. A 32x32 ones matrix multiplication on each GPU returned sum 32768.0. See gpu-verification.json.

Discord is optional at core startup: main.py lines 296-310 import discord_bot.bot only inside `if config.discord_bot_enabled`. Search of src found no direct import of discord. Missing discord-protos can therefore stay deferred while Discord is disabled; it is not the current core setup blocker. The package inventory check still truthfully reports its dependency warning because discord-py-self is installed. Do not interpret this as a successful complete dependency check.

Replace the earlier suggested build question with this narrower request:
Approve offline-only execution of pinned commit 203e1fd449ee6a345b3cd6bcc659330d778828e5 via `A:\Tools\gabriel-venv\Scripts\python.exe -B -m pytest tests/test_pathfinder_and_waypoints.py tests/test_voxel_nav.py -q -p no:cacheprovider`, after reviewing all imported modules for startup side effects. Use D:\Temp for temporary files, no network or device streams, no main.py/supervisor.py, no account access. This executes third-party Python code; no such test has run yet. Discord source-build approval is needed only if enabling that optional integration later.

A separate backend decision remains: provision a local OpenAI-compatible LLM server and a reviewed local TTS plugin, or identify an already-approved local endpoint. No server was found at the common LM Studio/Ollama ports. No credentials should be shared in chat. Do not activate the companion until capture/OSC permissions and runtime risks are explicitly addressed.

FOLLOW-UP CORRECTION: See LOCAL-LAUNCH-PLAN.md, which supersedes the earlier statements about mandatory local Gemini sub-agents. Actual recall is local retrieval; Gemini compression belongs to the cloud session. Dashboard defaults are now patched to loopback (two source lines), recorded in loopback-defaults.patch. The earlier temporary name and unnamed placeholder have been superseded by Brandon's selected character/build name, Yelena Xiomora. All runtime execution remains pending.


2026-10-15 name decision: Brandon selected Yelena Xiomora. Display name, idle banner and base prompt metadata updated; upstream names and source history preserved. No personality/backstory/voice was invented. Runtime and offline test approvals remain pending; nothing launched.
