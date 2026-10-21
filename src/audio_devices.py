"""Resolve configured audio names without relying on unstable device numbers."""


def resolve_named_device(pya, name, *, input_device):
    channel_key = "maxInputChannels" if input_device else "maxOutputChannels"
    matches = []
    for index in range(pya.get_device_count()):
        info = pya.get_device_info_by_index(index)
        if info.get(channel_key, 0) and name.casefold() in info["name"].casefold():
            # MME supports the mono 16/24 kHz streams through the Windows mixer.
            # WASAPI endpoints may require stereo/native rates instead.
            host = pya.get_host_api_info_by_index(info["hostApi"]).get("name", "")
            rank = 0 if host == "MME" else 1 if "DirectSound" in host else 2
            matches.append((rank, index))
    return min(matches)[1] if matches else None
