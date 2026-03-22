# FlowNote Testing Plan

## Prerequisites

```bash
# Install test dependencies
pip install -r notes_tool/requirements.txt

# Start Ollama
ollama serve

# Verify tesseract installed
tesseract --version
```

---

## Test Case 1: Application Launch

### TC-001: Normal Launch
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run `python notes_tool/run.py` | GUI window appears in top-right corner |
| 2 | Check system tray | FlowNote icon visible with gray (idle) color |
| 3 | Check status indicator | Shows "Ready" in gray |
| 4 | Check terminal | No error messages |

### TC-002: Ollama Not Running
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Stop Ollama: `pkill ollama` | - |
| 2 | Run `python notes_tool/run.py` | Error dialog: "Ollama is not running" |
| 3 | Click OK | App exits cleanly |
| 4 | Restart Ollama: `ollama serve` | Ollama running again |

---

## Test Case 2: Clipboard Capture

### TC-003: Text Clipboard Capture
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy text: "Machine learning uses algorithms to learn from data" | Text copied |
| 2 | Press `Ctrl+Shift+S` | Status: CAPTURING (blue) |
| 3 | Wait 2-3 seconds | Status: PROCESSING (yellow) |
| 4 | Wait for completion | Status: SAVED (green), preview shows bullet points |
| 5 | Check file: `notes/YYYY-MM-DD.md` | Note appended with bullet format |

### TC-004: Empty Clipboard Capture
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Clear clipboard | Clipboard empty |
| 2 | Press `Ctrl+Shift+S` | Status shows error or empty message |
| 3 | Check notes file | No new content added |

### TC-005: URL in Clipboard
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy URL: `https://en.wikipedia.org/wiki/Machine_learning` | URL copied |
| 2 | Press `Ctrl+Shift+S` | Status: CAPTURING |
| 3 | Wait for URL fetch + AI | AI processes page content |
| 4 | Check preview | Shows notes about the page topic |

---

## Test Case 3: Screenshot Capture

### TC-006: Screenshot with OCR
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open a webpage with text | Text visible on screen |
| 2 | Press `Ctrl+Shift+S` (or tray → Capture Screenshot) | Screen captured |
| 3 | Wait for OCR + AI | Status shows PROCESSING |
| 4 | Check preview | Shows extracted text as bullets |

### TC-007: Screenshot with No Text
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open blank window / image-only page | No readable text |
| 2 | Capture screenshot | Status shows warning or error |
| 3 | Check notes file | No content or minimal content |

---

## Test Case 4: System Tray

### TC-008: Tray Icon Visibility
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run app | Tray icon appears |
| 2 | Hover over icon | Tooltip shows "FlowNote - Ready" |
| 3 | Check icon color | Gray circle |

### TC-009: Tray Context Menu
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Right-click tray icon | Menu appears |
| 2 | Click "Capture Clipboard" | Capture starts |
| 3 | Click "Show Window" | Window appears |
| 4 | Click "Quit" | App closes, tray icon disappears |

### TC-010: Tray Click Toggle
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Window visible | Click tray icon once |
| 2 | Observe | Window hides |
| 3 | Click tray icon again | Window shows again |

---

## Test Case 5: GUI Overlay

### TC-011: Window Drag
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click and hold title bar | Window can be dragged |
| 2 | Release | Window stays at new position |

### TC-012: Close Button
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click × button | Window hides, app still running |
| 2 | Check tray icon | Still visible |

### TC-013: Status Indicator Colors
| Step | Trigger | Expected Color |
|------|---------|----------------|
| 1 | Idle | Gray |
| 2 | Press hotkey | Blue (Capturing) |
| 3 | AI processing | Yellow (Processing) |
| 4 | Success | Green (Saved) |
| 5 | Error | Red (Error) |

---

## Test Case 6: Hotkey

### TC-014: Hotkey Trigger
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Focus another window | FlowNote window not focused |
| 2 | Press `Ctrl+Shift+S` | Capture triggers from any app |
| 3 | Observe | Status changes, note saved |

### TC-015: Debounce
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Press `Ctrl+Shift+S` | Capture starts |
| 2 | Press again within 1 second | Nothing happens |
| 3 | Wait 2 seconds, press again | Capture triggers again |

### TC-016: Custom Hotkey
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Edit `config/settings.yaml`: `"hotkey": "ctrl+alt+n"` | - |
| 2 | Restart app | New hotkey active |
| 3 | Press `Ctrl+Alt+N` | Capture triggers |

---

## Test Case 7: Configuration

### TC-017: Model Override
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set `OLLAMA_MODEL=mistral` in .env | - |
| 2 | Restart app | Uses mistral model |
| 3 | Check logs | "Using model: mistral" |

### TC-018: Notes Path Override
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Set `NOTES_PATH=/tmp/test_notes` in .env | - |
| 2 | Restart app | Notes saved to /tmp/test_notes |

---

## Test Case 8: File Storage

### TC-019: Daily Note Creation
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run app | - |
| 2 | Create 3 notes | - |
| 3 | Check file: `notes/2026-03-22.md` | Contains all 3 notes |
| 4 | Check format | Proper Markdown with headers |

### TC-020: Multiple Sessions
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Create note on Day 1 | Saved to `notes/2026-03-22.md` |
| 2 | Change system date to Day 2 | - |
| 3 | Create note | Saved to `notes/2026-03-23.md` |

---

## Edge Cases

### EC-001: Very Long Text
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy 10,000+ word article | - |
| 2 | Capture | AI processes, returns condensed bullets |
| 3 | Check preview | Truncated or scrollable |

### EC-002: Non-ASCII Characters
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy: "日本語テスト 中文测试 한국어" | - |
| 2 | Capture | Processes without crash |

### EC-003: Special Characters
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy: `{"key": "value", "array": [1,2,3]}` | - |
| 2 | Capture | JSON preserved in notes |

### EC-004: Network Timeout
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Copy URL to slow site | - |
| 2 | Capture | Timeout after 15s (configurable) |
| 3 | Check status | Error shown, no crash |

### EC-005: Ollama Crash During Processing
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Start capture | Processing status |
| 2 | Kill ollama: `pkill ollama` | - |
| 3 | Wait | Error status shown |
| 4 | Restart ollama: `ollama serve` | App continues working |

### EC-006: Rapid Hotkey Presses
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Press hotkey 10 times rapidly | Only 2-3 captures triggered (debounce) |
| 2 | Check notes | 2-3 notes added |

---

## Failure Scenarios

### FS-001: Tesseract Not Installed
```
Symptom: Screenshot capture fails silently
Fix: sudo apt install tesseract-ocr  # Ubuntu
     brew install tesseract           # macOS
```

### FS-002: Keyboard Library Conflict
```
Symptom: Hotkey not triggering, no error
Cause: Another app is capturing the hotkey
Fix: Close other apps using similar shortcuts
```

### FS-003: PyQt6 Display Error (Linux)
```
Symptom: "QWidget: Cannot create a QApplication"
Cause: No display server
Fix: export DISPLAY=:0
```

### FS-004: Permission Denied (Notes Directory)
```
Symptom: "Cannot save notes"
Cause: No write permission
Fix: chmod 755 notes/ or chown user:user notes/
```

### FS-005: Model Not Found
```
Symptom: Ollama returns error
Cause: Config model not installed
Fix: ollama pull llama3
```

---

## Debug Checklist

### Before Testing
- [ ] `pip list | grep -E "PyQt6|requests|pyperclip|pytesseract|keyboard"` — all installed
- [ ] `ollama list` — shows installed models
- [ ] `tesseract --version` — tesseract available
- [ ] `notes/` directory exists and writable

### During Testing
- [ ] Terminal shows no Python tracebacks
- [ ] `journalctl --user -f` — check for systemd errors (if using)
- [ ] Watch logs with `tail -f notes/*.md` for file writes

### Common Issues
| Issue | Debug Command | Fix |
|-------|--------------|-----|
| Hotkey not working | `python -c "import keyboard; print(keyboard.is_pressed('ctrl+shift+s'))"` | Run as sudo or check permissions |
| OCR returns empty | `tesseract test.png stdout` | Reinstall tesseract |
| AI timeout | Check `curl http://localhost:11434/api/tags` | Restart ollama |
| Tray icon missing | `echo $DISPLAY` | Set DISPLAY variable |

### Log Locations
- Python stdout/stderr (terminal)
- `notes/` — markdown output
- `~/.cache/flownote/` — if implemented

---

## Test Summary Matrix

| Feature | TC Range | Must Pass |
|---------|----------|-----------|
| App Launch | TC-001, TC-002 | Yes |
| Clipboard Capture | TC-003, TC-004, TC-005 | Yes |
| Screenshot Capture | TC-006, TC-007 | Yes |
| System Tray | TC-008, TC-009, TC-010 | Yes |
| GUI Overlay | TC-011, TC-012, TC-013 | Yes |
| Hotkey | TC-014, TC-015, TC-016 | Yes |
| Configuration | TC-017, TC-018 | Yes |
| File Storage | TC-019, TC-020 | Yes |
| Edge Cases | EC-001 to EC-006 | If possible |
| Failure Handling | FS-001 to FS-005 | Yes |

---

## Quick Smoke Test (2 minutes)

```bash
# 1. Start app
python notes_tool/run.py &
sleep 2

# 2. Check tray
# Should see FlowNote icon

# 3. Test capture
echo "Test content for notes" | xclip
sleep 1
xdotool key ctrl+shift+s
sleep 5

# 4. Check result
cat notes/$(date +%Y-%m-%d).md | grep "Test content"

# 5. Clean up
pkill -f "python notes_tool/run.py"
```

**Expected:** Note appears in daily file with bullet points.
