import asyncio
import importlib.util
import io
import json
from pathlib import Path

import httpx
import numpy as np
import pytest
import soundfile as sf

from src.config import Config
from src.elevenlabs_service import ElevenLabsProvider
from src.service_config import env_file_values, elevenlabs_settings


def config(data):
    cfg = Config.__new__(Config)
    cfg._data = data
    return cfg


@pytest.fixture
def voice_config(tmp_path, monkeypatch):
    for name in ("ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL_ID"):
        monkeypatch.setenv(name, "")
    source = tmp_path / ".env"
    source.write_text(
        'ANTHROPIC_API_KEY=unrelated-secret\n'
        'export ELEVENLABS_API_KEY="test-key#quoted" # comment\n'
        'ELEVENLABS_VOICE_ID=original-voice\n'
        'ELEVENLABS_MODEL_ID=eleven_multilingual_v2\n', encoding="utf-8",
    )
    return config({"tts": {"provider": "elevenlabs", "elevenlabs": {
        "env_file": str(source), "voice_id": "female-voice",
    }}})


def test_reads_only_allowed_credentials_and_overrides_voice(voice_config, monkeypatch):
    source = Path(voice_config.get("tts", "elevenlabs", "env_file"))
    original = source.read_bytes()
    saved = env_file_values(source, {"ELEVENLABS_API_KEY"})
    assert saved == {"ELEVENLABS_API_KEY": "test-key#quoted"}
    settings = elevenlabs_settings(voice_config)
    assert settings == {"api_key": "test-key#quoted", "voice_id": "female-voice", "model": "eleven_multilingual_v2"}
    monkeypatch.setenv("ELEVENLABS_API_KEY", "environment-key")
    assert elevenlabs_settings(voice_config)["api_key"] == "environment-key"
    assert source.read_bytes() == original


def test_bad_credentials_do_not_leak_values(tmp_path):
    source = tmp_path / ".env"
    source.write_text('ELEVENLABS_API_KEY="do-not-log-this', encoding="utf-8")
    with pytest.raises(ValueError) as error:
        env_file_values(source, {"ELEVENLABS_API_KEY"})
    assert "do-not-log-this" not in str(error.value)


def test_missing_key_fails_before_network(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "")
    with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
        ElevenLabsProvider(config({"tts": {"elevenlabs": {"voice_id": "female-voice"}}}))


def test_elevenlabs_request_and_pcm_playback(voice_config):
    async def run():
        provider = ElevenLabsProvider(voice_config)
        provider.start()
        await provider._client.aclose()

        def respond(request):
            assert request.url.host == "api.elevenlabs.io"
            assert request.url.path == "/v1/text-to-speech/female-voice"
            assert request.url.params["output_format"] == "mp3_44100_128"
            assert request.headers["xi-api-key"] == "test-key#quoted"
            assert json.loads(request.content) == {"text": "Hello from Yelena.", "model_id": "eleven_multilingual_v2"}
            stream = io.BytesIO()
            sf.write(stream, np.full(441, 0.25, dtype="float32"), 44100, format="MP3")
            return httpx.Response(200, content=stream.getvalue())

        provider._client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        provider.feed_text("Hello from ")
        provider.feed_text("Yelena.")
        provider.turn_complete()
        async with asyncio.timeout(3):
            pcm = None
            while pcm is None:
                pcm = await provider.get_audio()
        assert pcm
        assert len(np.frombuffer(pcm, dtype="<i2")) == 240
        provider.stop()
        await asyncio.sleep(0)

    asyncio.run(run())


def test_checker_only_reads_voice_metadata(voice_config, monkeypatch, tmp_path):
    import yaml

    path = Path(__file__).resolve().parents[1] / "scripts/check_local_services.py"
    spec = importlib.util.spec_from_file_location("voice_checker_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("YELENA_TEST_MISSING_KEY", "")
    voice_config._data["local"] = {"llm": {"api_key_env": "YELENA_TEST_MISSING_KEY"}}
    cfg_path = tmp_path / "config.yml"
    cfg_path.write_text(yaml.safe_dump(voice_config._data), encoding="utf-8")
    requests = []

    def respond(request):
        requests.append(request)
        assert request.method == "GET"
        assert request.url.path == "/v1/voices/female-voice"
        return httpx.Response(200, json={"voice_id": "female-voice", "name": "Jessica", "labels": {"gender": "female"}})

    real_client = httpx.Client
    monkeypatch.setattr(module.httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw))
    result = module.check(cfg_path, 1)
    assert not result["llm"]["ready"]
    assert result["tts"]["ready"]
    assert result["tts"]["gender"] == "female"
    assert result["tts"]["speech_generated"] is False
    assert len(requests) == 1
    assert "test-key" not in json.dumps(result)
