from src.elevenlabs_service import ElevenLabsProvider
from src.plugins import Plugin


class ElevenLabsPlugin(Plugin):
    def setup(self, ctx):
        ctx.register_tts("elevenlabs", ElevenLabsProvider)
