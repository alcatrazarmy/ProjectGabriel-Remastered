"""Check configured AI and voice services without starting the companion."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import Config
from src.service_config import elevenlabs_settings


def check(config_path, timeout):
    # Only read service settings; do not construct audio, OSC or session objects.
    config = Config.__new__(Config)
    config._data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    result = {}
    with httpx.Client(timeout=timeout, trust_env=False) as client:
        try:
            response = client.get(
                config.local_llm_base_url + "/models",
                headers={"Authorization": "Bearer " + config.local_llm_api_key},
            )
            response.raise_for_status()
            models = [item["id"] for item in response.json().get("data", []) if item.get("id")]
            selected = config.local_llm_model
            valid = len(models) == 1 if selected == "auto" else selected in models
            result["llm"] = {"ready": valid, "models": models, "configured_model": selected}
        except ValueError as exc:
            result["llm"] = {"ready": False, "error": str(exc) if "Set " in str(exc) else "Invalid model response"}
        except httpx.HTTPStatusError as exc:
            result["llm"] = {"ready": False, "http_status": exc.response.status_code}
        except httpx.RequestError:
            result["llm"] = {"ready": False, "error": "Server unreachable or request timed out"}

        if config.tts_provider == "elevenlabs":
            try:
                settings = elevenlabs_settings(config)
                response = client.get(
                    "https://api.elevenlabs.io/v1/voices/" + quote(settings["voice_id"], safe=""),
                    headers={"xi-api-key": settings["api_key"]},
                )
                response.raise_for_status()
                voice = response.json()
                result["tts"] = {
                    "ready": voice.get("voice_id") == settings["voice_id"],
                    "provider": "elevenlabs", "voice": voice.get("name"),
                    "gender": voice.get("labels", {}).get("gender"),
                    "speech_generated": False,
                }
            except httpx.HTTPStatusError as exc:
                result["tts"] = {"ready": False, "http_status": exc.response.status_code}
            except (httpx.RequestError, OSError, ValueError):
                result["tts"] = {"ready": False, "error": "Check ElevenLabs connectivity and external voice credentials"}
        elif config.tts_provider == "xtts_service":
            url = config.get("tts", "xtts_service", "base_url", default="http://127.0.0.1:8095").rstrip("/")
            try:
                health = client.get(url + "/health")
                health.raise_for_status()
                voices = client.get(url + "/voices")
                voices.raise_for_status()
                available = voices.json().get("voices", [])
                selected = config.get("tts", "xtts_service", "voice", default="Alexandra Hisakawa")
                result["tts"] = {
                    "ready": health.json().get("status") == "ok" and selected in available,
                    "voice": selected,
                    "voice_available": selected in available,
                }
            except httpx.HTTPStatusError as exc:
                result["tts"] = {"ready": False, "http_status": exc.response.status_code}
            except (httpx.RequestError, ValueError):
                result["tts"] = {"ready": False, "error": "XTTS unreachable or returned an invalid response"}
        else:
            result["tts"] = {"ready": False, "error": "Select tts.provider: elevenlabs or xtts_service"}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.yml")
    parser.add_argument("--timeout", type=float, default=8)
    args = parser.parse_args()
    result = check(args.config, args.timeout)
    print(json.dumps(result, indent=2))
    sys.exit(0 if all(item["ready"] for item in result.values()) else 1)
