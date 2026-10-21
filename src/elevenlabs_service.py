"""ElevenLabs speech using the existing queued PCM playback adapter."""

from urllib.parse import quote

from src.service_config import elevenlabs_settings
from src.xtts_service import XTTSServiceProvider


class ElevenLabsProvider(XTTSServiceProvider):
    def __init__(self, config):
        super().__init__(config)
        settings = elevenlabs_settings(config)
        self._api_key = settings["api_key"]
        self._voice = settings["voice_id"]
        self._model = settings["model"]
        self._timeout = float(config.get("tts", "elevenlabs", "timeout", default=60))

    async def _request_audio(self, text):
        response = await self._client.post(
            "https://api.elevenlabs.io/v1/text-to-speech/" + quote(self._voice, safe=""),
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": self._api_key},
            json={"text": text, "model_id": self._model},
        )
        response.raise_for_status()
        return response.content
