"""Read avatar rig metadata in Blender; never save or run embedded scripts.

Run with blender --background --factory-startup --disable-autoexec
--python-exit-code 1 --python scripts/inspect_avatar_blend.py -- SOURCE OUTPUT.
SOURCE may be a .blend or a ZIP containing exactly one .blend.
"""

import json
import sys
import zipfile
from pathlib import Path

import bpy


def inspect(source, output):
    source = Path(source).resolve()
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    blend = source
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            members = [item for item in archive.infolist() if item.filename.lower().endswith(".blend")]
            if len(members) != 1:
                raise ValueError("Expected exactly one Blender scene in the archive")
            blend = output.with_suffix(".blend")
            # Use our own destination, never an archive-controlled extraction path.
            with archive.open(members[0]) as reader, blend.open("wb") as writer:
                import shutil
                shutil.copyfileobj(reader, writer)
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False, use_scripts=False)
    meshes = []
    rigs = []
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            keys = obj.data.shape_keys
            meshes.append({
                "name": obj.name,
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "shape_keys": [key.name for key in keys.key_blocks] if keys else [],
                "armatures": [mod.object.name for mod in obj.modifiers if mod.type == "ARMATURE" and mod.object],
            })
        elif obj.type == "ARMATURE":
            rigs.append({"name": obj.name, "bones": [bone.name for bone in obj.data.bones]})
    images = [{
        "name": image.name,
        "packed": bool(image.packed_file or image.packed_files),
        "source": image.source,
        "external_exists": Path(bpy.path.abspath(image.filepath)).is_file() if image.filepath else False,
    } for image in bpy.data.images]
    report = {
        "source": str(source), "blender_version": bpy.app.version_string,
        "meshes": meshes, "rigs": rigs, "images": images,
        "embedded_text_count": len(bpy.data.texts),
        "embedded_scripts_executed": False,
    }
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "source": str(source), "report": str(output),
        "meshes": len(meshes), "rigs": len(rigs),
        "shape_keys": sum(len(mesh["shape_keys"]) for mesh in meshes),
        "missing_images": sum(not image["packed"] and not image["external_exists"] for image in images if image["source"] == "FILE"),
    }))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 2:
        raise SystemExit("Expected SOURCE OUTPUT after --")
    inspect(*args)
