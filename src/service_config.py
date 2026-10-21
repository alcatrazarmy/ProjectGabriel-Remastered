"""Read service credentials without copying them into project configuration."""

import os
import shlex
from pathlib import Path


def environment_value(name: str) -> str:
    if name in os.environ:
        return os.environ[name]
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value)
        except OSError:
            pass
    return ""


def env_file_values(path, names):
    """Read only named values from a dotenv file, without executing its contents."""
    values = {}
    if not path:
        return values
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        name, separator, value = line.partition("=")
        name = name.strip().removeprefix("export ").strip()
        if not separator or name not in names:
            continue
        try:
            parts = shlex.split(value, comments=True, posix=True)
        except ValueError:
            raise ValueError(f"Invalid dotenv value for {name}") from None
        if len(parts) > 1:
            raise ValueError(f"Quote the dotenv value for {name}")
        values[name] = parts[0] if parts else ""
    return values


def elevenlabs_settings(config):
    names = ("ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL_ID")
    path = config.get("tts", "elevenlabs", "env_file", default="")
    saved = env_file_values(path, names)
    values = {name: environment_value(name) or saved.get(name, "") for name in names}
    key = values["ELEVENLABS_API_KEY"]
    voice = config.get("tts", "elevenlabs", "voice_id", default="") or values["ELEVENLABS_VOICE_ID"]
    model = config.get("tts", "elevenlabs", "model", default="") or values["ELEVENLABS_MODEL_ID"] or "eleven_multilingual_v2"
    if not key or not voice:
        raise ValueError("Set ELEVENLABS_API_KEY and an ElevenLabs voice ID")
    return {"api_key": key, "voice_id": voice, "model": model}
