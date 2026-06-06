# Riptext – Copilot Instructions

## Project Overview
**riptext** is a cross-platform TUI text transformation app built with Python 3.10+ and Textual. It provides a fuzzy-searchable command palette for running text transforms (called "rips").

## Tech Stack
- Python 3.10+, managed with `uv`
- Textual (TUI framework) with `[syntax]` extra
- tree-sitter-languages for syntax highlighting
- rapidfuzz for fuzzy search
- hatchling build backend

## Project Structure
```
src/riptext/
├── app.py          # Main Textual App class
├── cli.py          # CLI entry point (argparse)
├── commands.py     # Command palette provider
├── favorites.py    # Favorites/recent tracking (persisted to ~/.riptext/state.json)
├── macros.py       # Chained transforms (persisted to ~/.riptext/macros/)
├── save.py         # File save logic
├── selection.py    # Selection mode handling
├── syntax.py       # Language detection for highlighting
├── core/
│   ├── models.py      # SelectionRange, ScriptMetadata dataclasses
│   ├── execution.py   # ScriptExecution + run_script()
│   ├── scripts.py     # Script loading, metadata parsing, ScriptIndex
│   └── search.py      # Fuzzy ranking with rapidfuzz
└── rips/builtins/     # 26 built-in transform scripts
```

## Key Patterns
- Scripts use JSON metadata in module docstrings with fields: name, slug, description, tags, category, bias
- Scripts implement `main(exec)` or `transform(text)` entry points
- ScriptExecution provides: text, full_text, is_selection, insert(), post_info(), post_error()
- Script validation reports missing metadata, invalid metadata JSON, duplicate slugs, and missing entrypoints
- Script manager commands expose reload, user rips directory, template creation, and issue display
- Categories are inferred from tags if not explicitly set in metadata
- Favorites/recent state persisted to `~/.riptext/state.json`
- Macros persisted as JSON in `~/.riptext/macros/`

## Running
```bash
uv sync
uv run riptext [file]
```

## Key Bindings
- Ctrl+B: Command palette
- Ctrl+R: Re-run last script
- Ctrl+L: Cycle selection mode
- Ctrl+D: Toggle favorite
- Ctrl+M: Record/save macro
- Ctrl+E: Mark active selection/current line as a transform target
- Ctrl+U: Clear marked transform targets
- Ctrl+S: Save file
- Ctrl+Z: Undo/redo transform
- Ctrl+F/G/N/W: Find, goto line, line numbers, word wrap
- Ctrl+X: Quit
