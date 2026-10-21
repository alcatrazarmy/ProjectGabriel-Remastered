from src.plugins import Plugin
from src.xtts_service import XTTSServiceProvider


class XTTSServicePlugin(Plugin):
    def setup(self, ctx):
        ctx.register_tts("xtts_service", XTTSServiceProvider)
