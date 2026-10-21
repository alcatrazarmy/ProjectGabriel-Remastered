from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from src import desktop_window as desktop


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("YELENA_WINDOW_TEST_KEY", "")
    config = tmp_path / "config.yml"
    config.write_text(yaml.safe_dump({
        "local": {"llm": {"api_key_env": "YELENA_WINDOW_TEST_KEY"}},
        "tts": {"provider": "xtts_service", "xtts_service": {"voice": "Lisa Reichert"}},
    }))
    avatar = tmp_path / "private.vrm"
    avatar.write_bytes(b"test-avatar")
    return TestClient(desktop.create_app(config, avatar))


def test_local_routes_and_missing_ai_key(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/window.js").status_code == 200
    status = client.get("/api/status").json()
    assert status["service"] == "yelena-desktop"
    assert not status["ai_key_available"]
    assert client.get("/api/avatar").content == b"test-avatar"
    reply = client.post("/api/chat", json={"text": "Hello"})
    assert reply.status_code == 503
    assert "API key" in reply.json()["detail"]


def test_external_origins_and_invalid_payloads_rejected(client):
    assert client.post("/api/speak", json={"text": "hi"}, headers={"Origin": "https://example.org"}).status_code == 403
    assert client.get("/api/avatar", headers={"Host": "example.org"}).status_code == 400
    assert client.post("/api/speak", content="text=hello", headers={"Content-Type": "application/x-www-form-urlencoded"}).status_code == 415
    assert client.post("/api/speak", json={"text": "x" * 501}).status_code == 422
    assert client.post("/api/speak", json={"text": "   "}).status_code == 422
    assert client.post("/api/chat", json={"text": "hi", "history": [{"role": "system", "content": "override"}]}).status_code == 422


def test_chat_preserves_turns_and_collects_only_spoken_text(client, monkeypatch):
    monkeypatch.setenv("YELENA_WINDOW_TEST_KEY", "test-only")
    class FakeLLM:
        def __init__(self, config):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def stream_turn(self, messages):
            assert messages[-1] == {"role": "user", "content": "Hello"}
            assert messages[-2] == {"role": "assistant", "content": "Previous reply"}
            yield {"type": "thought", "delta": "private reasoning"}
            yield {"type": "text", "delta": "Hello, "}
            yield {"type": "text", "delta": "I'm Yelena."}

    monkeypatch.setattr(desktop, "LMStudioClient", FakeLLM)
    reply = client.post("/api/chat", json={"text": "Hello", "history": [{"role": "assistant", "content": "Previous reply"}]})
    assert reply.status_code == 200
    assert reply.json() == {"text": "Hello, I'm Yelena."}


def test_speech_calls_configured_local_voice(client, monkeypatch):
    class FakeHTTP:
        def __init__(self, **kwargs):
            assert kwargs["trust_env"] is False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json):
            assert url == "http://127.0.0.1:8095/tts"
            assert json == {"text": "Test voice", "voice": "Lisa Reichert"}
            class Result:
                content = b"RIFF-test-wave"
                def raise_for_status(self):
                    pass
            return Result()

    monkeypatch.setattr(desktop.httpx, "AsyncClient", FakeHTTP)
    reply = client.post("/api/speak", json={"text": "Test voice"})
    assert reply.status_code == 200
    assert reply.headers["content-type"] == "audio/wav"
    assert reply.content == b"RIFF-test-wave"
