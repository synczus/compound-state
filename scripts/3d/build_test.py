"""Blender test: build a scene — floating sphere with ring.
Tests: primitives, material, camera, lighting, render.
"""
import sys
import os

# Load template
sys.path.insert(0, "/home/synczus/kestrel/scripts/3d")
from blender_template import *

clear_scene()
setup_camera(location=(4, -4, 3), target=(0, 0, 0.5))
setup_lighting()
setup_render(engine="CYCLES")

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -0.5))
plane = bpy.context.active_object
add_material(plane, color=(0.15, 0.15, 0.15), roughness=0.8)

# Main sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(0, 0, 0.5))
sphere = bpy.context.active_object
add_material(sphere, color=(0.9, 0.2, 0.2), roughness=0.2, metal=0.6)

# Ring/torus around sphere
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.8, minor_radius=0.08,
    location=(0, 0, 0.5)
)
ring = bpy.context.active_object
ring.rotation_euler = (1.2, 0.3, 0.5)
add_material(ring, color=(1.0, 0.8, 0.2), roughness=0.1, metal=0.9)

# Small orbiting spheres
import math
for i in range(8):
    angle = i * 2 * math.pi / 8
    x = 2.2 * math.cos(angle)
    y = 2.2 * math.sin(angle)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, y, 0.5))
    orb = bpy.context.active_object
    orb.name = f"Orbiter_{i}"
    add_material(orb, color=(0.3, 0.6, 1.0), roughness=0.1, metal=0.7)

blend_path = save_blend("test_sphere.blend")
render_path = render_still("test_sphere_render.png")
print(f"\n✅ Build complete: {blend_path}")
print(f"📷 Render: {render_path}")