import asyncio
import time
from types import SimpleNamespace

import httpx
from fastapi.testclient import TestClient

from src.web.routes import core
from src import desktop_window


def test_avatar_state_uses_fresh_audio_and_excludes_reasoning(monkeypatch):
    session = SimpleNamespace(is_connected=True, audio_input_ready=False,
                              _avatar_audio_at=time.monotonic(), _avatar_audio_level=.6)
    monkeypatch.setitem(core.shared_state, "session", session)
    monkeypatch.setattr(core, "console_logs", [
        {"type": "thinking", "timestamp": "2", "content": "private"},
        {"type": "response", "timestamp": "3", "content": "Hello"},
        {"type": "transcription", "timestamp": "1", "content": "old"},
    ])
    result = asyncio.run(core.avatar_state(after="1"))
    assert result["connected"] and result["mouth"] == .6
    assert result["events"] == [{"type": "response", "timestamp": "3", "content": "Hello"}]
    session._avatar_audio_at -= 1
    assert asyncio.run(core.avatar_state())["mouth"] == 0


def test_window_forwards_to_original_session(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yml"
    cfg.write_text("tts: {provider: xtts_service}\n")
    requests = []
    def handle(request):
        requests.append(request)
        assert request.url.host == "127.0.0.1" and request.url.port == 8766
        if request.method == "GET":
            assert request.url.params["after"] == "3"
            return httpx.Response(200, json={"connected": True, "mouth": .7, "events": []})
        assert request.url.path == "/api/send-text"
        assert request.content == b'{"text":"Hello"}'
        return httpx.Response(200, json={"message": "Text sent"})
    original = httpx.AsyncClient
    monkeypatch.setattr(desktop_window.httpx, "AsyncClient",
                        lambda **kw: original(transport=httpx.MockTransport(handle), **kw))
    with TestClient(desktop_window.create_app(cfg, tmp_path / "avatar.vrm")) as client:
        assert client.get("/api/companion?after=3").json()["mouth"] == .7
        assert client.post("/api/companion/chat", json={"text": "Hello"}).json() == {"message": "Text sent"}
    assert len(requests) == 2
