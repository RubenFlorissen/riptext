import argparse
from pathlib import Path

from .app import run_app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="riptext — a TUI text transformation tool"
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Optional file to open and pre-populate the editor",
    )
    args = parser.parse_args()

    initial_text: str | None = None
    if args.file:
        if args.file.is_file():
            initial_text = args.file.read_text(encoding="utf-8")
        else:
            print(f"Error: File not found: {args.file}")
            raise SystemExit(1)

    run_app(initial_text=initial_text)
