# Yelena desktop window and Quest 3

Current headset connection is **Steam Link**, confirmed by the user. The
original app now opens Steam Streaming microphone and speaker endpoints;
both readiness flags are true. Stable name matching prevents stale Virtual
Desktop device numbers from selecting a monitor after device enumeration
changes. Use SteamVR desktop view for the avatar window. User confirmation
of heard speech and microphone transcription is still needed. The older
Virtual Desktop/disconnected-headset observations below are historical.

Latest verified integration: the window on port 8768 now sends messages to the
original app on port 8766 and reads its actual speech playback level. Skeletal
idle movement, head movement, blinking, a wave, and speech-driven mouth opening
are implemented for the existing private VRM. A browser test observed all of
idle bone movement, blinking, and mouth opening during a real original-app
reply; screenshots and the report are in `data/desktop-window/motion-*`.
This supersedes the static/bind-pose prototype status below. Headset testing
still requires the Quest to be connected.

Current target: the original app at `http://127.0.0.1:8766`. Lisa Ann
authentication, a Qwen3-235B reply, and local Lisa XTTS synthesis are verified.
The user confirmed the Quest is disconnected. The original app accepts typed
messages and opens the PC's default speaker when headset audio cannot open.
Headset microphone capture and listening remain untested. The desktop avatar
now connects to this same app session.

Updated 2026-10-21: `Start-Yelena-Window.ps1` now opens a standalone localhost
window using the existing private avatar. The window supports local XTTS
speech, an audio-output selector, amplitude-driven mouth opening and typed
AI chat. A muted browser check verified rendering, sample playback, mouth
movement and stopping playback. Twenty-three service/configuration tests
passed. Headset listening and microphone transcription remain unverified;
the window explicitly labels microphone conversation as not connected.

The user wants Yelena in her own window, viewed through a
Quest 3. The first target is a desktop window streamed into the headset.
An immersive stereoscopic scene is a separate implementation.

## Headset connection

VirtualDesktop.Streamer and VirtualDesktop.Service are already running on
this PC. Windows reports the Virtual Desktop Audio driver with status OK.
The initial name-filtered PyAudio check missed the virtual endpoints. Full
enumeration outside the sandbox subsequently found `Microphone (VDVAD Wave)`
and `Speakers (VDVAD Wave)`. Their presence does not verify sound reaching the
headset. No headset microphone recording has been performed.

Open Virtual Desktop on the Quest 3 and connect to this PC. Enable its
microphone passthrough option for voice conversation. Recheck audio endpoints
after connection before selecting the input/output devices; do not hard-code
device indices from another session.

Virtual Desktop officially supports Quest 3 and desktop display:
https://www.vrdesktop.net/
Its publisher's store listing documents microphone passthrough:
https://www.meta.com/experiences/virtual-desktop/2017050365004772/

## User-provided avatar inspection

| File | Findings |
| --- | --- |
| `C:/Cluster/Diana.blend` | Opened in Blender 4.5.14. 44 meshes, 51,442 mesh vertices, one 356-bone rig, 513 shape-key entries across meshes. Includes lower-jaw and facial bones. No missing file images detected. Script-dependent drivers emitted warnings with automatic scripts disabled. |
| `D:/Data/brandon/Downloads/blender_file (1).zip` | One Blender scene. 231 mesh objects, 41,063 mesh vertices, two rigs (metarig and Rigify), 635 shape-key entries across meshes. Mouth and jaw shapes found, including Jaw_Open. No missing file images detected. Embedded rig UI script was not executed. |
| `D:/Data/brandon/Downloads/blender_file.zip` | One Blender scene. Load raised an error for shape key KEKey.008 with an invalid from pointer; inspection stopped. Original archive was not modified or repaired. |
| `D:/Data/brandon/Downloads/maya.zip` | Maya binary scene `maya file.mb` and textures. Archive inventory only; no Maya scene execution or conversion. |

Counts are raw scene inventory, not evaluated export complexity. Presence of
face bones or morphs does not verify lip-sync deformation or export fidelity.
These files have not established a MetaHuman project or a ready-to-run VR app.
No model has been chosen to replace Yelena's existing avatar yet.

`scripts/inspect_avatar_blend.py` performs the metadata inspection with
Blender automatic Python execution disabled. Extracted working copies, JSON
reports and logs are under ignored `data/avatar-inspection/`. Source files
were neither saved over nor moved. The existing C: asset remains in place.

## Remaining integration

The existing `D:/Avatar/Yelena-Xiomora/Yelena-viewer.html` remains a static preview.
The window at `http://127.0.0.1:8768` reads its VRM model directly and drives
the A mouth morph with speech amplitude from the original app. It uses procedural
skeletal movement and blinking; this is not phoneme alignment. Newly downloaded avatars
still need selection and export/render verification before replacement.
Lisa Reichert XTTS has generated verified speech; Lisa Ann authenticates using
the existing Jarvis environment file. Speech recognition loads successfully,
but microphone capture and the complete headset conversation remain untested.
See LOCAL-SERVICES.md.
