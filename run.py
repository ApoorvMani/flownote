#!/usr/bin/env python3
"""
FlowNote - AI-Powered Note Taking Tool
Launcher script
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="FlowNote - AI-Powered Note Taking")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("--hotkey", action="store_true", help="Start with hotkey listener")
    parser.add_argument("--mode", choices=["clipboard", "screenshot", "link"], 
                       default="clipboard", help="Capture mode")
    args = parser.parse_args()

    if args.cli:
        from src.main import main as cli_main
        return cli_main()
    else:
        from src.app import main as gui_main
        return gui_main()


if __name__ == "__main__":
    sys.exit(main())
