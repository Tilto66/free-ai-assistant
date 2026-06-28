"""
AI PC Controller — powered by Groq (Free)
------------------------------------------
Controls your PC via natural language commands using Groq's free API.
Capabilities: mouse/keyboard, file management, app launching, window management.

Requirements:
    pip install groq pyautogui pygetwindow

Setup:
    1. Sign up free at https://console.groq.com
    2. Create an API key
    3. Set env var: export GROQ_API_KEY=gsk_...
    4. Run: python ai_pc_controller.py
"""

import os
import sys
import json
import time
import shutil
import platform
import subprocess
import pyautogui
import pygetwindow as gw
from groq import Groq

# ── Safety ─────────────────────────────────────────────────────────────────────
pyautogui.FAILSAFE = True   # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.3       # Small pause between actions for stability

# ── Groq client ────────────────────────────────────────────────────────────────
client = Groq(api_key="gsk_YOUR-GROK-API-KEY")
MODEL = "llama-3.3-70b-versatile"   # Best free model on Groq for tool use

# ── Tool definitions ───────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Click the mouse at given screen coordinates. Use 'right' for context menus, 'double' for opening files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "button": {"type": "string", "enum": ["left", "right", "double"], "description": "Click type (default: left)"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_move",
            "description": "Move the mouse to a position without clicking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_scroll",
            "description": "Scroll at a screen position. Positive clicks = scroll up, negative = scroll down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "clicks": {"type": "integer", "description": "Positive = up, negative = down"},
                },
                "required": ["x", "y", "clicks"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": "Type text at the current cursor position.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_hotkey",
            "description": "Press a keyboard shortcut, e.g. ctrl+c, alt+F4, win+d.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keys to hold together, e.g. ['ctrl', 'c']",
                    },
                },
                "required": ["keys"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_press",
            "description": "Press a single special key: enter, escape, tab, space, backspace, delete, up, down, left, right, f1-f12, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name"},
                },
                "required": ["key"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_size",
            "description": "Returns the screen resolution (width x height).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Takes a screenshot and saves it. Returns the file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Save path (default: screenshot.png)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_windows",
            "description": "Lists all currently open application windows with their titles.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "focus_window",
            "description": "Brings a window to the foreground by its title (partial match supported).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Window title or partial title"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_window",
            "description": "Closes a window by its title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "launch_app",
            "description": "Launches an application, opens a file, or opens a URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "App name, executable path, file path, or URL"},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return its output. Use with caution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 10)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_list",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: current directory)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write or overwrite a text file with given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_copy",
            "description": "Copy a file or directory to a new location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_move",
            "description": "Move or rename a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_delete",
            "description": "Delete a file or directory. Irreversible — confirm with the user first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_create_dir",
            "description": "Create a directory (including any missing intermediate directories).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Pause for a number of seconds before the next action.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number"},
                },
                "required": ["seconds"],
            },
        },
    },
]

# ── Tool executor ──────────────────────────────────────────────────────────────
def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "mouse_click":
            x, y = inputs["x"], inputs["y"]
            btn = inputs.get("button", "left")
            if btn == "double":
                pyautogui.doubleClick(x, y)
            elif btn == "right":
                pyautogui.rightClick(x, y)
            else:
                pyautogui.click(x, y)
            return f"Clicked ({x}, {y}) [{btn}]"

        elif name == "mouse_move":
            pyautogui.moveTo(inputs["x"], inputs["y"], duration=0.3)
            return f"Moved to ({inputs['x']}, {inputs['y']})"

        elif name == "mouse_scroll":
            pyautogui.scroll(inputs["clicks"], x=inputs["x"], y=inputs["y"])
            return f"Scrolled {inputs['clicks']} at ({inputs['x']}, {inputs['y']})"

        elif name == "keyboard_type":
            pyautogui.write(inputs["text"], interval=0.03)
            return f"Typed: {inputs['text']!r}"

        elif name == "keyboard_hotkey":
            pyautogui.hotkey(*inputs["keys"])
            return f"Hotkey: {'+'.join(inputs['keys'])}"

        elif name == "keyboard_press":
            pyautogui.press(inputs["key"])
            return f"Pressed: {inputs['key']}"

        elif name == "get_screen_size":
            w, h = pyautogui.size()
            return f"Screen size: {w}x{h}"

        elif name == "take_screenshot":
            path = inputs.get("path", "screenshot.png")
            pyautogui.screenshot(path)
            return f"Screenshot saved to: {os.path.abspath(path)}"

        elif name == "list_windows":
            wins = [w.title for w in gw.getAllWindows() if w.title.strip()]
            return json.dumps(wins, indent=2)

        elif name == "focus_window":
            title = inputs["title"]
            matches = gw.getWindowsWithTitle(title)
            if not matches:
                matches = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            if not matches:
                return f"No window found matching '{title}'"
            win = matches[0]
            win.activate()
            time.sleep(0.3)
            return f"Focused: {win.title}"

        elif name == "close_window":
            title = inputs["title"]
            matches = gw.getWindowsWithTitle(title)
            if not matches:
                matches = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            if not matches:
                return f"No window found matching '{title}'"
            matches[0].close()
            return f"Closed: {matches[0].title}"

        elif name == "launch_app":
            target = inputs["target"]
            system = platform.system()
            if system == "Windows":
                os.startfile(target)
            elif system == "Darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
            return f"Launched: {target}"

        elif name == "run_command":
            result = subprocess.run(
                inputs["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=inputs.get("timeout", 10),
            )
            return (result.stdout or result.stderr or "(no output)")[:2000]

        elif name == "file_list":
            path = inputs.get("path", ".")
            entries = os.listdir(path)
            lines = []
            for e in sorted(entries):
                kind = "DIR" if os.path.isdir(os.path.join(path, e)) else "FILE"
                lines.append(f"[{kind}] {e}")
            return "\n".join(lines) if lines else "(empty directory)"

        elif name == "file_read":
            with open(inputs["path"], "r", encoding="utf-8", errors="replace") as f:
                return f.read(8000)

        elif name == "file_write":
            with open(inputs["path"], "w", encoding="utf-8") as f:
                f.write(inputs["content"])
            return f"Written to: {inputs['path']}"

        elif name == "file_copy":
            src, dst = inputs["source"], inputs["destination"]
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            return f"Copied {src} → {dst}"

        elif name == "file_move":
            shutil.move(inputs["source"], inputs["destination"])
            return f"Moved {inputs['source']} → {inputs['destination']}"

        elif name == "file_delete":
            path = inputs["path"]
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return f"Deleted: {path}"

        elif name == "file_create_dir":
            os.makedirs(inputs["path"], exist_ok=True)
            return f"Created directory: {inputs['path']}"

        elif name == "wait":
            time.sleep(inputs["seconds"])
            return f"Waited {inputs['seconds']}s"

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        return f"ERROR: {e}"


# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""You are an AI assistant that controls a {platform.system()} computer on behalf of the user.

You have tools for:
- Mouse control (click, move, scroll)
- Keyboard input (type text, hotkeys, special keys)
- Screenshot capture
- Window management (list, focus, close)
- App and URL launching
- Shell commands
- File operations (list, read, write, copy, move, delete, create dirs)

Guidelines:
- Break complex tasks into sequential tool calls.
- For GUI interactions, take a screenshot first to see the current screen.
- Always confirm with the user before deleting files or running destructive commands.
- Be concise — briefly explain what you're doing and why.
- If something fails, try an alternative approach.
- Screen coordinates start at (0,0) top-left. Use get_screen_size if needed.
- Click a text field before typing into it.
"""

# ── Main agentic loop ──────────────────────────────────────────────────────────
def run():
    print("\n╔══════════════════════════════════════════╗")
    print("║   AI PC Controller — Groq (Free)         ║")
    print("║  Type your command. 'quit' to exit.      ║")
    print("║  Move mouse to top-left corner to abort. ║")
    print("╚══════════════════════════════════════════╝\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        # Agentic loop — model may call multiple tools in sequence
        while True:
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=4096,
                )
            except Exception as e:
                print(f"\nAPI error: {e}\nRetrying without tools...")
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=4096,
                )

            msg = response.choices[0].message
            messages.append(msg)  # groq message objects are serialisable

            # Print any text the model produced
            if msg.content and msg.content.strip():
                print(f"\nAssistant: {msg.content.strip()}\n")

            # No tool calls → model is done
            if not msg.tool_calls:
                break

            # Execute each tool call and feed results back
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"  → [{fn_name}] {json.dumps(fn_args)}")
                result = execute_tool(fn_name, fn_args)
                print(f"  ← {result[:200]}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })


if __name__ == "__main__":
    run()
