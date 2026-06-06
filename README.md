# riptext

A cross-platform terminal UI (TUI) text transformation tool inspired by [Boop](https://boop.okat.best/). Transform text with a fuzzy-searchable command palette and selection-aware scripts.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Command Palette** – Fuzzy search through available transformations with `Ctrl+B`
- **Selection-Aware** – Transforms apply to your selection, current line, or full text
- **Auto Mode Switching** – Automatically detects when you select text
- **Built-in Scripts** – 26 transformations organized in 9 categories
- **User Scripts** – Drop Python scripts in `~/.riptext/rips/` to extend functionality
- **Favorites & Recent** – Favorite scripts with `Ctrl+D`, recently used scripts are boosted
- **Macros** – Record chains of transforms with `Ctrl+M` and replay them
- **Syntax Highlighting** – Auto-detect language or run Detect Language
- **Save & Undo** – Save with `Ctrl+S`, undo/redo transforms with `Ctrl+Z`
- **Editor QoL** – Find (`Ctrl+F`), go to line (`Ctrl+G`), line numbers, word wrap
- **Keyboard-First** – Designed for fast, mouse-free workflows

## Installation

Requires Python 3.10+.

```bash
# Clone the repo
git clone https://github.com/youruser/riptext.git
cd riptext

# Install with uv (recommended)
uv sync
uv run riptext

# Or install globally with uv
uv tool install .

# Or install with pip
pip install -e .
```

## Usage

```bash
# Launch with empty editor
riptext

# Open a file
riptext myfile.txt
```

### Keybindings

| Key | Action |
|-----|--------|
| `Ctrl+B` | Open command palette |
| `Ctrl+R` | Re-run last script |
| `Ctrl+L` | Cycle selection mode (Full → Line → Selection) |
| `Ctrl+D` | Toggle favorite on last-run script |
| `Ctrl+M` | Start/stop macro recording |
| `Ctrl+S` | Save file |
| `Ctrl+Z` | Undo/redo last transform |
| `Ctrl+F` | Find text |
| `Ctrl+G` | Go to line |
| `Ctrl+N` | Toggle line numbers |
| `Ctrl+W` | Toggle word wrap |
| `Ctrl+X` | Quit |

### Selection Modes

- **Full text** – Transform the entire document
- **Current line** – Transform only the line where the cursor is
- **Selection** – Transform only the selected text (auto-activates when you select)

## Built-in Scripts (26)

| Category | Scripts |
|----------|---------|
| **Text Case** | Uppercase, Lowercase, Title Case, camelCase, snake_case, kebab-case |
| **Data** | JSON Prettify, JSON Minify, CSV to JSON, JSON to CSV |
| **Encoding** | Base64 Encode/Decode, URL Encode/Decode |
| **Lines** | Sort, Reverse, Remove Duplicates, Add Line Numbers, Trim, Wrap Lines |
| **Hashing** | MD5, SHA256 |
| **Analysis** | Count Stats (lines, words, chars) |
| **Formatting** | Markdown Table |
| **Text** | Reverse Text |
| **Utility** | Detect Language |

## Custom Scripts

Create Python scripts in `~/.riptext/rips/` with a JSON metadata docstring:

```python
"""
{
  "name": "My Transform",
  "slug": "my_transform",
  "description": "Does something cool",
  "tags": ["custom", "example"],
  "category": "Custom",
  "bias": 0.0
}
"""

def main(exec):
    text = exec.text
    exec.insert(text.upper())  # Your transformation
    exec.post_info("Done!")
```

### Script API

The `exec` object provides:

| Method/Property | Description |
|-----------------|-------------|
| `exec.text` | The text to transform (selection or full text) |
| `exec.full_text` | Always the full document |
| `exec.is_selection` | `True` if working on a selection |
| `exec.insert(str)` | Replace the target with new text |
| `exec.post_info(str)` | Show an info message |
| `exec.post_error(str)` | Show an error message |

## Development

```bash
# Clone and setup
git clone https://github.com/youruser/riptext.git
cd riptext
uv sync

# Run from source
uv run riptext

# Run with debug key logging
RIPTEXT_DEBUG_KEYS=1 uv run riptext
```

## Why "riptext"?

It rips through text transformations. Fast, simple, terminal-native.

## License

MIT
