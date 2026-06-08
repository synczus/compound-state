"""Blender test — check available engines and basic operations."""
import bpy

# List render engines
for e in bpy.types.RenderEngine.__subclasses__():
    try:
        if hasattr(e, 'bl_idname'):
            print(f"Engine: {e.bl_idname}")
    except:
        pass

# Available engines
avail = []
for e in bpy.types.RenderEngine.__subclasses__():
    try:
        if hasattr(e, 'bl_idname'):
            avail.append(e.bl_idname)
    except:
        pass
print(f"Available engines: {avail}")

# Basic ops — cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
print(f"Objects: {len(bpy.data.objects)}")

# Set render engine
for s in bpy.data.scenes:
    print(f"Scene '{s.name}': engine={s.render.engine}")

# Save test file
output_path = "/home/synczus/gdrive/kestrel-notes/3d/blender_test.blend"
import os
os.makedirs(os.path.dirname(output_path), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"Saved: {output_path}")