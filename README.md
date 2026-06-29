# AI PC Controller

Control your Windows PC with natural language commands, powered by **Groq's free API** and **Llama 3.3 70B**.

---

## Features

-  **Mouse control** — click, right-click, double-click, move, scroll
-  **Keyboard input** — type text, hotkeys (Ctrl+C, Alt+F4…), special keys
-  **Screenshot** — capture the screen so the AI can see what's on it
-  **Window management** — list, focus, or close open windows
-  **App launching** — open apps, files, or URLs
-  **Shell commands** — run any terminal command and get the output
-  **File operations** — list, read, write, copy, move, delete, create folders
-  **Memory** — remembers facts about you and recent conversations across sessions

---

## Requirements

- Python 3.9+
- A free [Groq API key](https://console.groq.com)

---

## Installation

```bash
pip install groq pyautogui pygetwindow
```

---

## Setup

1. Sign up for free at **https://console.groq.com**
2. Go to **API Keys** → **Create API Key**
3. Open `ai.py` and replace line 33 with your key:

```python
client = Groq(api_key="gsk_YOUR_KEY_HERE")
```

4. Run it:

```bash
python ai.py
```

---

## Commands You Can Give

###  Mouse & Keyboard
```
You: Click on the search bar
You: Right-click on the desktop
You: Double-click the recycle bin
You: Press Ctrl+C
You: Press Alt+F4
You: Type "Hello World" in Notepad
You: Scroll down on the page
You: Press the Enter key
```

###  Screen & Vision
```
You: Take a screenshot and tell me what's on screen
You: What's currently open on my screen?
You: Screenshot and describe the taskbar
```
> The AI cannot see your screen in real time — it takes a screenshot on demand and analyses it.

###  Window Management
```
You: List all open windows
You: Focus Chrome
You: Close Notepad
You: Switch to Visual Studio Code
You: Close cs2.exe
```
> Use the real process name — CS2 is `cs2.exe`, not `csgo.exe`.

###  Launching Apps & URLs
```
You: Open Notepad
You: Launch Chrome
You: Open https://google.com
You: Open C:\Users\Tilto66\Documents\report.pdf
You: Start Task Manager
```

###  Shell Commands
```
You: What's my IP address?
You: Show running processes
You: How much disk space do I have left?
You: Kill the cs2.exe process
You: Run ipconfig and show me the result
You: What's my PC's hostname?
```

###  File Operations
```
You: List the files in my Downloads folder
You: Read the file C:\Users\Tilto66\notes.txt
You: Create a folder called Projects on my Desktop
You: Copy report.pdf from Downloads to Desktop
You: Rename vacation.jpg to holiday.jpg
You: Delete the file temp.txt
You: Write "Hello" to a new file called test.txt
```
> The AI will ask for confirmation before deleting files.

###  Memory Commands
```
You: my name is Tilto66
You: I prefer dark mode
You: remember that I use VS Code
You: I always keep files on C:\Users\Tilto66\Desktop
```

Special built-in commands:
```
memory            → shows everything the AI currently remembers
clear memory      → wipes the memory file completely
quit / exit / q   → saves memory and exits
```

### 💬 General Chat
```
You: What can you do?
You: Do you remember my name?
You: What did I ask you last time?
```
> For plain questions like these, the AI replies directly without using any PC tools.

---

## Memory System

The assistant saves a `memory.json` file next to `ai.py`. It stores two things:

- **Facts** — things you tell it about yourself (name, preferences, habits). Up to 50 facts.
- **History** — the last 20 conversation exchanges so it has context when you relaunch.

This means the AI will remember you across sessions — even after restarting your PC.

**Example across two sessions:**
```
Session 1:
  You: my name is Tilto66
  You: I always keep my projects in C:\Dev

Session 2 (next day):
  You: where do I keep my projects?
  Assistant: In C:\Dev, as you mentioned before.
```

The memory file is plain JSON — you can open and edit `memory.json` manually at any time.

---

## How It Works

```
┌──────────────────────────────────────────────────┐
│               You type a command                  │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│  Memory injected into the system prompt           │
│  (your name, preferences, recent history)         │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│  Llama 3.3 70B via Groq reads your command        │
│  and decides which tools to call                  │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│  ai.py executes tools locally on your PC:         │
│  pyautogui    → mouse & keyboard                  │
│  pygetwindow  → window management                 │
│  subprocess   → shell commands                    │
│  os / shutil  → file operations                   │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│  Results sent back to the model                   │
│  Model replies or calls more tools                │
│  until the task is complete                       │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────┐
│  Conversation + new facts saved to memory.json    │
└──────────────────────────────────────────────────┘
```

### What a tool call looks like under the hood

When you type `Open Notepad and type Hello World`, here is what actually runs:

```
→ [launch_app]      {"target": "notepad"}
← Launched: notepad

→ [wait]            {"seconds": 1}
← Waited 1s

→ [take_screenshot] {}
← Screenshot saved to: screenshot.png

→ [mouse_click]     {"x": 640, "y": 400, "button": "left"}
← Clicked (640, 400) [left]

→ [keyboard_type]   {"text": "Hello World"}
← Typed: 'Hello World'
```

The model loops through tool calls until it decides the task is done, then gives you a plain text reply.

---

## Safety

- **Failsafe** — move your mouse to the **top-left corner** of the screen at any time to instantly stop all actions (built into pyautogui)
- **Destructive actions** — the AI asks for confirmation before deleting files or running dangerous shell commands
- **API errors** — if Groq returns a malformed tool call (400 error), the script automatically retries in plain text mode instead of crashing

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GroqError: api_key must be set` | Hardcode your key in `ai.py` as shown in Setup |
| `BadRequestError: tool call validation failed` | Wrap the API call in a try/except (already in latest version) |
| Window not found | Use the exact process name, e.g. `cs2.exe` not `csgo.exe` |
| Mouse clicks the wrong spot | Ask the AI to take a screenshot first so it can see the layout |

---

## Limitations

- The AI cannot see your screen in real time — it must take a screenshot on demand
- GUI interactions (clicking buttons) work best when preceded by a screenshot
- Groq free tier has rate limits, but they are very generous for personal use
- Window title matching may not always match the process name exactly
- No linux version for now but maybe one later
- No api key else than Groq

---

## License

MIT — do whatever you want with it but nothing illegal.