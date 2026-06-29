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
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" 

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
            "description": "Takes a screenshot and send it to the ai. Optionally specify a path to save the image.",
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
            path = (inputs or {}).get("path", "screenshot.png")
            pyautogui.screenshot(path)
            import base64
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"SCREENSHOT_B64:{b64}"
 
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
# ── Memory system ──────────────────────────────────────────────────────────────
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
MAX_HISTORY  = 20   # max past exchanges to keep in memory
MAX_FACTS    = 50   # max facts/preferences to store
 
def load_memory() -> dict:
    """Load memory from disk, or return a fresh structure."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"facts": [], "history": []}
 
def save_memory(memory: dict) -> None:
    """Persist memory to disk."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        print(f"  [memory] Could not save: {e}")
 
def update_history(memory: dict, role: str, content: str) -> None:
    """Append a message to rolling history, trimming to MAX_HISTORY exchanges."""
    memory["history"].append({"role": role, "content": content})
    # Keep only the last MAX_HISTORY messages (each exchange = 2 messages)
    if len(memory["history"]) > MAX_HISTORY * 2:
        memory["history"] = memory["history"][-(MAX_HISTORY * 2):]
 
def extract_facts(memory: dict, user_msg: str, assistant_msg: str) -> None:
    """
    Simple heuristic: look for self-referential statements and preferences
    and store them as facts so the AI remembers across sessions.
    """
    triggers = [
        "my name is", "i am", "i'm", "i live", "i work", "i use",
        "i prefer", "i like", "i hate", "i always", "i never",
        "remember that", "remember:", "note that", "don't forget",
    ]
    for line in (user_msg + " " + assistant_msg).lower().split("."):
        if any(t in line for t in triggers):
            fact = line.strip().capitalize()
            if fact and fact not in memory["facts"]:
                memory["facts"].append(fact)
    # Trim to max
    memory["facts"] = memory["facts"][-MAX_FACTS:]
 
def memory_summary(memory: dict) -> str:
    """Build a concise summary string to inject into the system prompt."""
    parts = []
    if memory["facts"]:
        parts.append("Facts you know about the user:\n" +
                     "\n".join(f"- {f}" for f in memory["facts"]))
    if memory["history"]:
        lines = []
        for m in memory["history"]:
            role = "User" if m["role"] == "user" else "You"
            lines.append(f"{role}: {m['content'][:200]}")
        parts.append("Recent conversation history:\n" + "\n".join(lines))
    return "\n\n".join(parts) if parts else ""
 
 
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
- Only use tools when the user explicitly asks you to do something on the PC. For conversational questions, just reply in text — do NOT take screenshots or move the mouse.
"""
 
# ── Main agentic loop ──────────────────────────────────────────────────────────
def run():
    print("\n╔══════════════════════════════════════════╗")
    print("║   AI PC Controller — Groq (Free)         ║")
    print("║  Type your command. 'quit' to exit.      ║")
    print("║  Move mouse to top-left corner to abort. ║")
    print("╚══════════════════════════════════════════╝\n")
 
    # Load persistent memory
    memory = load_memory()
    if memory["facts"] or memory["history"]:
        print(f"  [memory] Loaded {len(memory['facts'])} fact(s), "
              f"{len(memory['history'])} past message(s).\n")
 
    def build_system_message() -> str:
        summary = memory_summary(memory)
        if summary:
            return SYSTEM_PROMPT + "\n\n--- YOUR MEMORY ---\n" + summary + "\n-------------------"
        return SYSTEM_PROMPT
 
    messages = [{"role": "system", "content": build_system_message()}]
 
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            save_memory(memory)
            break
 
        if not user_input:
            continue
 
        # Memory management commands
        if user_input.lower() in ("quit", "exit", "q"):
            save_memory(memory)
            print("Goodbye!")
            break
        if user_input.lower() in ("memory", "show memory"):
            summary = memory_summary(memory)
            print("\n" + (summary if summary else "(memory is empty)") + "\n")
            continue
        if user_input.lower() in ("clear memory", "forget everything"):
            memory = {"facts": [], "history": []}
            save_memory(memory)
            print("  [memory] Cleared.\n")
            continue
 
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
                print(f"\nAPI error (retrying without tools): {e}\n")
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    max_tokens=4096,
                )
 
            msg = response.choices[0].message
            messages.append(msg)  # groq message objects are serialisable
 
            # Print any text the model produced
            if msg.content and msg.content.strip():
                reply_text = msg.content.strip()
                print(f"\nAssistant: {reply_text}\n")
 
                # No tool calls → end of turn; save to memory
                if not msg.tool_calls:
                    update_history(memory, "user", user_input)
                    update_history(memory, "assistant", reply_text)
                    extract_facts(memory, user_input, reply_text)
                    save_memory(memory)
                    # Refresh system message with updated memory for next turn
                    messages[0] = {"role": "system", "content": build_system_message()}
 
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
 
                print(f"  → [{fn_name}] {json.dumps(fn_args)}")
                result = execute_tool(fn_name, fn_args)
                display = "[image data]" if result.startswith("SCREENSHOT_B64:") else result
                print(f"  ← {display[:200]}")

                if result.startswith("SCREENSHOT_B64:"):
                    b64 = result[len("SCREENSHOT_B64:"):]
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": "Screenshot taken."})
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            {"type": "text", "text": "This is the screenshot. Describe what you see."}
                        ]
                    })
                else:
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
 
 
if __name__ == "__main__":
    run()
