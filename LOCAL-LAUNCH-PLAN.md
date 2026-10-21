# Yelena Xiomora local launch preparation - awaiting execution approval

Current voice status, 2026-10-21: the user selected the downloaded Lisa Reichert
XTTS model as the default. The isolated runtime is installed, its localhost
service is running on cuda:0, and a 5.53-second speech sample was generated.
This supersedes the ElevenLabs default below. See LOCAL-SERVICES.md.

Latest voice selection, 2026-10-21: the user supplied the existing Pip dotenv
file and requested a female voice. Yelena now selects ElevenLabs Jessica,
reading credentials from that external file without changing Pip. Speech is
cloud-based; the earlier XTTS selection below is superseded. See LOCAL-SERVICES.md.

2026-10-21 update: reuse Lisa Ann's existing llama.cpp server and this node's
Companion XTTS service. The connection settings, environment-key support and
XTTS adapter are now added to this checkout. See [LOCAL-SERVICES.md](LOCAL-SERVICES.md)
for current configuration and blockers. The proposed model downloads below
are superseded; a saved Lisa Ann API key and running XTTS service are still needed.

LATEST VERIFIED STATUS: User approved the two offline navigation test files; 29 tests passed. Initial two fixture errors were resolved by a fresh task-specific D:/Temp basetemp, without changing project logic. Device/network guards recorded zero attempts. Yelena Xiomora requires a female avatar; none is selected yet. Live startup and capture remain unapproved. Earlier pending-test notes below are historical and superseded. See AVATAR-SETUP.md and offline-navigation-tests.txt.
No project/plugin/runtime model code was executed during this follow-up. No model or extra server was installed. Brandon selected Yelena Xiomora as the character/build name. Active display and prompt names reflect that choice. Voice and personality details remain unspecified.

## Smallest no-paid-API path examined
- LLM server: portable official llama.cpp, on A:\Tools\Gabriel\llama.cpp. Yelena accepts OpenAI-compatible /v1/chat/completions (LM Studio, Ollama, llama.cpp and vLLM are documented alternatives). Portable llama.cpp avoids a global install and supports explicit bind/model paths. LM Studio is the README's default GUI option; no existing running server found.
- Lowest-download functional trial: official Qwen3-0.6B Q8_0, 639,446,688 bytes. This is a capability smoke-test candidate, not a promise of good companion/tool behavior.
- More useful compact baseline: official Qwen3-4B Q4_K_M, 2,497,280,256 bytes. Use a limited tool set and non-thinking/concise behavior; validate tool calls locally before enabling actions. No vision in these text-only choices.
- STT: built-in Parakeet, smallest documented realtime_eou_120m-v1-q8_0.gguf is 176,001,472 bytes. Default tdt-0.6b-v3-q8_0.gguf is 940,663,680 bytes. The tiny streaming path is documented but WIP; larger default is fallback if unreliable.
- STT native engine: CPU archive 673,218 bytes; Vulkan archive 17,902,929 bytes. Both are HoppouAI mirrors and must be reviewed/hashed before load. CPU is the smallest download. GGUF model license/provenance must be reviewed at download time.
- VAD: src/local_live/stt.py loads snakers4/silero-vad via torch.hub with trust_repo=True. This is another downloaded-code execution approval, not just a weight download. Pin a reviewed revision/local checkout rather than implicitly trust mutable main. Budget additional small model/cache downloads, exact bytes not yet enumerated.
- TTS: official plugin pocket_tts at ProjectGabriel-Plugins commit e1e521b9aa9a170567122531d0b1a9376f7bcdde, manifest 0.1.5. CPU, no API/account/server needed; plugin docs estimate ~400 MB weights plus selected built-in voice and tokenizer/cache files. Use a built-in voice, no voice cloning. Requires pocket-tts>=2.1 plus existing torch/numpy/stream2sentence/nltk/safetensors. Current PyPI pocket-tts 3.3.0 additionally needs einops and sentencepiece; resolve/pin in the isolated venv without replacing the tested torch trio. Plugin starts background warmup on load.
- Total model payload: minimum examined ~1.22 GB plus runtime/wheels/VAD/voice caches; practical 4B + default STT ~3.84 GB plus these extras. These totals use the plugin's approximate 400 MB figure, not measured complete transfer sizes. No embedding model needed for SQLite keyword memory.

Official portable llama.cpp stable pointer v0.6.0 resolves to b11429. CPU x64 archive 19,398,918 bytes; Vulkan x64 archive 33,337,769 bytes. Vulkan avoids adding a global CUDA toolkit and is an optional GPU choice. CPU is smallest. Source URLs:
https://github.com/ggml-org/llama.cpp/releases/download/b11429/llama-b11429-bin-win-cpu-x64.zip
https://github.com/ggml-org/llama.cpp/releases/download/b11429/llama-b11429-bin-win-vulkan-x64.zip
https://huggingface.co/Qwen/Qwen3-0.6B-GGUF
https://huggingface.co/Qwen/Qwen3-4B-GGUF
https://huggingface.co/mudler/parakeet-cpp-gguf
https://github.com/HoppouAI/ProjectGabriel-Plugins/tree/e1e521b9aa9a170567122531d0b1a9376f7bcdde/pocket_tts
https://github.com/kyutai-labs/pocket-tts

Other documented local TTS choices: omnivoice_tts (GPU Python model), omnivoice_cpp_tts (native DLL plus GGUF, automatic Windows downloads), breeze_tts (separate native websocket server plus GGUF). These add larger/extra moving parts. Built-in Hoppou and Chirp need cloud credentials; TikTok provider sends text to https://ottsy.weilbyte.dev/api/generation, a third-party endpoint, so it is not the proposed offline path.

## Correction: exact cloud paths
Earlier handoff repeated stale config comments about mandatory Gemini sub-agents. Actual code at the pinned commit shows:
- src/memory/tools.py: recall_memories explicitly performs keyword/vector retrieval then returns memories to the active main model, with no separate generative API call. SQLite + rag_enabled=false stays local here.
- src/memory/rag.py: _init_rag selects local embedding HTTP vs Gemini; genai.Client at line 132 and embed_content at lines 156/178 are the Gemini embedding path. Keep rag_enabled=false or use local embeddings later.
- src/gemini_live/session.py: line 187/190 creates the Gemini compression summary call; belongs to GeminiLiveSession. LocalLiveSession is a separate class and trims message history instead. Main chooses it under backend=local.
- src/gemini_live/session.py: line 531 is the Gemini Live client; not selected by backend=local.
- src/music_gen.py: line 100 is the Gemini music client; music_gen.enabled=false.
- Optional diary plugin uses Gemini and is not installed/enabled. Discord has its own cloud session and remains disabled.
- Source comments claiming local recall/summary requires flash-lite appear stale. No mandatory Gemini call was found in the examined local session path. This is static evidence, not a network-isolation test or a guarantee covering unexamined optional plugins.

## Prepared loopback/inactive changes
main.py control dashboard host and src/web/app.py standalone default now bind 127.0.0.1, not 0.0.0.0. Exactly two source lines changed; loopback-defaults.patch records them. The checkout remains based on commit 203e1fd449ee6a345b3cd6bcc659330d778828e5 with this local patch. Static AST parsing of both changed files passed.
Config uses 127.0.0.1:1234/v1 for LLM, blank Gemini key, custom compression off, capture/motion/social/plugins off, local memory and an unconfigured TTS placeholder. Nothing is listening or capturing.
OSC receive already binds 127.0.0.1 upstream; main still constructs that listener automatically. Tracker module initializes bettercam at import, audio manager starts runtime audio later, and keyboard controller is constructed at module scope. These need explicit permission or a reviewed standalone-mode code change before launching main. A config toggle alone is insufficient.

## One consolidated launch decision/permission bundle for parent
Ask Brandon to choose practical local setup (4B LLM + Pocket built-in voice + default STT) or minimum-download trial (0.6B + tiny STT), choose a built-in voice (character/build name is Yelena Xiomora), and authorize the following clearly bounded actions together if desired:
1. Download/provision the selected official portable LLM server/models and reviewed Pocket plugin/deps on A:/D: as above; verify immutable revisions/hashes before execution. No paid APIs, accounts or global installs.
2. Execute the pinned Yelena offline navigation tests; then execute the reviewed local inference server, Pocket model/plugin, Parakeet DLL, and pinned Silero hub code. Opening only localhost listeners (LLM 1234, dashboard 8766, OSC receive 9001 if needed), no firewall changes, no LAN/public exposure. Proposed LLM command after inspecting its extracted executable is `llama-server.exe -m D:\Models\Gabriel\Qwen3-4B-Q4_K_M.gguf --host 127.0.0.1 --port 1234 --jinja` (adjust model for trial). Do not execute until artifacts are concretely inspected and action-time approval covers them.
3. Choose first experience: standalone text/mock only (requires reviewed no-device startup adaptation), local microphone/speaker conversation (explicit mic/audio permission, and remove unnecessary screen/OSC startup), or VRChat integration (explicit screen capture + OSC movement/chatbox permission and user-prepared private session). None authorizes account login, public-world interaction, Discord messaging or desktop control.
4. For later VRChat voice routing, determine existing virtual cables before installing any audio drivers; driver/global changes need separate concrete approval if actually necessary. Motion generation, Unity/avatar modifications, gated body/encoder models and voice cloning are deferred optional features, not prerequisites for the first local companion.

Pending offline test approval does not authorize plugin/native-code execution or capture. No runtime approval has arrived in this thread.
