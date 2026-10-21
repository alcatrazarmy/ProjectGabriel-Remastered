"""Audio adapter for the existing Companion XTTS /tts service."""

import asyncio
import io
import logging
import re

import httpx
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class XTTSServiceProvider:
    def __init__(self, config):
        self._url = config.get("tts", "xtts_service", "base_url", default="http://127.0.0.1:8095").rstrip("/")
        self._voice = config.get("tts", "xtts_service", "voice", default="Alexandra Hisakawa")
        self._sample_rate = int(config.get("audio", "receive_sample_rate", default=24000))
        self._timeout = float(config.get("tts", "xtts_service", "timeout", default=180))
        self._running = False
        self._interrupted = False
        self._pending = ""
        self._generation = 0
        self._sentences = asyncio.Queue()
        self._audio_queue = asyncio.Queue()
        self._worker = None
        self._client = None

    def start(self):
        if not self._running:
            self._client = httpx.AsyncClient(timeout=self._timeout, trust_env=False)
            self._running = True

    def stop(self):
        self.interrupt()
        self._running = False
        if self._client is not None:
            client, self._client = self._client, None
            asyncio.get_running_loop().create_task(client.aclose())

    def feed_text(self, text):
        if not self._running or not text:
            return
        self._interrupted = False
        self._pending += text
        self._split_pending()

    def _split_pending(self, flush=False):
        # The existing service truncates requests to 500 characters. Split here
        # so a long reply is spoken completely, in order, rather than cut off.
        while self._pending:
            match = re.search(r"[.!?](?:\s+|$)", self._pending)
            if match and match.end() <= 500:
                end = match.end()
            elif len(self._pending) > 500:
                end = self._pending.rfind(" ", 0, 501)
                if end <= 0:
                    end = 500
            elif flush:
                end = len(self._pending)
            else:
                break
            sentence, self._pending = self._pending[:end].strip(), self._pending[end:]
            if sentence:
                self._sentences.put_nowait((self._generation, sentence))

    def turn_complete(self):
        if self._running and not self._interrupted:
            self._split_pending(flush=True)

    def interrupt(self):
        self._interrupted = True
        self._generation += 1
        self._pending = ""
        if self._worker:
            self._worker.cancel()
            self._worker = None
        for queue in (self._sentences, self._audio_queue):
            while not queue.empty():
                queue.get_nowait()

    async def get_audio(self):
        if not self._running:
            return None
        if self._worker is None:
            self._worker = asyncio.create_task(self._synthesize())
        try:
            return await asyncio.wait_for(self._audio_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

    def _decode(self, content):
        # XTTS returns MP3; the app consumes mono signed 16-bit PCM.
        audio, sample_rate = sf.read(io.BytesIO(content), dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        if not len(audio):
            return b""
        if sample_rate != self._sample_rate:
            count = max(1, round(len(audio) * self._sample_rate / sample_rate))
            audio = np.interp(np.linspace(0, len(audio) - 1, count), np.arange(len(audio)), audio)
        return (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()

    async def _synthesize(self):
        while self._running:
            generation, text = await self._sentences.get()
            try:
                content = await self._request_audio(text)
                pcm = await asyncio.to_thread(self._decode, content)
                if generation == self._generation and not self._interrupted:
                    # Match the small PCM chunks used by the existing providers.
                    size = max(2, self._sample_rate // 50 * 2)
                    for offset in range(0, len(pcm), size):
                        self._audio_queue.put_nowait(pcm[offset:offset + size])
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Speech synthesis failed (%s); check the configured provider", type(exc).__name__)

    async def _request_audio(self, text):
        response = await self._client.post(
            self._url + "/tts", json={"text": text, "voice": self._voice},
        )
        response.raise_for_status()
        return response.content
