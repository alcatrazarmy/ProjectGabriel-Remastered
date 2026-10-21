"""Serve a downloaded XTTS checkpoint through the companion's voice API."""

import io
import threading
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field


VOICE_NAME = "Lisa Reichert"


def validate_model_directory(directory):
    directory = Path(directory).resolve()
    for name in ("config.json", "model.pth", "vocab.json", "speakers_xtts.pth", "reference.wav"):
        path = directory / name
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Missing XTTS asset: {path}")
        with path.open("rb") as stream:
            if stream.read(80).startswith(b"version https://git-lfs.github.com/spec/v1"):
                raise ValueError(f"Download the actual model file, not its Git LFS pointer: {name}")
    return directory


class LocalXTTS:
    def __init__(self, model_dir, device="auto"):
        import torch
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts

        directory = validate_model_directory(model_dir)
        self.device = ("cuda:0" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        self._lock = threading.Lock()
        torch.set_num_threads(6)
        config = XttsConfig()
        config.load_json(str(directory / "config.json"))
        self._model = Xtts.init_from_config(config)
        self._model.load_checkpoint(config, checkpoint_dir=str(directory), eval=True, use_deepspeed=False)
        self._model.to(self.device)
        with torch.inference_mode():
            self._conditioning, self._speaker = self._model.get_conditioning_latents(
                audio_path=[str(directory / "reference.wav")],
            )
        self.sample_rate = int(config.audio.get("output_sample_rate", 24000))

    def synthesize(self, text):
        import torch

        with self._lock, torch.inference_mode():
            result = self._model.inference(
                text, "en", self._conditioning, self._speaker,
                enable_text_splitting=True,
            )
        output = io.BytesIO()
        sf.write(output, result["wav"], self.sample_rate, format="WAV", subtype="PCM_16")
        return output.getvalue()


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    voice: str = VOICE_NAME


def create_app(engine):
    app = FastAPI(title="Yelena local XTTS", docs_url=None, redoc_url=None)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "yelena-xtts", "device": engine.device}

    @app.get("/voices")
    def voices():
        return {"voices": [VOICE_NAME]}

    @app.post("/tts")
    def speak(body: SpeechRequest):
        if body.voice != VOICE_NAME:
            raise HTTPException(400, "This service provides only the Lisa Reichert voice")
        text = body.text.strip()
        if not text:
            raise HTTPException(400, "Speech text cannot be blank")
        return Response(engine.synthesize(text), media_type="audio/wav")

    return app
