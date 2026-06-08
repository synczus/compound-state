# Render preview of bench for user
import bpy
import os

# Open the saved bench file
bpy.ops.wm.open_mainfile(filepath="/home/synczus/kestrel/outputs/bench.blend")

# Set render settings
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.filepath = "/home/synczus/kestrel/outputs/bench_preview.png"
scene.render.image_settings.file_format = "PNG"

# Use Eevee for fast preview
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 64

# Add ground plane
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, -0.02))
ground = bpy.context.active_object
ground.name = "Ground"
ground_mat = bpy.data.materials.new(name="Ground")
ground_mat.use_nodes = True
ground_mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.4, 0.4, 0.4, 1.0)
ground.data.materials.append(ground_mat)

# Render
bpy.ops.render.render(write_still=True)
print(f"\n✅ Rendered: {scene.render.filepath}")