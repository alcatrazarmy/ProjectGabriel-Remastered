# ProjectGabriel -- Copilot Instructions

> **Owner:** HoppouAI
> **Repo:** ProjectGabriel-Remaster

## Overview

ProjectGabriel is a real-time AI companion for VRChat powered by **Gemini Live** (WebSocket audio streaming). It listens to people in VRChat, responds with voice, and controls VRChat via OSC. It includes person following via YOLOv8 computer vision and face tracking via YOLOv8 face.

The project is a monolithic Python app. `main.py` is the entry point, `supervisor.py` handles auto restart on crash. Config lives in `config.yml` with a `.example` template tracked in git. A WebUI (FastAPI on port 8766) provides dashboards, memory management, and OBS overlays. An optional Discord bot runs a separate Gemini Live session.

## Development Conventions

- Code should be self explanatory. Only comment complex logic, never obvious stuff.
- No em dashes anywhere: code, comments, commits, docs.
- Config changes: add the property to `config.yml.example` and to the `Config` class in `src/config.py`.
- All async code uses `asyncio`. Blocking calls go through `asyncio.to_thread()`.
- Commit often; each meaningful change gets its own focused commit. Keep commit messages casual and human sounding. Never mention AI cleanup tasks.
- Sensitive files (config.yml, prompt YMLs) are gitignored. Only `.example` templates are tracked.
- `config.yml` must NEVER be committed or pushed.

## SDK: Google GenAI

- **Always** use `google-genai` (`from google import genai`). Never `google-generativeai`.
- Client: `genai.Client(api_key=...)` created per session.
- Live API: `client.aio.live.connect(model=..., config=...)`.
- Tool calls in Live are manual: execute the function, send `FunctionResponse` back.
- Thinking config: `types.ThinkingConfig(thinking_budget=..., include_thoughts=...)` in `LiveConnectConfig`.
- Context window compression: `types.ContextWindowCompressionConfig` with `SlidingWindow`.
- Session resumption: handle persisted to `data/session_handle.txt`, 2 hour expiry. If the stored handle is missing, expired, or rejected, delete `data/session_handle.txt` and start a new Live session without resumption. Each Live session stores its resumption handle in its own file: the main session uses `data/session_handle.txt`, and the Discord session uses `data/discord_session_handle.txt`. Never share a handle between sessions.

## Key Architecture

### API Key Rotation
Keys in `config.yml` (primary + backup list). On 429/quota errors, `Config.rotate_key()` cycles to the next key and the session reconnects automatically. After all keys have hit quota errors, wait 5 minutes, reset the rotation to the primary key, and try again. Repeat this cycle until a connection succeeds or the app is restarted. For any other Live session disconnect or error (not 429/quota), retry the connection with exponential backoff, starting at 1 second and capped at 30 seconds. After 5 consecutive failures, stop reconnecting, log an error with the last failure reason, and surface the outage in the WebUI and console.

### Audio Pipeline
Mic -> PyAudio input (raw PCM 16kHz mono) -> Gemini Live -> Gemini Live audio output (raw PCM, sample rate per the Live API response, typically 24kHz) -> `AudioManager.process_output_audio()` (boost/distortion) -> PyAudio output. Music/SFX go through pygame.mixer to system output.

### VRChat OSC
Chatbox: `/chatbox/input`, typing indicator: `/chatbox/typing`, voice toggle: `/input/Voice`, movement: `/input/MoveForward`, `/input/LookHorizontal`, `/input/Run`. Grab/Drop: `/input/GrabRight`, Use: `/input/UseRight`. Smooth look uses EMA with smoothing factor `alpha` from config (default 0.2). On a new look target, ramp the input from the current value to the target over 0.5 seconds using linear interpolation. Crouch/crawl via pynput keyboard. Chatbox messages are limited to 144 characters per page, including the `(1/N)` page suffix. Split on word boundaries where possible, and hard-split words longer than the available space.

### Memory System
Memory storage uses MongoDB Atlas. If the MongoDB connection fails at startup, use SQLite for the session and log a warning with the connection error. If MongoDB fails at runtime, keep using SQLite until the next app restart. Types: `long_term`, `short_term`, `quick_note`. Vector search backend is selected by `rag_provider` in the memory config: `gemini` uses Gemini embeddings, `local` uses local LM Studio + ChromaDB. If unset, default to `gemini`. Tools: `saveMemory`, `searchMemories` (keyword + semantic lookup returning raw matching records), `deleteMemory`, `listMemories` (browse by `memoryType`: `long_term`, `short_term`, or `quick_note`, and/or by `category`, a free-text label stored on each memory), `recallMemories` (AI-summarized search across all memories). Call `recallMemories` when the user asks a conversational question about past events or preferences and wants a summary. Call `searchMemories` only when a specific memory is requested by exact keyword or the raw matching records are wanted. Do not call both for the same request. Each tool is a separate `FunctionDeclaration` to avoid Gemini Live 1011 errors.

### Prompt & Personality System
Prompts in `config/prompts/`: base prompts (`prompts.yml`), auto appends (`appends.yml`), switchable personalities (`personalities.yml`). Supports `{date}`, `{memories}` placeholders. Model can call `switchPersonality` to change modes mid session. It is a registered tool (`PersonalityTools` in `src/tools/personalities.py`) taking a `personalityId` that must match an entry in `personalities.yml`; unknown or disabled IDs return an error result without switching.

## Adding a New Tool

1. Create a file in `src/tools/` with a class decorated `@register_tool` extending `BaseTool`.
2. Implement `declarations(self, config=None)` returning `list[types.FunctionDeclaration]`.
3. Implement `async handle(self, name, args)` returning a dict result or `None` if not handled. If handling raises, catch and log it and return a dict such as `{"result": "error", "error": "<short message>"}` so the Live session still receives a `FunctionResponse`. Never let an exception escape `handle()`.
4. Import the module in `src/tools/_handler.py :: ToolHandler.__init__()` to trigger registration.
5. Include `\n**Invocation Condition:**` in each tool's description.
6. Access shared state via `self.handler` (audio, osc, tracker, config, etc).

```python
from google.genai import types
from src.tools._base import BaseTool, register_tool

@register_tool
class MyTool(BaseTool):
    def declarations(self, config=None):
        return [types.FunctionDeclaration(
            name="myTool",
            description="Does something.\n**Invocation Condition:** Call when ...",
            parameters={"type": "OBJECT", "properties": {
                "arg1": {"type": "STRING", "description": "..."},
            }, "required": ["arg1"]},
        )]

    async def handle(self, name, args):
        if name == "myTool":
            return {"result": "ok", "data": "..."}
        return None
```

## Plugin System

Plugins live in `plugins/<name>/` with a `plugin.yml` manifest and `__init__.py`. Classes subclass `src.plugins.Plugin` with `setup(ctx)` / `teardown(ctx)`. The `PluginContext` exposes registries for tools, TTS, STT, chatbox sources, prompt contributors, events, and mid session text injection. A `ctx.discord` sub context does the same for the Discord bot's separate Gemini Live session. Plugins are loaded before `GeminiLiveSession` so `@register_tool` fires before `ToolHandler` reads the registry. If a plugin's `setup(ctx)` raises an exception, log the error with the plugin name, call that plugin's `teardown(ctx)` if setup partially completed, skip the plugin, and continue starting the app. Plugins live in a separate repo at [HoppouAI/ProjectGabriel-Plugins](https://github.com/HoppouAI/ProjectGabriel-Plugins).

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point |
| `supervisor.py` | Auto restart on crash |
| `src/config.py` | Config class, key rotation |
| `src/audio.py` | Audio input/output pipeline |
| `src/gemini_live/session.py` | Gemini Live session management |
| `src/gemini_live/config_builder.py` | Live API config construction |
| `src/tools/_handler.py` | Tool registry and dispatch |
| `src/plugins/loader.py` | Plugin manager |
| `src/memory/_base.py` | Memory system backend |
| `src/vrchatapi.py` | VRChat REST API client |
| `src/cli.py` | Colored logging, startup banner |

