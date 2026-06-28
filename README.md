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

---

## Usage

```bash
python ai.py
```

Then just type what you want in plain English:

```
You: Open Notepad and write Hello World
You: Take a screenshot and tell me what's on screen
You: List the files in my Downloads folder
You: Close Chrome
You: What's my IP address?
```

---

## Safety

- **Failsafe** — move your mouse to the **top-left corner** of the screen at any time to instantly stop all actions
- **Destructive actions** — the AI will ask for confirmation before deleting files or running dangerous commands
- **API errors** — if Groq returns a bad response, the script retries automatically in plain text mode

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `GroqError: api_key must be set` | Hardcode your key in `ai.py` as shown above |
| `BadRequestError: tool call validation failed` | Wrap the API call in a try/except (see below) |
| Window not found | Use the exact process name, e.g. `cs2.exe` not `csgo.exe` |
| Mouse moves to wrong place | Run `get_screen_size` first, or take a screenshot so the AI can orient itself |

---

## How It Works

```
You type a command
       ↓
Llama 3.3 70B (via Groq) decides which tools to call
       ↓
ai.py executes the tools on your PC (pyautogui, subprocess, os...)
       ↓
Results are sent back to the model
       ↓
Model responds or calls more tools until the task is done
```

---

## Limitations

- GUI interactions (clicking buttons) require a screenshot first so the AI knows where things are
- The AI cannot see the screen in real time — it takes a screenshot on demand
- Groq free tier has rate limits (but they are generous for personal use)
- Window title matching may differ from the actual process name

---

## License

MIT — do whatever you want with it.
