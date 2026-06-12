#!/usr/bin/env python3
"""
Blender bench generator — game-ready low-poly park bench.
Usage: blender --background --python build-bench.py

Output: /home/synczus/kestrel/outputs/bench.blend + bench.fbx
"""

import bpy
import os
import sys
from math import radians

OUTPUT_DIR = "/home/synczus/kestrel/outputs"

# ── Clean slate ──────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)

# ── Materials ────────────────────────────────────────────
wood_mat = bpy.data.materials.new(name="Wood")
wood_mat.use_nodes = True
bsdf = wood_mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs[0].default_value = (0.45, 0.28, 0.12, 1.0)  # Base Color (brown)
bsdf.inputs[2].default_value = 0.3  # Roughness

metal_mat = bpy.data.materials.new(name="Metal")
metal_mat.use_nodes = True
bsdf2 = metal_mat.node_tree.nodes["Principled BSDF"]
bsdf2.inputs[0].default_value = (0.15, 0.15, 0.15, 1.0)  # Base Color (dark grey)
bsdf2.inputs[2].default_value = 0.6  # Roughness
bsdf2.inputs[1].default_value = 0.5  # Metallic

# ── Seat planks ──────────────────────────────────────────
plank_count = 5
plank_width = 0.15
plank_height = 0.05
seat_depth = 0.5
seat_length = 1.8

for i in range(plank_count):
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(
            -seat_length / 2 + seat_length / (plank_count + 1) * (i + 1),
            0,
            plank_height / 2
        ),
        scale=(0.9, seat_depth / 2, plank_height / 2)
    )
    obj = bpy.context.active_object
    obj.name = f"Seat_Plank_{i}"
    obj.data.materials.append(wood_mat)

# ── Backrest ─────────────────────────────────────────────
backrest_height = 0.5
backrest_thickness = 0.04
backrest_angle = 15  # degrees lean back

# Backrest support legs (2 vertical)
for x_pos in [-0.7, 0.7]:
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(x_pos, -seat_depth / 2 + 0.02, seat_depth / 4 + backrest_height / 2),
        scale=(0.04, 0.04, backrest_height / 2)
    )
    obj = bpy.context.active_object
    obj.name = f"Backrest_Leg_{x_pos}"
    obj.data.materials.append(metal_mat)

# Backrest planks
backrest_planks = 4
for i in range(backrest_planks):
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(
            -seat_length / 2 + seat_length / (backrest_planks + 1) * (i + 1),
            -seat_depth / 2 + 0.02,
            seat_depth / 4 + backrest_height / 2
        ),
        scale=(0.9, backrest_thickness / 2, (backrest_height - 0.05) / 2)
    )
    obj = bpy.context.active_object
    obj.name = f"Backrest_Plank_{i}"
    obj.data.materials.append(wood_mat)

# ── Legs ─────────────────────────────────────────────────
leg_height = 0.4
leg_thickness = 0.05

for x_pos in [-0.8, 0.8]:
    for y_pos in [-seat_depth / 2 + 0.05, seat_depth / 2 - 0.05]:
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(x_pos, y_pos, leg_height / 2 + plank_height),
            scale=(leg_thickness / 2, leg_thickness / 2, leg_height / 2)
        )
        obj = bpy.context.active_object
        obj.name = f"Leg_{x_pos}_{y_pos}"
        obj.data.materials.append(metal_mat)

# ── Armrests ─────────────────────────────────────────────
for x_pos in [-0.85, 0.85]:
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(x_pos, 0, seat_depth / 4 + backrest_height / 2),
        scale=(0.04, seat_depth / 2, 0.04)
    )
    obj = bpy.context.active_object
    obj.name = f"Armrest_{x_pos}"
    obj.data.materials.append(wood_mat)

# ── Lighting & Camera ────────────────────────────────────
bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 5

bpy.ops.object.camera_add(location=(-0.5, -2.5, 1.2))
cam = bpy.context.active_object
cam.rotation_euler = (radians(60), 0, radians(5))
bpy.context.scene.camera = cam

# ── Output ───────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)

blend_path = os.path.join(OUTPUT_DIR, "bench.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"\n✅ Saved: {blend_path}")

# Export FBX
fbx_path = os.path.join(OUTPUT_DIR, "bench.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=False,
    object_types={"MESH"},
    apply_scale_options="FBX_SCALE_UNITS"
)
print(f"✅ Exported: {fbx_path}")
print(f"\n📐 Poly count: {sum(len(obj.data.polygons) for obj in bpy.data.objects if obj.type == 'MESH')}")