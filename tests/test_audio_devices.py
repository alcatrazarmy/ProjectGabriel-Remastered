from types import SimpleNamespace

from src.audio_devices import resolve_named_device


def audio(devices):
    return SimpleNamespace(
        get_device_count=lambda: len(devices),
        get_device_info_by_index=lambda i: devices[i],
        get_host_api_info_by_index=lambda i: {"name": ["WASAPI", "MME"][i]},
    )


def device(name, inputs=0, outputs=0, host=1):
    return {"name": name, "maxInputChannels": inputs, "maxOutputChannels": outputs, "hostApi": host}


def test_steam_audio_survives_renumbering():
    mic = device("Microphone (Steam Streaming Mic", inputs=8)
    monitor = device("LG monitor", outputs=2)
    assert resolve_named_device(audio([monitor, mic]), "Microphone (Steam Streaming", input_device=True) == 1
    assert resolve_named_device(audio([mic, monitor]), "Microphone (Steam Streaming", input_device=True) == 0


def test_prefers_mixer_and_filters_direction():
    devices = [device("Steam", outputs=2), device("Steam", inputs=2, host=0), device("Steam", inputs=8)]
    assert resolve_named_device(audio(devices), "Steam", input_device=True) == 2


def test_missing_headset_does_not_select_monitor():
    assert resolve_named_device(audio([device("LG monitor", outputs=2)]), "Steam", input_device=False) is None
