<div align="center">
  <img src="https://via.placeholder.com/150/1E1E2E/CDD6F4?text=✦" alt="FlowNote Logo" width="100" height="100"/>
  <h1>FlowNote</h1>
  <p><strong>Intelligent AI-Powered Note Taking Right from Your Desk</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/intro)
  [![Ollama](https://img.shields.io/badge/Ollama-Local_AI-orange?style=for-the-badge)](https://ollama.ai)
</div>

<br/>

## ✨ Introduction

**FlowNote** is a beautifully designed, fast, and local AI-powered note-taking tool. Sitting unobtrusively on your screen as an elegant floating bubble, it lets you generate instantly summarized and formatted notes from text, URLs, and even screenshots! Powered entirely by local AI (Ollama), your data stays yours without sacrificing AI capabilities.

> **Why FlowNote?** Stop switching tabs to jot down notes. Just highlight, press a hotkey or click the bubble, and your intelligent assistant captures, processes, and saves it beautifully in Markdown.

<div align="center">
  <!-- PLACEHOLDER FOR SCREENSHOT OF THE GORGEOUS BUBBLE WIDGET -->
  <img src="https://via.placeholder.com/800x400/181825/CDD6F4?text=Screenshot+of+FlowNote+Bubble+Widget" alt="FlowNote Interface" style="border-radius: 10px;"/>
  <p><i>The gorgeous new floating AI assistant</i></p>
</div>

---

## 🚀 Features

- 🫧 **Stunning UI**: A sleek, dark-themed floating widget with smooth animations and layout scaling.
- 📋 **Clipboard Capture**: Copy anything and turn it instantly into structured notes.
- 📷 **Screenshot OCR**: Built-in OCR easily extracts text from uncopyable areas on your screen and turns it into notes. 
- 🔗 **Link Fetching**: Feed it a URL and get a summary of the webpage.
- ⌨️ **Global Hotkeys**: Keep your flow going. Use your keyboard to command the assistant from anywhere on your OS.
- 🧠 **Local AI Processing**: Using Ollama, all intelligence runs securely on your machine.
- 🎨 **Style Selection**: Choose exactly how you want your notes (Concise, Extensive, Bullet Points, Code snippet, etc.).

---

## 🛠️ Installation

### Prerequisites
1. **Python 3.10+**
2. **Ollama**: [Download and install Ollama](https://ollama.ai/). Pull your preferred model (default is `llama3.2`):
   ```bash
   ollama run llama3.2
   ```
3. **Tesseract OCR (Optional, for Screenshots)**: 
   - Windows: [Download Installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Debian/Ubuntu: `sudo apt install tesseract-ocr`

### Setup
Clone the repository and install the dependencies:
```bash
git clone https://github.com/yourusername/flownote.git
cd flownote
pip install -r requirements.txt
```

---

## 🎯 Usage

Start FlowNote by simply running the main application script:

```bash
python run.py
```

### Modes of Operation
You can run FlowNote from the CLI for one-off tasks:
```bash
python run.py --clipboard         # Capture current clipboard
python run.py --screenshot        # Trigger OCR screenshot tool
python run.py --link              # Input a URL to summarize
```

### Hotkeys Mode
Run it silently in the background:
```bash
python run.py --hotkey            # Listens to Ctrl+Shift+S (or default)
```

**Inside the GUI:**
Click the beautifully redesigned floating bubble widget in the bottom right corner of your screen to expand it. You can interactively select tasks like taking screenshots, capturing clipboard, and changing processing styles!

---

## 🎨 Aesthetics & Technical Stack
FlowNote's UI has been overhauled mimicking premium design systems with a "Catppuccin"-esque dark theme palette containing brilliant accents of vivid green, purple, and blue.

The stack utilizes:
- **Core**: Python
- **GUI**: PyQt5 with custom QPropertyAnimations for an elegant UX
- **AI Backend**: Ollama
- **OCR Engine**: Tesseract with `pytesseract` and `mss`

---

## 🤝 Contributing
Contributions are totally welcome! Feel free to:
- Open issues for bugs or feature requests
- Create a Pull Request with your amazing additions
- Help enhance documentation

<div align="center">
  <i>Built with ❤️ for productive note-taking workflows</i>
</div>
