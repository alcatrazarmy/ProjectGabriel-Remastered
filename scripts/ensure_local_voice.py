"""Reuse or start the configured local Lisa voice before the original app."""

import argparse
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]


def voice_ready(client, url, voice):
    try:
        health = client.get(url + "/health")
    except httpx.ConnectError:
        return False
    health.raise_for_status()
    if health.json().get("service") != "yelena-xtts":
        raise RuntimeError("Configured voice URL belongs to a different service.")
    voices = client.get(url + "/voices")
    voices.raise_for_status()
    if voice not in voices.json().get("voices", []):
        raise RuntimeError("Configured voice is not available from the voice service.")
    return health.json().get("status") == "ok"


def ensure_voice(config_path, wait_seconds=180):
    config_path = Path(config_path).resolve()
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    tts = cfg.get("tts", {})
    if tts.get("provider") != "xtts_service":
        return "Selected voice provider does not require the local XTTS server."
    settings = tts.get("xtts_service", {})
    url = settings.get("base_url", "http://127.0.0.1:8095").rstrip("/")
    voice = settings.get("voice", "Lisa Reichert")
    with httpx.Client(timeout=3, trust_env=False) as client:
        if voice_ready(client, url, voice):
            return "Lisa voice is ready; reusing the running service."
        endpoint = urlsplit(url)
        if (endpoint.scheme != "http" or endpoint.hostname not in ("127.0.0.1", "localhost")
                or endpoint.path or endpoint.query or endpoint.fragment
                or endpoint.username or endpoint.password):
            raise RuntimeError("Configured voice service is unavailable; only a local HTTP service can be started automatically.")
        python = Path(os.environ.get("YELENA_TTS_PYTHON", "A:/Tools/yelena-tts/Scripts/python.exe"))
        if not python.is_file():
            raise RuntimeError("Lisa voice Python is missing. Set YELENA_TTS_PYTHON to its installed python.exe.")
        log_dir = ROOT / "data" / "voice"
        log_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", TEMP="D:/Temp", TMP="D:/Temp")
        print("Starting Lisa's local voice; waiting for the model to load...", flush=True)
        with (log_dir / "autostart.log").open("ab") as log:
            process = subprocess.Popen(
                [str(python), "-B", "-u", str(ROOT / "scripts" / "serve_local_voice.py"),
                 "--config", str(config_path), "--port", str(endpoint.port or 80)],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        (log_dir / "autostart.pid").write_text(str(process.pid), encoding="ascii")
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Lisa voice startup failed. See data/voice/autostart.log.")
            if voice_ready(client, url, voice):
                return "Lisa voice is ready."
            time.sleep(1)
        raise RuntimeError("Lisa voice is still loading. See data/voice/autostart.log before retrying.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yml")
    args = parser.parse_args()
    try:
        print(ensure_voice(args.config))
    except (OSError, ValueError, RuntimeError, httpx.HTTPError) as exc:
        # HTTP exception strings may include a configured URL; keep credentials out of logs.
        print(str(exc) if isinstance(exc, RuntimeError) else "Voice startup check failed. Check config.yml and data/voice/autostart.log.")
        raise SystemExit(1)
