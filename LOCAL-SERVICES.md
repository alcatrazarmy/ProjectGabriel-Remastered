# Lisa Ann AI and Yelena's voice

## Original application — current status

Headset update: the user is using **Steam Link**. The app now selects
`Microphone (Steam Streaming` and `Speakers (Steam Streaming Speak` by name
prefix, preferring the Windows MME mixer. These names take priority over
numeric audio indices, which changed when SteamVR started. Both input and
output streams opened successfully after restart. In the headset, view the
Yelena window through SteamVR's desktop view. Hearing and a spoken round trip
still require confirmation from the headset user.

Use `run.bat` and the original dashboard at `http://127.0.0.1:8766`.
`run.bat` reuses the running Lisa voice service or starts it hidden and waits
for the configured voice to become ready before launching the original app.
Automatic startup logs are in `data/voice/autostart.log`. The voice service
stays running after the app closes so subsequent launches can reuse it.
On 2026-10-21, a typed message through this dashboard received a real
Qwen3-235B reply from Lisa Ann and triggered a successful local XTTS request.
When headset input is unavailable the app keeps typed chat available and can
fall back to the Windows default speaker. Steam Link microphone and output
streams are now open; actual headset listening remains unconfirmed.
Reconnect the Quest, recheck audio-device selection, and restart the original
app before testing headset conversation. Open the animated avatar with
`Start-Yelena-Window.ps1` as described below.

## Standalone window (Quest 3 via Steam Link desktop view)

The avatar window now connects to the original app on port 8766. Messages
entered here use that app's conversation session and speech output. The window
reads a small playback meter to drive mouth opening, with skeletal breathing,
head movement, blinking, speaking gestures, and a Wave button. A live browser
test verified a typed message, the app's reply, and speech-driven mouth motion.
The audio-output selector in this window applies only to its voice tests;
conversation audio follows the original app's configured output.

Run `./Start-Yelena-Window.ps1` to start the loopback-only window at
`http://127.0.0.1:8768` and open it in an Edge app window. It uses the existing
private VRM without copying it into the repository. The browser profile and
runtime logs stay under ignored `data/desktop-window/` on D:.

Click **Test Lisa's voice** for the verified local sample, or enter text and
click **Read text aloud** to generate new local speech. The mouth opens with
the audio amplitude. **Send** forwards your message to the original application;
that session owns the conversation history, AI connection, and speech playback.

Select the headset audio output in the window or in Windows Sound settings.
This PC exposes `Microphone (VDVAD Wave)` and `Speakers (VDVAD Wave)` through
Virtual Desktop. The window can be viewed on the Quest through Virtual Desktop.
It does not yet transcribe the headset microphone. It starts no VRChat/OSC,
screen capture or tool-control loop of its own. The avatar has skeletal idle
and speaking movement, blinking, and a manual wave.

The service remains running after the window closes. The startup script reuses
the running service, and records its PID in `data/desktop-window/server.pid`.
See `QUEST-AVATAR-STATUS.md` for the new avatar inventory and test limits.

This checkout uses Lisa Ann's llama.cpp server for responses and the downloaded
Lisa Reichert XTTS model for local speech. The voice service runs on this node's
GPU and binds only to 127.0.0.1:8095. No ElevenLabs requests are made by the
selected voice provider. Microphone/STT and avatar integration are separate.

The local `config.yml` is configured as follows (keep credentials out of Git):

```yaml
backend: local
local:
  llm:
    base_url: http://192.168.50.190:8080/v1
    base_url_env: LISA_ANN_BASE_URL
    api_key_env: LLM_KEY
    env_file: C:/Users/brandon/.jarvis/.env
    model: auto
tts:
  provider: xtts_service
  xtts_service:
    base_url: http://127.0.0.1:8095
    voice: Lisa Reichert
    model_dir: A:/Public_Domain_Lisa_Reichert_XTTS_2.0.2
    timeout: 180
plugins:
  enabled: true
```

Merge these sections into an existing config; preserve its other settings.
`auto` selects the sole model listed by `/v1/models`. If the server advertises
multiple models, set `local.llm.model` to the desired ID instead.
Environment values come from the process first, then saved Windows user
variables, then the explicitly configured external environment file for the
named key. The existing Jarvis `LLM_KEY` authenticated successfully; no secret
was copied into this checkout. A missing key produces a clear connection error.

## Local voice startup

The model already cloned by the user at the path above is reused in place.
Its model, speaker data and reference WAV match the repository's SHA-256
hashes. New models should be stored under `D:/Models/Yelena`; no model files
were moved or duplicated. This runtime reads the existing checkpoint with
PyTorch weights-only loading enforced and Hugging Face offline mode enabled.

The isolated runtime is `A:/Tools/yelena-tts`, with caches under
`D:/Caches/Yelena/xtts`. It uses Coqui TTS 0.28.0 and PyTorch/TorchAudio
2.8.0+cu128. `requirements-xtts.lock.txt` records the complete tested versions.
The companion's existing environment was not modified.

Start the voice service in a separate terminal and leave it running:

```powershell
.\Start-Yelena-Voice.ps1
```

Use `-Device cpu` if CPU operation is desired. The launch script does not
start the AI companion or microphone. The server loads the downloaded model
and its reference recording directly; it does not download a default XTTS model.
It implements `/health`, `/voices` and `/tts`, returning PCM WAV audio that
the existing adapter converts to the companion's audio chunks.

To recreate the environment, use an installed `uv` executable:

```powershell
$env:UV_CACHE_DIR = 'D:\Caches\uv'
$env:TEMP = 'D:\Temp'
$env:TMP = 'D:\Temp'
uv venv --python 'A:\Tools\Python\cpython-3.12-windows-x86_64-none\python.exe' 'A:\Tools\yelena-tts'
uv pip install --python 'A:\Tools\yelena-tts\Scripts\python.exe' --torch-backend cu128 -r requirements-xtts.lock.txt
```

Verified 2026-10-21: the service loaded on `cuda:0` and synthesized the sample
`data/voice/lisa-reichert-sample.wav` (5.53 seconds, 24000 Hz, mono).
Runtime logs and the started process ID are under `data/voice/` (ignored by Git).
Twenty-five adapter, configuration and motion-navigation tests passed.
The original companion's typed reply and XTTS synthesis were subsequently
verified; the disconnected headset still prevents a microphone conversation test.

## Optional ElevenLabs voice

ElevenLabs Jessica remains configured as a manual alternative. Select
`tts.provider: elevenlabs` to use it; there is no automatic cloud fallback.
That provider sends speech text to ElevenLabs and uses the account's quota.
The external file `D:/Projects/openmontage-birthday/pip-live/env/.env`
supplies `ELEVENLABS_API_KEY` and
`ELEVENLABS_MODEL_ID` (currently `eleven_multilingual_v2`). It is read without
executing it or importing unrelated credentials. Process/saved user variables
can override these values. The explicit `voice_id` overrides the file's male
Charlie voice for Yelena only; the source file and Pip's configuration are
unchanged. No key is copied into this checkout.

The adapter calls the documented
[ElevenLabs speech endpoint](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
and converts returned MP3 to the app's mono PCM playback stream. The checker
uses only [voice metadata](https://elevenlabs.io/docs/api-reference/voices/get);
it does not synthesize speech or verify available speech quota.

The older Companion XTTS server at
`D:\Projects\companion\app\coqui_tts_server.py` was not modified or started.
Yelena now uses the bundled server and the downloaded Lisa Reichert model.

## Connection checks

Check connectivity without starting microphone, screen capture, OSC or speech:

```powershell
& 'A:\Tools\gabriel-venv\Scripts\python.exe' -B scripts/check_local_services.py
```

Lisa Ann authentication and automatic selection of Qwen3-235B are verified.
Parakeet speech recognition loads on Vulkan using the existing local model;
microphone capture cannot be verified while the Quest is disconnected.
`run.bat` uses `YELENA_PYTHON` if set, otherwise an existing repo-local `.venv`,
then the installed `A:\Tools\gabriel-venv\Scripts\python.exe`. The supervisor
uses the same interpreter for the companion. Do not use `setup.bat` to duplicate
the installation. `run.bat` also selects the provisioned Parakeet runtime on A:
and model caches on D:. Headset audio-device checks remain necessary before
a spoken conversation.
