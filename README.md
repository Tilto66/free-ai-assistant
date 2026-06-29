# AI PC Controller — GUI Version

A dark-themed desktop GUI for [AI PC Controller](https://github.com/Tilto66/ai-pc-controller), powered by **Groq's free API** and **Llama 4 Scout** (vision-capable).

---

## What's New vs the CLI

| Feature | CLI (`ai.py`) | GUI (`ai_gui.py`) |
|---|---|---|
| Interface | Terminal | Desktop window |
| Color-coded output | ❌ | ✅ |
| Memory viewer | Type `memory` | Button in toolbar |

---

## Requirements

- Python 3.9+
- A free [Groq API key](https://console.groq.com)

---

## Installation

```bash
pip install groq pyautogui pygetwindow pillow
```

---

## Setup

1. Get a free API key at **https://console.groq.com** → API Keys → Create API Key

2. Set it as an environment variable:

```bash
# Windows
set GROQ_API_KEY=gsk_your_key_here
```

Or hardcode it directly in `ai_gui.py` line 20:

```python
API_KEY = "gsk_your_key_here"
```

3. Run:

```bash
python ai_gui.py
```

---

## Usage

Type a command in the input box and press **Enter** to send. Use **Shift+Enter** for a newline.

### Examples

```
Take a screenshot and tell me what's on screen
Open Notepad and type Hello World
List all open windows
What's my IP address?
Copy report.pdf from Downloads to Desktop
Close Chrome
```

### Toolbar Buttons

| Button | Action |
|---|---|
| **Memory** | View everything the AI remembers about you |
| **Clear Memory** | Wipe the memory file |
| **Clear Chat** | Clear the chat display (memory is kept) |

### Chat Colors

| Color | Meaning |
|---|---|
| 🟣 Purple | Your message |
| 🟢 Green | Assistant reply |
| 🟡 Yellow | Tool call |
| ⚫ Gray | Tool result |
| 🔴 Red | Error |

---

## Vision / Screenshots

The GUI version uses **Llama 4 Scout** (`meta-llama/llama-4-scout-17b-16e-instruct`), a free vision model on Groq. When you ask the AI to take a screenshot, it actually sees the image and can describe or act on what's there.

---

## Memory

The assistant saves a `memory.json` file next to `ai_gui.py`. It stores:

- **Facts** — things you tell it about yourself (name, preferences, habits). Up to 50.
- **History** — the last 20 conversation exchanges for context across sessions.

The memory file is plain JSON — you can open and edit it manually at any time.

---

## Safety

- **Failsafe** — move your mouse to the **top-left corner** of the screen to instantly stop all pyautogui actions
- **Destructive actions** — the AI asks for confirmation before deleting files or running dangerous shell commands
- **API errors** — if Groq returns an error, the script retries in plain text mode instead of crashing

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Invalid API Key` | Set `GROQ_API_KEY` or hardcode the key in `ai_gui.py` |
| Screenshot fails | Make sure you're not running in a headless environment |
| Window not found | Use the exact process name, e.g. `cs2.exe` not `csgo.exe` |

---

## License

MIT — same as the original project.
