# Blender Agent Protocol — Describe → Build → Render

## Lane
All agents. This is a shared skill.

## What It Is
When a human says "build me [thing]" in chat, any compound agent can:
1. Generate a valid `bpy` Python script
2. Execute it through the Blender headless runner
3. Post the rendered result back to the chat

## Architecture

```
Human: "Build me a rotating gear with 8 teeth"
  → Agent generates bpy script
  → Writes to /home/synczus/kestrel/blender/scripts/<name>.py
  → Executes via:
      BLENDER_OUTPUT_DIR=/home/synczus/kestrel/blender/output \
      /home/synczus/blender-4.3.2-linux-x64/blender --background \
      --python /home/synczus/kestrel/blender/run.py \
      -- --script=/path/to/script.py --output=<name>
  → Reads result from /home/synczus/kestrel/blender/output/result.json
  → Sends output PNG to the chat
```

Or via n8n:
- n8n webhook receives the description
- Sub-agent generates the bpy script
- n8n executes blender --background with the script
- Result posted to Telegram

## Blender Runner API

The runner (`/home/synczus/kestrel/blender/run.py`) provides these globals:

| Function | Purpose |
|---|---|
| `clean_scene()` | Delete all objects, start fresh |
| `setup_basic_scene()` | Add default camera + sun light |
| `render_still(path)` | Render current scene to PNG |
| `render_animation(dir, fps, frames)` | Render animation frames |
| `bpy` | Full Blender Python API |
| `C` | `bpy.context` |
| `D` | `bpy.data` |
| `scene` | `bpy.context.scene` |

### Script Structure

Every Blender script MUST define a `render(output_path)` function:

```python
def render(output_path):
    """Build scene, render to output_path, return path."""
    clean_scene()
    setup_basic_scene()

    # Your bpy code here
    bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0))

    return render_still(output_path)
```

The render function receives `output_path` (string) and should return it after rendering.

## Output Paths
- Scripts: `/home/synczus/kestrel/blender/scripts/`
- Renders: `/home/synczus/kestrel/blender/output/`
- Runner: `/home/synczus/kestrel/blender/run.py`
- Blender binary: `/home/synczus/blender-4.3.2-linux-x64/blender`

## Constraints
- Keep polygon counts reasonable (< 100K for quick renders)
- Use `bpy.ops.mesh.primitive_*` and `bpy.ops.object.*` for construction
- Materials use ShaderNodeBsdfPrincipled
- Resolution: 1920x1080 default
- Renders should aim for < 30s execution time

## Examples

### 1. Simple sphere with material
```python
def render(output_path):
    clean_scene()
    setup_basic_scene()
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 0), radius=1)
    return render_still(output_path)
```

### 2. Animated rotation
```python
def render(output_path):
    clean_scene()
    setup_basic_scene()
    bpy.ops.mesh.primitive_torus_add(location=(0, 0, 0))
    obj = bpy.context.object
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.rotation_euler = (0, 0, 3.14159 * 2)
    obj.keyframe_insert(data_path="rotation_euler", frame=48)
    scene.frame_end = 48
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    return render_still(output_path)
```