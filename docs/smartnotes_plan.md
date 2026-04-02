# SmartNotes — Full Project Plan

**Author:** Apoorv Mani (Anagh)
**Date:** 2026-03-11
**Status:** Planning
**Type:** Standalone tool (Windows, Python)

---

## What It Does

A background tool that captures what's on your screen or what you've selected —
intelligently extracts the important stuff — and appends structured Markdown notes,
all with a single hotkey press. No window switching. No typing. No manual screenshots kept.

---

## Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Screenshot-first? | NO — last resort only | Privacy + speed. Try text extraction first |
| If screenshot needed | Auto-delete after processing | Never stored, exists <2 seconds |
| Model | Local Ollama only | Privacy, offline, free |
| Primary model | `llava-phi3` (3.8B) | Best quality/speed tradeoff on laptop |
| Fast mode model | `moondream2` (1.8B) | Near-instant for quick captures |
| Text-only LLM | `qwen2.5:latest` (already installed) | Summarise selected/extracted text |
| Hotkeys | Two: selected text + full context | Different use cases, same pipeline |
| UI | Silent background + tray icon | No interruption |
| Output | Structured Markdown, date-stamped files | Easy to read, searchable, portable |
| Platform | Windows only (for now) | Win32 APIs for text extraction |

---

## Existing Tools Found (Research)

| Tool | What it does | Gap |
|---|---|---|
| Screenshot_LLM (GitHub) | Watches folder for screenshots → Ollama | No hotkey, no text extraction, no structured notes |
| ollama-ocr (pip, 2k+ stars) | Image → Ollama vision → Markdown/JSON | No hotkey, no text extraction, image-only |
| note-gen (GitHub) | AI Markdown note app | No screen capture, no hotkey |

**Gap confirmed:** No tool combines hotkey + text-first extraction + local Ollama + structured Markdown. This is original.

**Useful:** `ollama-ocr` package — will use this as the vision extraction engine instead of reimplementing.

---

## Input Methods (Priority Order)

The tool tries each method in order, uses the first that works:

```
Hotkey pressed
      │
      ▼
1. CLIPBOARD TRICK (selected text mode)
   User selects text in any app → presses hotkey
   Tool: save clipboard → Ctrl+C → read → restore clipboard
   Works in: browser, PDF, Word, VS Code, terminal, anything
   Needs: pyautogui + pyperclip
   → sends plain text to text LLM (no vision needed)
      │
      │ (if no selection found)
      ▼
2. UI AUTOMATION (active window text)
   Gets focused control via Windows IUIAutomation API
   Reads text via TextPattern / ITextPattern2
   Works in: WPF, WinForms, Qt, browsers (accessibility enabled), Notepad, Word
   Needs: uiautomation (yinkaisheng)
   → sends plain text to text LLM
      │
      │ (if app doesn't expose accessibility tree)
      ▼
3. SCREENSHOT FALLBACK
   mss captures screen → saves to tempfile
   Sends to vision LLM (ollama-ocr / llava-phi3)
   Immediately deletes tempfile in finally block
   Works with: anything visible on screen
   Needs: mss + ollama-ocr
   → sends image to vision LLM → delete image
```

---

## Hotkeys

| Hotkey | Action |
|---|---|
| `Ctrl+Shift+N` | Capture selected text (clipboard trick) |
| `Ctrl+Shift+W` | Capture full active window context (UI automation → screenshot fallback) |
| `Ctrl+Shift+Q` | Quick capture — moondream2, minimal notes, fastest |

All configurable in `config.json`.

---

## Architecture

```
smartnotes.py (entry point — runs forever in background)
      │
      ├── HotkeyListener (pynput GlobalHotKeys)
      │     └── pushes events to Queue (never blocks callback)
      │
      ├── Worker Thread (consumes Queue)
      │     ├── InputDetector
      │     │     ├── ClipboardExtractor   (method 1)
      │     │     ├── UIAutoExtractor      (method 2)
      │     │     └── ScreenshotExtractor  (method 3, fallback)
      │     │
      │     ├── ContextTagger
      │     │     └── gets foreground window title (win32gui)
      │     │         tags source: "Chrome — TryHackMe", "VS Code — main.py"
      │     │
      │     ├── LLMProcessor
      │     │     ├── TextMode  → ollama (qwen2.5:latest)
      │     │     └── VisionMode → ollama-ocr (llava-phi3 / moondream2)
      │     │
      │     └── NoteWriter
      │           └── appends to ~/notes/YYYY-MM-DD/<category>.md
      │
      └── Notifier (plyer)
            └── tray popup: "✓ Note saved → TryHackMe.md"
```

---

## Output Structure

Notes are saved to `~/Documents/SmartNotes/` by default.

### Folder Structure
```
SmartNotes/
├── 2026-03-11/
│   ├── TryHackMe.md
│   ├── Research.md
│   ├── Programming.md
│   └── General.md
├── 2026-03-12/
│   └── ...
└── index.md       ← auto-generated summary of all notes
```

### Category Detection
The LLM auto-detects the category from window title + content:

| Window Title Contains | Category File |
|---|---|
| TryHackMe, HackTheBox, CTF | `CTF.md` |
| arXiv, Scholar, ResearchOS | `Research.md` |
| VS Code, Python, GitHub | `Programming.md` |
| YouTube, tutorial, course | `Study.md` |
| anything else | `General.md` |

### Note Format (inside each .md file)

```markdown
---
## [14:32] Chrome — TryHackMe: Nmap Module
**Source:** Selected text
**Model:** qwen2.5:latest

### Key Points
- `-sV` detects service versions
- `-sC` runs default NSE scripts
- `-p-` scans all 65535 ports
- `-T4` aggressive timing (faster, noisier)

### Commands
```bash
nmap -sV -sC -p- -T4 <target>
```

### Definitions
- **NSE:** Nmap Scripting Engine — extend nmap with Lua scripts

---
```

---

## LLM Prompts

### Text mode (selected text / UI automation)
```
You are a smart note-taking assistant for a cybersecurity student.
Given the following text from the screen, extract ONLY the important information.

Rules:
- Be concise. No filler, no preamble.
- Use Markdown: ## headings, bullet points, code blocks
- Use these sections ONLY if relevant:
  ### Key Points
  ### Commands / Code
  ### Definitions
  ### TODO / Action Items
- If it's a CTF/security topic: prioritise commands, ports, flags, tools
- If it's research/academic: prioritise concepts, methods, findings
- If it's code: preserve exact syntax, add one-line explanation

Text:
{content}
```

### Vision mode (screenshot)
```
You are a smart note-taking assistant for a cybersecurity student.
Look at this screenshot and extract ONLY the important information visible.

Same rules as above. Ignore navigation bars, ads, UI chrome.
Focus on the main content area.
```

---

## Tech Stack

| Component | Library | Install |
|---|---|---|
| Hotkey listener | `pynput` | `pip install pynput` |
| Clipboard | `pyperclip` + `pyautogui` | `pip install pyperclip pyautogui` |
| UI Automation | `uiautomation` | `pip install uiautomation` |
| Screenshot | `mss` | `pip install mss` |
| Vision OCR | `ollama-ocr` | `pip install ollama-ocr` |
| LLM client | `ollama` | `pip install ollama` |
| Window title | `pywin32` | `pip install pywin32` |
| Notifications | `plyer` | `pip install plyer` |
| Tray icon | `pystray` + `Pillow` | `pip install pystray pillow` |
| Config | `json` (stdlib) | — |

### Ollama Models Needed
```bash
ollama pull llava-phi3      # primary vision model (3.8B, best quality/speed)
ollama pull moondream2      # fast vision model (1.8B, quick captures)
# qwen2.5:latest already installed — used for text-only mode
```

---

## File Structure
```
smartnotes/
├── smartnotes.py           # entry point — start this to run
├── config.json             # hotkeys, model, output path (user editable)
├── PLAN.md                 # this file
├── README.md               # setup + usage
├── requirements.txt
└── core/
    ├── __init__.py
    ├── hotkeys.py          # pynput listener + queue
    ├── extractor.py        # input detection (clipboard → uiauto → screenshot)
    ├── llm.py              # ollama text + vision calls
    ├── writer.py           # Markdown output + category detection
    └── notifier.py         # tray icon + plyer notifications
```

---

## Config (`config.json`)
```json
{
  "hotkeys": {
    "selected_text":  "<ctrl>+<shift>+n",
    "full_context":   "<ctrl>+<shift>+w",
    "quick_capture":  "<ctrl>+<shift>+q"
  },
  "models": {
    "text":    "qwen2.5:latest",
    "vision":  "llava-phi3",
    "fast":    "moondream2"
  },
  "output_dir": "~/Documents/SmartNotes",
  "ollama_host": "http://localhost:11434",
  "auto_categorise": true,
  "notify": true
}
```

---

## Build Order

1. `core/hotkeys.py` — listener + queue
2. `core/extractor.py` — clipboard trick first (simplest, test it)
3. `core/llm.py` — text mode with qwen2.5 (no vision yet)
4. `core/writer.py` — Markdown output + folders
5. `core/notifier.py` — tray icon + popup
6. `smartnotes.py` — wire everything together
7. Add UI automation extractor (method 2)
8. Add screenshot fallback + ollama-ocr (method 3)
9. Add category auto-detection
10. Add `config.json` support

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| pynput callback blocking | Use threading.Queue — callback only pushes, worker processes |
| Ctrl+C hijack disturbs clipboard | Save + restore clipboard before/after, 100ms settle time |
| UI automation fails on some apps | Always fallback to screenshot |
| Screenshot privacy | tempfile + immediate delete in finally block |
| llava-phi3 not installed | Check on startup, prompt user to pull |
| Slow vision model | Stream response + notify when done, don't block |
| Hotkey conflicts | Make hotkeys fully configurable in config.json |

---

## Status

- [x] Research complete
- [x] Plan documented
- [ ] Build core/hotkeys.py
- [ ] Build core/extractor.py (clipboard)
- [ ] Build core/llm.py
- [ ] Build core/writer.py
- [ ] Build core/notifier.py
- [ ] Wire smartnotes.py
- [ ] Add UI automation
- [ ] Add screenshot fallback
- [ ] Add config.json
- [ ] Test on TryHackMe
- [ ] Test on arXiv paper
- [ ] Test on VS Code
