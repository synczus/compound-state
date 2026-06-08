"""Blender template: basic scene setup.

Use this as a starting template for any Blender build.
- Clears the default cube
- Sets up camera + 3-point lighting
- Configures Cycles render engine
"""

import bpy
import os
import sys

# ── CONFIG ───────────────────────────────────────────────────────
OUTPUT_DIR = "/home/synczus/gdrive/kestrel-notes/3d"
RENDER_WIDTH = 1920
RENDER_HEIGHT = 1080
RENDER_SAMPLES = 128
# ──────────────────────────────────────────────────────────────────


def clear_scene():
    """Remove default objects."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def setup_camera(location=(7, -7, 5), target=(0, 0, 0)):
    """Position camera looking at target."""
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    cam.name = "Camera"
    # Point at target
    direction = (target[0] - location[0],
                 target[1] - location[1],
                 target[2] - location[2])
    cam.rotation_euler = (
        direction[2] * 0.1,
        0,
        direction[1] * 0.1
    )
    bpy.context.scene.camera = cam
    return cam


def setup_lighting():
    """3-point lighting: key, fill, rim + ambient."""
    # Key light (warm, strong)
    bpy.ops.object.light_add(type="AREA", location=(5, -5, 8))
    key = bpy.context.active_object
    key.name = "Key Light"
    key.data.energy = 500
    key.data.color = (1.0, 0.9, 0.7)

    # Fill light (cool, soft)
    bpy.ops.object.light_add(type="AREA", location=(-4, -3, 4))
    fill = bpy.context.active_object
    fill.name = "Fill Light"
    fill.data.energy = 200
    fill.data.color = (0.7, 0.8, 1.0)

    # Rim light
    bpy.ops.object.light_add(type="AREA", location=(0, 6, 3))
    rim = bpy.context.active_object
    rim.name = "Rim Light"
    rim.data.energy = 300
    rim.data.color = (1.0, 1.0, 0.9)


def setup_render(engine="CYCLES"):
    """Configure render settings."""
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.resolution_x = RENDER_WIDTH
    scene.render.resolution_y = RENDER_HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    if engine == "CYCLES":
        scene.cycles.samples = RENDER_SAMPLES
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.01
        scene.cycles.max_bounces = 8
        scene.view_settings.look = "AgX - Very High Contrast"


def add_material(obj, color=(0.8, 0.3, 0.3), roughness=0.3, metal=0.0):
    """Add a simple material to an object."""
    mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (*color, 1.0)
        principled.inputs["Roughness"].default_value = roughness
        principled.inputs["Metallic"].default_value = metal
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    return mat


def render_still(filename="render.png"):
    """Render the current scene to a PNG file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"RENDER_SAVED={output_path}")
    return output_path


def save_blend(filename="scene.blend"):
    """Save the .blend file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"BLEND_SAVED={output_path}")
    return output_path