"""
CLI Entry point for QManimPlayer.

Usage:
    python -m qmanimplayer [script.py]

Examples:
    python -m qmanimplayer
    python -m qmanimplayer bond_stretching.py
"""

import sys
import argparse
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="QManimPlayer - Parameter Editor for manim-gl Scripts"
    )

    parser.add_argument(
        "script",
        nargs="?",
        help="Path to manim-gl script to open"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="QManimPlayer 0.1.0"
    )

    args = parser.parse_args()

    # Create Qt application
    app = QApplication(sys.argv)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Load script if provided
    if args.script:
        script_path = Path(args.script)
        if script_path.exists():
            window._load_script(str(script_path))
        else:
            print(f"Error: Script not found: {args.script}", file=sys.stderr)

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
