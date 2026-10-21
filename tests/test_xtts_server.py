import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from src.xtts_server import VOICE_NAME, create_app, validate_model_directory


class FakeVoice:
    device = "cpu"

    def __init__(self):
        self.requests = []

    def synthesize(self, text):
        self.requests.append(text)
        stream = io.BytesIO()
        sf.write(stream, np.zeros(240, dtype="float32"), 24000, format="WAV")
        return stream.getvalue()


def test_voice_service_health_and_audio_contract():
    engine = FakeVoice()
    with TestClient(create_app(engine)) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/voices").json() == {"voices": [VOICE_NAME]}
        response = client.post("/tts", json={"text": " Hello Yelena. ", "voice": VOICE_NAME})
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert sf.info(io.BytesIO(response.content)).samplerate == 24000
        assert engine.requests == ["Hello Yelena."]


@pytest.mark.parametrize("body,status", [
    ({"text": "  "}, 400),
    ({"text": ""}, 422),
    ({"text": "a" * 501}, 422),
    ({"text": "hello", "voice": "another voice"}, 400),
])
def test_rejects_invalid_speech_without_running_model(body, status):
    engine = FakeVoice()
    with TestClient(create_app(engine)) as client:
        assert client.post("/tts", json=body).status_code == status
    assert not engine.requests


def test_incomplete_downloads_are_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_model_directory(tmp_path)
    (tmp_path / "config.json").write_text("{}")
    (tmp_path / "model.pth").write_text("version https://git-lfs.github.com/spec/v1\n")
    with pytest.raises(ValueError, match="Git LFS pointer"):
        validate_model_directory(tmp_path)
