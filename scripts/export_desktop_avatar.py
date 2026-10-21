"""Export a working copy of the supplied CC/Rigify avatar for local display.

blender --background --factory-startup --disable-autoexec --python-exit-code 1
  --python scripts/export_desktop_avatar.py -- SOURCE.blend OUTPUT.glb
Original Blender file is never saved. Embedded scripts remain disabled.
"""
import json
import sys
from pathlib import Path

import bpy

source, destination = (Path(p).resolve() for p in sys.argv[sys.argv.index("--") + 1:])
destination.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
rig = bpy.data.objects.get("blender file_Rigify")
if not rig:
    raise RuntimeError("Expected the supplied Rigify character")
meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig and o.name not in {"EyeOcclusion", "TearLine"}]
keep = {"V_Open", "V_Tight_O", "V_Wide", "V_Dental_Lip", "Eye_Blink_L", "Eye_Blink_R", "Mouth_Smile_L", "Mouth_Smile_R", "Jaw_Open", "Brow_Raise_Inner_L", "Brow_Raise_Inner_R"}
rig.animation_data_clear()
rig.data.pose_position = "REST"
for obj in meshes:
    obj.animation_data_clear()
    if obj.data.shape_keys:
        obj.data.shape_keys.animation_data_clear()
        for key in list(obj.data.shape_keys.key_blocks)[1:]:
            if key.name not in keep:
                obj.shape_key_remove(key)
            else:
                key.value = 0
    # Character source uses custom addon shaders. Rebuild portable PBR nodes
    # from the source's explicitly named diffuse/normal/opacity image nodes.
    for mod in list(obj.modifiers):
        if mod.type != "ARMATURE":
            obj.modifiers.remove(mod)

materials = {m for obj in meshes for m in obj.data.materials if m}
used_images = set()
for material in materials:
    maps = {}
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                for kind in ["DIFFUSE", "NORMAL", "ALPHA", "ROUGHNESS"]:
                    if f"({kind})" in node.name:
                        maps[kind] = node.image
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    bsdf, output = nodes.new("ShaderNodeBsdfPrincipled"), nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = .6
    bsdf.inputs["Metallic"].default_value = 0
    material.use_backface_culling = False
    for kind, image in maps.items():
        used_images.add(image)
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        if kind == "DIFFUSE":
            image.colorspace_settings.name = "sRGB"
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        elif kind == "NORMAL":
            image.colorspace_settings.name = "Non-Color"
            normal = nodes.new("ShaderNodeNormalMap")
            normal.inputs["Strength"].default_value = .55
            links.new(tex.outputs["Color"], normal.inputs["Color"])
            links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
        elif kind == "ROUGHNESS":
            image.colorspace_settings.name = "Non-Color"
            links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])
        elif kind == "ALPHA":
            image.colorspace_settings.name = "Non-Color"
            links.new(tex.outputs["Color"], bsdf.inputs["Alpha"])
            material.surface_render_method = "DITHERED"

for image in used_images:
    width, height = image.size
    if max(width, height) > 2048:
        factor = 2048 / max(width, height)
        image.scale(round(width * factor), round(height * factor))

bpy.ops.object.select_all(action="DESELECT")
rig.hide_set(False)
rig.select_set(True)
for obj in meshes:
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=str(destination), export_format="GLB", use_selection=True,
    export_animations=False, export_skins=True, export_def_bones=True,
    export_rest_position_armature=True, export_morph=True,
    export_morph_normal=True, export_morph_tangent=False,
    export_materials="EXPORT", export_image_format="AUTO",
    export_extras=False, export_cameras=False, export_lights=False,
)
print(json.dumps({"output": str(destination), "bytes": destination.stat().st_size, "mesh_objects": len(meshes), "materials": len(materials)}))
