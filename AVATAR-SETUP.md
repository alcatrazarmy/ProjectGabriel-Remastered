# Yelena Xiomora - female avatar requirement

Brandon explicitly requested a female avatar. Her name is Yelena Xiomora. The staged base prompt records female/she-her identity, with no invented age, body design, personality or backstory. Voice remains undecided; changing voice or prompt does not change the avatar mesh.

## What Gabriel actually controls
- src/vrchat.py sends OSC movement and avatar parameters to the running VRChat client. It operates the currently worn avatar, not a bundled character model.
- No .fbx, .vrm, .vrca or .unitypackage asset was found in unity_assets or in the inspected D:/Projects and D:/Data/brandon/Downloads trees. This is a limited local inventory, not a claim about all drives or avatars available inside the VRChat account. No account/session was opened.
- unity_assets contains installers, shaders and sensor/puppet rig components, not a verified licensed female character.
- src/personalities.py reads optional avatar_id from config/prompts/personalities.yml. src/tools/personalities.py can call VRChat's avatar-select API on personality switch. src/vrchatapi.py first authenticates and PUTs /avatars/{avatar_id}/select. That is an account action and has NOT been authorized or performed.
- normal.avatar_id is deliberately empty. searchAvatars, switchAvatar and personality tools remain disabled. No fabricated avatar ID or unsupported gender/body config was added.

## Actual female-body selection needed
Lowest-friction route: Brandon manually selects an existing female avatar he is entitled to use in his VRChat account before a separately approved private test. An available public avatar can be worn without us downloading/uploading a model; availability/rights have not been verified here.
For advanced raycast sensing or generated motion, choose a female humanoid avatar source project with permission to modify it, then prepare the documented Unity rig. Rig setup and upload are separate unperformed actions. Motion model datasets/body priors (such as SMPL male files) do not themselves select the visible VRChat avatar's body.
If automatic switching is later wanted, obtain the chosen accessible avtr_ ID and authorize account access, then populate the supported avatar_id field. Manual avatar selection avoids a new API login.

## Verified offline tests
29 passed in 0.10s: test_pathfinder_and_waypoints.py and test_voxel_nav.py.
Initial run: 27 passed, 2 setup errors because existing D:/Temp/pytest-of-brandon was inaccessible. Reran with a new UUID-named yelena-pytest directory under D:/Temp; no permission changes, deletion of existing directories or project logic changes.
Pytest third-party plugin autoload disabled. Import guards prohibited mss/bettercam/pyaudio/pynput/sounddevice/pygame/discord/pythonosc. Audit guards prohibited socket connect/bind/sendto/DNS, subprocess and os.system. No blocked attempts were recorded. These guards supplement inspected test/import paths; they are not a general OS sandbox.
Results: offline-navigation-tests.txt, offline-navigation-tests.xml, offline-test-guards.json. This verifies navigation math/persistence only, not avatar rendering, voice or companion startup.

## Remaining launch bundle
1. Choose a female avatar already available/licensed to Brandon (or provide the existing source-project path for inspection); do not buy, upload, log in or join a world through automation.
2. Choose the local model/STT/TTS stack described in LOCAL-LAUNCH-PLAN.md and a voice. Model/server/plugin provisioning and native Parakeet/Silero/Pocket execution still require the scoped review/approval described there.
3. Choose first runtime scope: no-device text testing with a reviewed standalone startup adaptation, explicitly permitted microphone/speaker conversation, or separately permitted private VRChat screen/OSC interaction. Current approval covers only the completed navigation tests.
No microphone, screen capture, OSC movement, VRChat account action or cloud call was activated.
