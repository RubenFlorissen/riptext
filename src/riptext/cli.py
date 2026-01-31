import argparse
import os
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
    file_path: Path | None = None
    cwd = Path(os.getcwd())

    if args.file:
        file_path = args.file.resolve()
        if file_path.is_file():
            initial_text = file_path.read_text(encoding="utf-8")
        else:
            print(f"Error: File not found: {args.file}")
            raise SystemExit(1)

    run_app(initial_text=initial_text, file_path=file_path, cwd=cwd)
