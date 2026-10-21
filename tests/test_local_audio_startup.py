import asyncio
from types import SimpleNamespace
from src.local_live.session import LocalLiveSession


def test_text_session_survives_disconnected_headset(monkeypatch):
    import src.local_live.session as module
    monkeypatch.setattr(module, '_broadcast_console', lambda *args: None)
    async def run():
        s=LocalLiveSession.__new__(LocalLiveSession)
        stopped=[]
        async def start(): pass
        async def stop(): stopped.append('llm')
        s._llm=SimpleNamespace(start=start,stop=stop)
        s._stt=SimpleNamespace(start=lambda:None,ready=True,stop=lambda:stopped.append('stt'))
        s._idle_chatbox=SimpleNamespace(stop=lambda:None)
        s.config=SimpleNamespace(local_llm_model='test',local_stt_model='test')
        s.tool_handler=SimpleNamespace()
        stream=SimpleNamespace(close=lambda:stopped.append('stream'))
        def missing_mic(): raise OSError('Headset disconnected')
        def speaker():
            if s.audio.output_device==18: raise OSError('Headset disconnected')
            return stream
        s.audio=SimpleNamespace(open_input_stream=missing_mic,open_output_stream=speaker,output_device=18,pya=SimpleNamespace(get_default_output_device_info=lambda:{'index':1,'name':'PC speakers'}))
        async def idle(*args): await asyncio.Event().wait()
        async def turn():
            assert s.is_connected
            assert not s.audio_input_ready
            assert s.audio_output_ready
            assert s.audio.output_device==1
        s._turn_pump_loop=turn
        for name in ('_stt_partial_loop','_barge_in_loop','_tts_audio_loop','_play_audio_loop','_idle_check_loop','_now_playing_loop','_reconnect_monitor_loop'):
            setattr(s,name,idle)
        await s.run()
        assert not s.is_connected
        assert set(stopped)=={'stream','stt','llm'}
    asyncio.run(run())
