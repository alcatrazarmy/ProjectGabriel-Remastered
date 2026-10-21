# Lisa Ann AI and Yelena's voice

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
    api_key_env: LISA_ANN_API_KEY
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
variables. An explicitly selected but missing API-key variable fails with a
clear error instead of sending a placeholder key.

Lisa Ann's address was found in `D:\SystemSetup\scripts\set-lisa-ann-key.ps1`.
That existing script prompts privately for the key, tests it, and saves
`LISA_ANN_API_KEY` and `LISA_ANN_BASE_URL`. Run it in your own terminal if the
key has not been saved; do not paste keys into chat or config examples:

```powershell
& 'D:\SystemSetup\scripts\set-lisa-ann-key.ps1'
```

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
The full companion conversation loop has not yet been run.

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

Lisa Ann responds but requires authentication (HTTP 401); `LISA_ANN_API_KEY`
was absent from process/user/machine environment. Live LLM model selection
and end-to-end conversation remain unverified. Local speech is verified.
The current `run.bat` also expects a repo-local `.venv`; the installed Python
environment is on `A:`. Do not use `setup.bat` to duplicate the installation.
