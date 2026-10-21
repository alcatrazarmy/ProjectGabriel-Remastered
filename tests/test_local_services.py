import asyncio
import importlib.util
import io
from pathlib import Path

import httpx
import numpy as np
import pytest
import soundfile as sf

from src.config import Config
from src.xtts_service import XTTSServiceProvider


def config(data):
    cfg = Config.__new__(Config)
    cfg._data = data
    return cfg


def test_service_environment_overrides_and_missing_key(monkeypatch):
    cfg = config({"local": {"llm": {
        "base_url": "http://fallback/v1", "base_url_env": "YELENA_TEST_URL",
        "api_key_env": "YELENA_TEST_KEY", "api_key": "must-not-fall-back",
    }}})
    monkeypatch.setenv("YELENA_TEST_URL", "http://node:8080/v1/")
    monkeypatch.setenv("YELENA_TEST_KEY", "test-only")
    assert cfg.local_llm_base_url == "http://node:8080/v1"
    assert cfg.local_llm_api_key == "test-only"
    monkeypatch.setenv("YELENA_TEST_KEY", "")
    with pytest.raises(ValueError, match="Set YELENA_TEST_KEY"):
        _ = cfg.local_llm_api_key


def test_existing_local_settings_still_work():
    cfg = config({"local": {"llm": {"api_key": "local", "base_url": "http://localhost:1234/v1"}}})
    assert cfg.local_llm_api_key == "local"
    assert cfg.local_llm_base_url == "http://localhost:1234/v1"


@pytest.mark.parametrize("model_ids", [["loaded-model"], [], ["one", "two"]])
def test_llama_model_discovery_and_streaming(monkeypatch, model_ids):
    # Load only the HTTP client, bypassing the live-session package initializer.
    path = Path(__file__).resolve().parents[1] / "src/local_live/llm.py"
    spec = importlib.util.spec_from_file_location("llm_service_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    requests = []

    def respond(request):
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer test-only"
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": name} for name in model_ids]})
        assert request.url.path == "/v1/chat/completions"
        assert b'"model":"loaded-model"' in request.content
        return httpx.Response(200, text='data: {"choices":[{"delta":{"content":"Hello Yelena"}}]}\n\ndata: [DONE]\n\n')

    real_client = httpx.AsyncClient
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw))

    async def run():
        client = module.LMStudioClient(config({"local": {"llm": {
            "base_url": "http://node:8080/v1", "model": "auto", "api_key": "test-only",
        }}}))
        if len(model_ids) != 1:
            with pytest.raises(ValueError, match="explicitly"):
                await client.start()
            assert client._client is None
        else:
            events = [event async for event in client.stream_turn([{"role": "user", "content": "Hi"}])]
            assert "".join(e["delta"] for e in events if e["type"] == "text") == "Hello Yelena"
            await client.stop()

    asyncio.run(run())


def audio_bytes(format="WAV"):
    stream = io.BytesIO()
    sf.write(stream, np.full((240, 2), 0.25, dtype="float32"), 24000, format=format)
    return stream.getvalue()


def test_mp3_decode_and_resampling():
    provider = XTTSServiceProvider(config({"audio": {"receive_sample_rate": 48000}}))
    pcm = provider._decode(audio_bytes("MP3"))
    values = np.frombuffer(pcm, dtype="<i2")
    assert len(values) == 480
    assert np.max(np.abs(values)) > 1000


def test_long_text_is_spoken_in_order_without_service_truncation():
    async def run():
        provider = XTTSServiceProvider(config({}))
        provider.start()
        await provider._client.aclose()
        sent = []

        def respond(request):
            import json
            body = json.loads(request.content)
            sent.append(body["text"])
            assert body["voice"] == "Alexandra Hisakawa"
            assert len(body["text"]) <= 500
            return httpx.Response(200, content=audio_bytes())

        provider._client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        text = "word " * 230 + "finished."
        for offset in range(0, len(text), 17):
            provider.feed_text(text[offset:offset + 17])
        provider.turn_complete()
        chunks = []
        for _ in range(30):
            chunk = await provider.get_audio()
            if chunk:
                chunks.append(chunk)
            if len(sent) == 3 and len(chunks) == 3:
                break
        provider.stop()
        await asyncio.sleep(0)
        assert " ".join(sent).split() == text.split()
        assert len(chunks) == 3

    asyncio.run(run())


def test_interruption_cancels_old_speech_and_allows_next_turn():
    async def run():
        provider = XTTSServiceProvider(config({}))
        provider.start()
        await provider._client.aclose()
        started = asyncio.Event()
        cancelled = asyncio.Event()
        count = 0

        async def respond(request):
            nonlocal count
            count += 1
            if count == 1:
                started.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    cancelled.set()
                    raise
            return httpx.Response(200, content=audio_bytes())

        provider._client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
        provider.feed_text("Old speech.")
        assert await provider.get_audio() is None
        assert started.is_set()
        provider.interrupt()
        provider.feed_text("New speech.")
        async with asyncio.timeout(3):
            chunk = None
            while chunk is None:
                chunk = await provider.get_audio()
        assert cancelled.is_set()
        assert chunk
        assert provider._audio_queue.empty()
        provider.stop()
        await asyncio.sleep(0)

    asyncio.run(run())
