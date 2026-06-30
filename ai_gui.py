import os
import sys
import json
import time
import shutil
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pyautogui
import pygetwindow as gw
from groq import Groq

# ── Safety ─────────────────────────────────────────────────────────────────────
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

# ── Groq client ────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("GROQ_API_KEY", "gsk_YOUR-GROQ-API-KEY")
client = Groq(api_key="gsk_YOUR-GROK-API-KEY")  # Replace with your Groq API key or set GROQ_API_KEY
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ── Tools ──────────────────────────────────────────────────────
TOOLS = [
    {"type":"function","function":{"name":"mouse_click","description":"Click the mouse at given screen coordinates.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"},"button":{"type":"string","enum":["left","right","double"]}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"mouse_move","description":"Move the mouse to a position.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"}},"required":["x","y"]}}},
    {"type":"function","function":{"name":"mouse_scroll","description":"Scroll at a screen position.","parameters":{"type":"object","properties":{"x":{"type":"integer"},"y":{"type":"integer"},"clicks":{"type":"integer"}},"required":["x","y","clicks"]}}},
    {"type":"function","function":{"name":"keyboard_type","description":"Type text.","parameters":{"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}}},
    {"type":"function","function":{"name":"keyboard_hotkey","description":"Press a keyboard shortcut.","parameters":{"type":"object","properties":{"keys":{"type":"array","items":{"type":"string"}}},"required":["keys"]}}},
    {"type":"function","function":{"name":"keyboard_press","description":"Press a single key.","parameters":{"type":"object","properties":{"key":{"type":"string"}},"required":["key"]}}},
    {"type":"function","function":{"name":"get_screen_size","description":"Returns screen resolution.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"take_screenshot","description":"Takes a screenshot.","parameters":{"type":"object","properties":{"path":{"type":"string"}}}}},
    {"type":"function","function":{"name":"list_windows","description":"Lists open windows.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"focus_window","description":"Focus a window by title.","parameters":{"type":"object","properties":{"title":{"type":"string"}},"required":["title"]}}},
    {"type":"function","function":{"name":"close_window","description":"Close a window by title.","parameters":{"type":"object","properties":{"title":{"type":"string"}},"required":["title"]}}},
    {"type":"function","function":{"name":"launch_app","description":"Launch an app, file, or URL.","parameters":{"type":"object","properties":{"target":{"type":"string"}},"required":["target"]}}},
    {"type":"function","function":{"name":"run_command","description":"Run a shell command.","parameters":{"type":"object","properties":{"command":{"type":"string"},"timeout":{"type":"integer"}},"required":["command"]}}},
    {"type":"function","function":{"name":"file_list","description":"List files in a directory.","parameters":{"type":"object","properties":{"path":{"type":"string"}}}}},
    {"type":"function","function":{"name":"file_read","description":"Read a text file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"file_write","description":"Write a text file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"file_copy","description":"Copy a file.","parameters":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}}},
    {"type":"function","function":{"name":"file_move","description":"Move a file.","parameters":{"type":"object","properties":{"source":{"type":"string"},"destination":{"type":"string"}},"required":["source","destination"]}}},
    {"type":"function","function":{"name":"file_delete","description":"Delete a file.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"file_create_dir","description":"Create a directory.","parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}}},
    {"type":"function","function":{"name":"wait","description":"Pause for seconds.","parameters":{"type":"object","properties":{"seconds":{"type":"number"}},"required":["seconds"]}}},
]

def execute_tool(name, inputs):
    try:
        if name == "mouse_click":
            x, y, btn = inputs["x"], inputs["y"], inputs.get("button", "left")
            if btn == "double": pyautogui.doubleClick(x, y)
            elif btn == "right": pyautogui.rightClick(x, y)
            else: pyautogui.click(x, y)
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
            matches = gw.getWindowsWithTitle(title) or [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            if not matches: return f"No window found matching '{title}'"
            matches[0].activate(); time.sleep(0.3)
            return f"Focused: {matches[0].title}"
        elif name == "close_window":
            title = inputs["title"]
            matches = gw.getWindowsWithTitle(title) or [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
            if not matches: return f"No window found matching '{title}'"
            matches[0].close()
            return f"Closed: {matches[0].title}"
        elif name == "launch_app":
            target = inputs["target"]
            if platform.system() == "Windows": os.startfile(target)
            elif platform.system() == "Darwin": subprocess.Popen(["open", target])
            else: subprocess.Popen(["xdg-open", target])
            return f"Launched: {target}"
        elif name == "run_command":
            r = subprocess.run(inputs["command"], shell=True, capture_output=True, text=True, timeout=inputs.get("timeout", 10))
            return (r.stdout or r.stderr or "(no output)")[:2000]
        elif name == "file_list":
            path = inputs.get("path", ".")
            entries = os.listdir(path)
            return "\n".join(f"[{'DIR' if os.path.isdir(os.path.join(path,e)) else 'FILE'}] {e}" for e in sorted(entries)) or "(empty)"
        elif name == "file_read":
            with open(inputs["path"], "r", encoding="utf-8", errors="replace") as f: return f.read(8000)
        elif name == "file_write":
            with open(inputs["path"], "w", encoding="utf-8") as f: f.write(inputs["content"])
            return f"Written to: {inputs['path']}"
        elif name == "file_copy":
            src, dst = inputs["source"], inputs["destination"]
            shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
            return f"Copied {src} → {dst}"
        elif name == "file_move":
            shutil.move(inputs["source"], inputs["destination"])
            return f"Moved {inputs['source']} → {inputs['destination']}"
        elif name == "file_delete":
            path = inputs["path"]
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
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

# ── Memory ─────────────────────────────────────────────────────────────────────
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
MAX_HISTORY, MAX_FACTS = 10, 30

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"facts": [], "history": []}

def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False, default=str)
    except: pass

def update_history(memory, role, content):
    memory["history"].append({"role": role, "content": content})
    if len(memory["history"]) > MAX_HISTORY * 2:
        memory["history"] = memory["history"][-(MAX_HISTORY * 2):]

def extract_facts(memory, user_msg, assistant_msg):
    triggers = ["my name is","i am","i'm","i live","i work","i use","i prefer","i like","i hate","i always","i never","remember that","remember:","note that","don't forget"]
    for line in (user_msg + " " + assistant_msg).lower().split("."):
        if any(t in line for t in triggers):
            fact = line.strip().capitalize()
            if fact and fact not in memory["facts"]:
                memory["facts"].append(fact)
    memory["facts"] = memory["facts"][-MAX_FACTS:]

def memory_summary(memory):
    parts = []
    if memory["facts"]:
        parts.append("Facts you know about the user:\n" + "\n".join(f"- {f}" for f in memory["facts"]))
    if memory["history"]:
        lines = [f"{'User' if m['role']=='user' else 'You'}: {m['content'][:200]}" for m in memory["history"]]
        parts.append("Recent conversation history:\n" + "\n".join(lines))
    return "\n\n".join(parts) if parts else ""

SYSTEM_PROMPT = f"""You are an AI assistant that controls a {platform.system()} computer on behalf of the user.
You have tools for mouse control, keyboard input, screenshots, window management, app launching, shell commands, and file operations.
Guidelines:
- Break complex tasks into sequential tool calls.
- For GUI interactions, take a screenshot first to see the current screen.
- Always confirm with the user before deleting files or running destructive commands.
- Be concise — briefly explain what you're doing and why.
- If something fails, try an alternative approach.
- Only use tools when the user explicitly asks you to do something on the PC. For conversational questions, just reply in text.
"""

# ── GUI ────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI PC Controller")
        self.geometry("900x650")
        self.minsize(600, 400)
        self.configure(bg="#0f0f13")

        self.memory = load_memory()
        self.messages = [{"role": "system", "content": self._sys_msg()}]
        self.busy = False

        self._build_ui()
        self._log_system(f"Loaded {len(self.memory['facts'])} fact(s), {len(self.memory['history'])} past message(s).")
        self._log_system("Type a command and press Enter or click Send.")

    def _sys_msg(self):
        summary = memory_summary(self.memory)
        return SYSTEM_PROMPT + ("\n\n--- YOUR MEMORY ---\n" + summary + "\n-------------------" if summary else "")

    def _build_ui(self):
        # ── Top bar ──
        topbar = tk.Frame(self, bg="#0f0f13", pady=8)
        topbar.pack(fill="x", padx=12)

        tk.Label(topbar, text="AI PC Controller", font=("Segoe UI", 14, "bold"),
                 fg="#a78bfa", bg="#0f0f13").pack(side="left")

        btn_frame = tk.Frame(topbar, bg="#0f0f13")
        btn_frame.pack(side="right")
        for label, cmd in [("Memory", self._show_memory), ("Clear Memory", self._clear_memory), ("Clear Chat", self._clear_chat)]:
            tk.Button(btn_frame, text=label, command=cmd,
                      bg="#1e1e2e", fg="#94a3b8", relief="flat",
                      font=("Segoe UI", 9), padx=10, pady=4,
                      activebackground="#2d2d44", activeforeground="#e2e8f0",
                      cursor="hand2").pack(side="left", padx=3)

        # ── Chat area ──
        chat_frame = tk.Frame(self, bg="#0f0f13")
        chat_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.chat = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, state="disabled",
            bg="#0d0d17", fg="#e2e8f0", font=("Consolas", 10),
            relief="flat", bd=0, padx=12, pady=10,
            insertbackground="#a78bfa",
            selectbackground="#3730a3"
        )
        self.chat.pack(fill="both", expand=True)

        # Tags
        self.chat.tag_config("system",   foreground="#475569", font=("Consolas", 9, "italic"))
        self.chat.tag_config("user",     foreground="#a78bfa", font=("Consolas", 10, "bold"))
        self.chat.tag_config("assistant",foreground="#34d399", font=("Consolas", 10))
        self.chat.tag_config("tool_call",foreground="#fbbf24", font=("Consolas", 9))
        self.chat.tag_config("tool_res", foreground="#64748b", font=("Consolas", 9))
        self.chat.tag_config("error",    foreground="#f87171", font=("Consolas", 10))

        # ── Status bar ──
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self, textvariable=self.status_var, bg="#0f0f13",
                          fg="#475569", font=("Segoe UI", 9), anchor="w")
        status.pack(fill="x", padx=14, pady=(0, 4))

        # ── Input bar ──
        input_frame = tk.Frame(self, bg="#1e1e2e", pady=8, padx=10)
        input_frame.pack(fill="x", padx=12, pady=(0, 12))
        input_frame.columnconfigure(0, weight=1)

        self.entry = tk.Text(input_frame, height=2, bg="#1e1e2e", fg="#e2e8f0",
                             font=("Consolas", 11), relief="flat", bd=0,
                             insertbackground="#a78bfa", wrap=tk.WORD)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(4, 8))
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)

        self.send_btn = tk.Button(input_frame, text="Send ▶", command=self._send,
                                  bg="#7c3aed", fg="white", relief="flat",
                                  font=("Segoe UI", 10, "bold"), padx=14, pady=6,
                                  activebackground="#6d28d9", activeforeground="white",
                                  cursor="hand2")
        self.send_btn.grid(row=0, column=1)

        self.entry.focus()

    def _log(self, text, tag=""):
        self.chat.configure(state="normal")
        self.chat.insert("end", text, tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _log_system(self, msg):   self._log(f"[system] {msg}\n", "system")
    def _log_user(self, msg):     self._log(f"\nYou: {msg}\n", "user")
    def _log_assistant(self, msg):self._log(f"\nAssistant: {msg}\n", "assistant")
    def _log_tool(self, name, args, result):
        self._log(f"  → [{name}] {args}\n", "tool_call")
        self._log(f"  ← {result[:200]}\n", "tool_res")

    def _on_enter(self, event):
        if not event.state & 0x1:  # Shift not held
            self._send()
            return "break"

    def _send(self):
        if self.busy: return
        user_input = self.entry.get("1.0", "end").strip()
        if not user_input: return
        self.entry.delete("1.0", "end")

        # Special commands
        if user_input.lower() in ("memory", "show memory"):
            self._show_memory(); return
        if user_input.lower() in ("clear memory", "forget everything"):
            self._clear_memory(); return

        self._log_user(user_input)
        self.messages.append({"role": "user", "content": user_input})
        self.busy = True
        self.send_btn.configure(state="disabled", text="...")
        self.status_var.set("Thinking…")
        threading.Thread(target=self._agent_loop, args=(user_input,), daemon=True).start()

    def _agent_loop(self, user_input):
        try:
            while True:
                try:
                    response = client.chat.completions.create(
                        model=MODEL, messages=self.messages,
                        tools=TOOLS, tool_choice="auto", max_tokens=4096)
                except Exception as e:
                    response = client.chat.completions.create(
                        model=MODEL, messages=self.messages, max_tokens=4096)

                msg = response.choices[0].message
                self.messages.append(msg)

                if msg.content and msg.content.strip():
                    reply = msg.content.strip()
                    self.after(0, self._log_assistant, reply)
                    if not msg.tool_calls:
                        update_history(self.memory, "user", user_input)
                        update_history(self.memory, "assistant", reply)
                        extract_facts(self.memory, user_input, reply)
                        save_memory(self.memory)
                        self.messages[0] = {"role": "system", "content": self._sys_msg()}

                if not msg.tool_calls:
                    break

                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try: fn_args = json.loads(tc.function.arguments)
                    except: fn_args = {}
                    self.after(0, lambda n=fn_name: self.status_var.set(f"Running: {n}…"))
                    result = execute_tool(fn_name, fn_args)
                    display_result = "[image data]" if result.startswith("SCREENSHOT_B64:") else result
                    self.after(0, self._log_tool, fn_name, json.dumps(fn_args), display_result)
                    if isinstance(result, str) and result.startswith("SCREENSHOT_B64:"):
                        b64 = result[len("SCREENSHOT_B64:"):]
                        self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": "Screenshot taken, see next message."})
                        self.messages.append({
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                {"type": "text", "text": "This is the screenshot. Respond to the user based on this image."}
                            ]
                        })
                    else:
                        self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        except Exception as e:
            self.after(0, self._log, f"\nError: {e}\n", "error")
        finally:
            self.after(0, self._done)

    def _done(self):
        self.busy = False
        self.send_btn.configure(state="normal", text="Send ->")
        self.status_var.set("Ready")

    def _show_memory(self):
        summary = memory_summary(self.memory)
        win = tk.Toplevel(self)
        win.title("Memory")
        win.geometry("500x400")
        win.configure(bg="#0f0f13")
        txt = scrolledtext.ScrolledText(win, bg="#0d0d17", fg="#94a3b8", font=("Consolas", 10), relief="flat", padx=10, pady=10)
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", summary if summary else "(memory is empty)")
        txt.configure(state="disabled")

    def _clear_memory(self):
        if messagebox.askyesno("Clear Memory", "Wipe all memory? This cannot be undone."):
            self.memory = {"facts": [], "history": []}
            save_memory(self.memory)
            self.messages[0] = {"role": "system", "content": self._sys_msg()}
            self._log_system("Memory cleared.")

    def _clear_chat(self):
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self._log_system("Chat cleared.")

    def on_close(self):
        save_memory(self.memory)
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
