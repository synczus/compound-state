"""
Blender Agent Control Add-on
══════════════════════════════

Installs a lightweight HTTP server inside Blender that lets compound
agents execute bpy code remotely in your live session.

Install: Copy this file to:
  ~/config/blender/4.3/scripts/addons/blender_agent_control.py
Then: Edit → Preferences → Add-ons → Enable "Agent Control"

Or run once:
  blender --python blender_agent_control.py

Endpoints:
  POST /exec          Execute bpy code     {"code": "bpy.ops.mesh...", "name": "my_asset"}
  POST /exec-file     Execute .py file     {"path": "/path/to/script.py"}
  GET  /ping          Health check
  GET  /scene-info    Scene stats (object count, types, memory)

Usage from Telegram agents:
  curl -X POST http://localhost:9877/exec \
    -H "Content-Type: application/json" \
    -d '{"code": "bpy.ops.mesh.primitive_monkey_add(location=(0,0,0))"}'

Author: Nemoclaw / Compound Agents
"""

bl_info = {
    "name": "Agent Control",
    "author": "Nemoclaw",
    "version": (1, 0, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Agent",
    "description": "HTTP server for remote agent control of Blender",
    "category": "Development",
}

import bpy
import json
import os
import queue
import socket
import sys
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── Globals ──────────────────────────────────────────────────────────

HOST = "127.0.0.1"
PORT = 9877
CMD_QUEUE = queue.Queue()
RESULT_QUEUE = queue.Queue()
SERVER = None
SERVER_THREAD = None
TIMER_RUNNING = False

# ── HTTP Handler ─────────────────────────────────────────────────────

class AgentHandler(BaseHTTPRequestHandler):
    """HTTP handler that queues bpy commands for main-thread execution."""

    def log_message(self, format, *args):
        # Quiet logging — Blender's console is noisy enough
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/ping":
            self._send_json({"status": "ok", "agent": "blender-agent-control"})

        elif path == "/scene-info":
            # Collect scene info from the main thread
            CMD_QUEUE.put(("scene-info", {}))
            try:
                result = RESULT_QUEUE.get(timeout=10)
                self._send_json(result)
            except queue.Empty:
                self._send_json({"error": "timeout"}, 504)

        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"}, 400)
            return

        if path == "/exec":
            code = data.get("code", "")
            if not code:
                self._send_json({"error": "missing 'code' field"}, 400)
                return

            name = data.get("name", "unnamed")
            CMD_QUEUE.put(("exec", {"code": code, "name": name}))

            try:
                result = RESULT_QUEUE.get(timeout=30)
                self._send_json(result)
            except queue.Empty:
                self._send_json({"error": "execution timeout (>30s)"}, 504)

        elif path == "/exec-file":
            script_path = data.get("path", "")
            if not script_path or not os.path.exists(script_path):
                self._send_json({"error": "file not found"}, 404)
                return

            with open(script_path) as f:
                code = f.read()

            CMD_QUEUE.put(("exec", {"code": code, "name": os.path.basename(script_path)}))
            try:
                result = RESULT_QUEUE.get(timeout=30)
                self._send_json(result)
            except queue.Empty:
                self._send_json({"error": "execution timeout (>30s)"}, 504)

        else:
            self._send_json({"error": "not found"}, 404)


# ── Timer: Poll Queue & Execute on Main Thread ──────────────────────

def poll_commands():
    """Called by bpy.app.timers every 0.1s. Executes queued bpy code."""
    global TIMER_RUNNING

    try:
        while not CMD_QUEUE.empty():
            cmd_type, cmd_data = CMD_QUEUE.get_nowait()

            if cmd_type == "exec":
                code = cmd_data["code"]
                name = cmd_data["name"]

                # Save context
                context_override = {
                    "area": next(
                        (a for a in bpy.context.screen.areas if a.type == "VIEW_3D"),
                        None,
                    ),
                }

                try:
                    # Create a namespace with bpy already imported
                    namespace = {
                        "bpy": bpy,
                        "C": bpy.context,
                        "D": bpy.data,
                        "scene": bpy.context.scene,
                    }

                    exec(code, namespace)

                    # If script defined a main() function, call it
                    if "main" in namespace and callable(namespace["main"]):
                        namespace["main"]()

                    RESULT_QUEUE.put({"status": "success", "name": name})

                except Exception as e:
                    tb = traceback.format_exc()
                    RESULT_QUEUE.put({
                        "status": "error",
                        "error": str(e),
                        "traceback": tb,
                    })

            elif cmd_type == "scene-info":
                info = {
                    "objects": len(bpy.data.objects),
                    "meshes": len(bpy.data.meshes),
                    "materials": len(bpy.data.materials),
                    "cameras": len([o for o in bpy.data.objects if o.type == "CAMERA"]),
                    "lights": len([o for o in bpy.data.objects if o.type == "LIGHT"]),
                    "scene_name": bpy.context.scene.name,
                    "render_engine": bpy.context.scene.render.engine,
                    "resolution": f"{bpy.context.scene.render.resolution_x}x{bpy.context.scene.render.resolution_y}",
                }
                RESULT_QUEUE.put(info)

    except Exception as e:
        print(f"[AgentControl] Timer error: {e}")

    return 0.1  # Re-register timer (poll every 100ms)


# ── Server Thread ────────────────────────────────────────────────────

def start_server():
    """Start the HTTP server in a background thread."""
    global SERVER

    server = HTTPServer((HOST, PORT), AgentHandler)
    SERVER = server
    print(f"\n═══ Agent Control Server ═══")
    print(f"  Listening on http://{HOST}:{PORT}")
    print(f"  POST /exec       — Execute bpy code")
    print(f"  POST /exec-file  — Execute .py file")
    print(f"  GET  /ping       — Health check")
    print(f"  GET  /scene-info — Scene statistics")
    print(f"═══════════════════════════════\n")
    server.serve_forever()


def stop_server():
    """Shut down the HTTP server."""
    global SERVER, SERVER_THREAD
    if SERVER:
        SERVER.shutdown()
        SERVER = None
    if SERVER_THREAD:
        SERVER_THREAD = None


# ── Operator: Toggle Server ──────────────────────────────────────────

class AGENT_OT_toggle_server(bpy.types.Operator):
    """Start/Stop the Agent Control server"""
    bl_idname = "agent.toggle_server"
    bl_label = "Toggle Agent Server"
    bl_description = f"Start/stop the agent HTTP server on port {PORT}"

    def execute(self, context):
        global SERVER_THREAD, TIMER_RUNNING

        if SERVER is not None:
            # Stop
            stop_server()
            self.report({"INFO"}, "Agent server stopped")
            return {"FINISHED"}

        # Start
        SERVER_THREAD = threading.Thread(target=start_server, daemon=True)
        SERVER_THREAD.start()

        if not TIMER_RUNNING:
            bpy.app.timers.register(poll_commands, persistent=True)
            TIMER_RUNNING = True

        self.report({"INFO"}, f"Agent server running on http://{HOST}:{PORT}")
        return {"FINISHED"}


# ── UI Panel ─────────────────────────────────────────────────────────

class AGENT_PT_main(bpy.types.Panel):
    """Panel in the 3D Viewport sidebar"""
    bl_label = "Agent Control"
    bl_idname = "AGENT_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Agent"

    def draw(self, context):
        layout = self.layout

        status = "🟢 Running" if SERVER else "🔴 Stopped"
        layout.label(text=f"Server: {status}")
        layout.label(text=f"Port: {PORT}")

        row = layout.row()
        row.scale_y = 1.5
        if SERVER:
            row.operator("agent.toggle_server", text="Stop Server", icon="PAUSE")
        else:
            row.operator("agent.toggle_server", text="Start Server", icon="PLAY")

        layout.separator()

        layout.label(text="Quick Actions:")
        col = layout.column(align=True)
        col.operator("agent.add_monkey", text="🐵 Spawn Monkey", icon="MESH_MONKEY")
        col.operator("agent.add_cube", text="📦 Spawn Cube", icon="MESH_CUBE")
        col.operator("agent.add_light", text="💡 Spawn Light", icon="LIGHT_SUN")


class AGENT_OT_add_monkey(bpy.types.Operator):
    """Spawn a Suzanne monkey at 3D cursor"""
    bl_idname = "agent.add_monkey"
    bl_label = "Spawn Monkey"

    def execute(self, context):
        bpy.ops.mesh.primitive_monkey_add(
            location=context.scene.cursor.location
        )
        self.report({"INFO"}, "🦍 Monkey spawned")
        return {"FINISHED"}


class AGENT_OT_add_cube(bpy.types.Operator):
    """Spawn a cube at 3D cursor"""
    bl_idname = "agent.add_cube"
    bl_label = "Spawn Cube"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add(
            location=context.scene.cursor.location
        )
        self.report({"INFO"}, "📦 Cube spawned")
        return {"FINISHED"}


class AGENT_OT_add_light(bpy.types.Operator):
    """Spawn a sun light"""
    bl_idname = "agent.add_light"
    bl_label = "Spawn Sun Light"

    def execute(self, context):
        bpy.ops.object.light_add(
            type="SUN",
            location=context.scene.cursor.location
        )
        self.report({"INFO"}, "☀️ Light spawned")
        return {"FINISHED"}


# ── Registration ─────────────────────────────────────────────────────

classes = [
    AGENT_OT_toggle_server,
    AGENT_OT_add_monkey,
    AGENT_OT_add_cube,
    AGENT_OT_add_light,
    AGENT_PT_main,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    stop_server()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

    # Auto-start the server when run as a script
    bpy.ops.agent.toggle_server()