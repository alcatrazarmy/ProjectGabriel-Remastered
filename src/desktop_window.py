"""Loopback-only talking-avatar window, independent of VRChat/device startup."""

import asyncio
import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.config import Config
from src.local_live.llm import LMStudioClient

ROOT = Path(__file__).resolve().parents[1]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    history: list[Message] = Field(default_factory=list, max_length=20)


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


def create_app(config_path=ROOT / "config.yml", avatar_path=None):
    # Read only settings. Do not import main.py or construct capture/OSC objects.
    config = Config.__new__(Config)
    config._data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if avatar_path is None:
        manifest = json.loads((ROOT / "config/avatar-local.json").read_text(encoding="utf-8"))
        if manifest.get("enabled") is False or not manifest.get("vrm_path"):
            raise RuntimeError("Previous avatar removed. Configure the selected MetaHuman assets before launching a replacement.")
        avatar_path = manifest["vrm_path"]
    avatar_path = Path(avatar_path)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def local_requests(request: Request, call_next):
        origin = request.headers.get("origin")
        expected = f"{request.url.scheme}://{request.headers.get('host')}"
        if origin and origin != expected:
            return JSONResponse({"detail": "Use the local Yelena window."}, status_code=403)
        if request.method == "POST" and request.headers.get("content-type", "").split(";")[0] != "application/json":
            return JSONResponse({"detail": "JSON required."}, status_code=415)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' blob:; media-src 'self' blob:; connect-src 'self' blob:; style-src 'self'; script-src 'self'; frame-ancestors 'none'"
        return response

    @app.get("/")
    async def index():
        return FileResponse(ROOT / "desktop/index.html")

    @app.get("/api/status")
    async def status():
        try:
            key_available = bool(config.local_llm_api_key)
        except ValueError:
            key_available = False
        return {
            "service": "yelena-desktop", "avatar_available": avatar_path.is_file(),
            "ai_key_available": key_available, "microphone_transcription": False,
            "voice": config.get("tts", "xtts_service", "voice", default="Lisa Reichert"),
        }

    @app.get("/api/avatar")
    async def avatar():
        if not avatar_path.is_file():
            raise HTTPException(404, "Configured avatar is missing.")
        return FileResponse(avatar_path, media_type="model/gltf-binary")

    @app.get("/api/companion")
    async def companion(after: str = ""):
        try:
            async with httpx.AsyncClient(timeout=3, trust_env=False) as client:
                result = await client.get("http://127.0.0.1:8766/api/avatar-state", params={"after": after})
                result.raise_for_status()
                return result.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, "Original app is unavailable. Start run.bat.") from None

    @app.post("/api/companion/chat")
    async def companion_chat(body: SpeechRequest):
        if not body.text.strip():
            raise HTTPException(422, "Enter a message.")
        try:
            async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
                result = await client.post("http://127.0.0.1:8766/api/send-text", json={"text": body.text})
                result.raise_for_status()
                return result.json()
        except httpx.HTTPError:
            raise HTTPException(503, "Original app could not accept the message. Check port 8766.") from None

    @app.get("/api/sample")
    async def sample():
        path = ROOT / "data/voice/lisa-reichert-sample.wav"
        if not path.is_file():
            raise HTTPException(404, "Voice sample is missing.")
        return FileResponse(path, media_type="audio/wav")

    @app.post("/api/chat")
    async def chat(body: ChatRequest):
        if not body.text.strip():
            raise HTTPException(422, "Enter a message.")
        try:
            _ = config.local_llm_api_key
            client = LMStudioClient(config)
        except ValueError:
            raise HTTPException(503, "Lisa Ann's saved API key is not available. Run set-lisa-ann-key.ps1, then retry.") from None
        messages = [{"role": "system", "content": (
            "You are Yelena Xiomora, a female AI companion. Speak naturally and concisely. "
            "You are in a desktop avatar window. You cannot see the user or control their computer."
        )}] + [item.model_dump() for item in body.history]
        messages.append({"role": "user", "content": body.text})
        parts = []
        try:
            async with asyncio.timeout(120), client:
                async for event in client.stream_turn(messages):
                    if event["type"] == "text":
                        parts.append(event["delta"])
                    elif event["type"] == "error":
                        raise HTTPException(502, "Lisa Ann could not complete the reply. Check AI connectivity and authentication.")
        except (httpx.HTTPError, ValueError, TimeoutError):
            raise HTTPException(502, "Lisa Ann is unavailable. Check AI connectivity and authentication.") from None
        text = "".join(parts).strip()
        if not text:
            raise HTTPException(502, "Lisa Ann returned no spoken reply.")
        return {"text": text}

    @app.post("/api/speak")
    async def speak(body: SpeechRequest):
        if not body.text.strip():
            raise HTTPException(422, "Enter text to speak.")
        if config.tts_provider != "xtts_service":
            raise HTTPException(409, "This window requires the local XTTS voice provider.")
        url = config.get("tts", "xtts_service", "base_url", default="http://127.0.0.1:8095").rstrip("/")
        if urlsplit(url).hostname not in {"localhost", "127.0.0.1"}:
            raise HTTPException(409, "The desktop voice service must be on this PC.")
        try:
            async with httpx.AsyncClient(timeout=180, trust_env=False) as client:
                result = await client.post(url + "/tts", json={
                    "text": body.text,
                    "voice": config.get("tts", "xtts_service", "voice", default="Lisa Reichert"),
                })
                result.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(502, "Local voice unavailable. Start Start-Yelena-Voice.ps1 and retry.") from None
        if not result.content.startswith(b"RIFF"):
            raise HTTPException(502, "The local voice service did not return WAV audio.")
        return Response(result.content, media_type="audio/wav")

    app.mount("/static", StaticFiles(directory=ROOT / "desktop"), name="static")
    return app
