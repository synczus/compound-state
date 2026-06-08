"""Blender Runner — execute bpy scripts headless and output renders.

This script is the bridge between agent-generated Blender Python and
Blender's headless engine. Agents write scripts that define a `render()`
function, and this runner calls it, handles output, and ships the result.

Usage:
  blender --background --python run.py -- --script=/path/to/script.py

Or via n8n:
  blender --background --python run.py -- --script=<inline_script>
"""

import bpy
import sys
import json
import os
import argparse
import tempfile
import base64

OUTPUT_DIR = os.environ.get("BLENDER_OUTPUT_DIR", "/tmp/blender-output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_args():
    """Parse --key=value arguments after the -- separator."""
    args = {}
    for arg in sys.argv:
        if arg.startswith("--"):
            arg = arg.lstrip("-")
            if "=" in arg:
                key, val = arg.split("=", 1)
                args[key] = val
            else:
                args[arg] = True
    return args


def clean_scene():
    """Remove default cube, camera, light to start fresh."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def setup_basic_scene():
    """Add a camera and a light source if none exist."""
    # Check if camera exists
    if not any(obj.type == "CAMERA" for obj in bpy.data.objects):
        bpy.ops.object.camera_add(location=(5, -5, 5))
        cam = bpy.context.object
        cam.rotation_euler = (1.1, 0, 0.8)
        bpy.context.scene.camera = cam

    # Check if light exists
    if not any(obj.type == "LIGHT" for obj in bpy.data.objects):
        bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
        light = bpy.context.object
        light.data.energy = 3


def render_still(output_path):
    """Render the current scene as a PNG."""
    scene = bpy.context.scene
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return output_path


def render_animation(output_dir, fps=24, frame_count=48):
    """Render animation frames to output_dir."""
    scene = bpy.context.scene
    scene.render.filepath = os.path.join(output_dir, "frame_")
    scene.render.image_settings.file_format = "PNG"
    scene.frame_start = 1
    scene.frame_end = frame_count
    bpy.ops.render.render(animation=True)
    return output_dir


def write_result(result_data: dict):
    """Write execution result as JSON for n8n/agent to consume."""
    result_path = os.path.join(OUTPUT_DIR, "result.json")
    with open(result_path, "w") as f:
        json.dump(result_data, f)
    print(f"\n--- BLENDER RESULT ---")
    print(json.dumps(result_data))
    print(f"--- END BLENDER RESULT ---")


def main():
    args = parse_args()

    script_path = args.get("script")
    inline_script = args.get("inline")
    output_name = args.get("output", "render")

    if not script_path and not inline_script:
        print("ERROR: Provide --script=<path> or --inline=<bpy_code>")
        sys.exit(1)

    if inline_script:
        # Write inline script to temp file
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir="/tmp"
        )
        tmp.write(inline_script)
        tmp.close()
        script_path = tmp.name

    # Execute the user script
    namespace = {
        "bpy": bpy,
        "C": bpy.context,
        "D": bpy.data,
        "scene": bpy.context.scene,
        "output_dir": OUTPUT_DIR,
        "clean_scene": clean_scene,
        "setup_basic_scene": setup_basic_scene,
        "render_still": render_still,
        "render_animation": render_animation,
    }

    try:
        with open(script_path) as f:
            exec(f.read(), namespace)
    except Exception as e:
        write_result({"status": "error", "error": str(e)})
        sys.exit(1)

    # If script defined render(), call it
    if "render" in namespace and callable(namespace["render"]):
        try:
            output_file = os.path.join(OUTPUT_DIR, f"{output_name}.png")
            result = namespace["render"](output_file)
            write_result(
                {
                    "status": "success",
                    "output": result if result else output_file,
                    "type": "still",
                }
            )
        except Exception as e:
            write_result({"status": "error", "error": str(e)})
            sys.exit(1)
    else:
        write_result({"status": "ok", "message": "Script executed, no render() call"})


if __name__ == "__main__":
    main()