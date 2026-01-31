# riptext

A cross-platform terminal UI (TUI) text transformation tool inspired by [Boop](https://boop.okat.best/). Transform text with a fuzzy-searchable command palette and selection-aware scripts.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Command Palette** – Fuzzy search through available transformations with `Ctrl+B`
- **Selection-Aware** – Transforms apply to your selection, current line, or full text
- **Auto Mode Switching** – Automatically detects when you select text
- **Built-in Scripts** – 13 common transformations out of the box
- **User Scripts** – Drop Python scripts in `~/.riptext/rips/` to extend functionality
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
| `Ctrl+X` | Quit |

### Selection Modes

- **Full text** – Transform the entire document
- **Current line** – Transform only the line where the cursor is
- **Selection** – Transform only the selected text (auto-activates when you select)

## Built-in Scripts

| Script | Description |
|--------|-------------|
| Uppercase | Convert text to UPPERCASE |
| Lowercase | Convert text to lowercase |
| JSON Prettify | Format JSON with indentation |
| Add Line Numbers | Prefix each line with its number |
| Base64 Encode | Encode text as Base64 |
| Base64 Decode | Decode Base64 to text |
| URL Encode | Percent-encode for URLs |
| URL Decode | Decode percent-encoded text |
| Trim | Remove leading/trailing whitespace |
| Sort Lines | Sort lines alphabetically |
| Reverse | Reverse the text |
| Reverse Lines | Reverse the order of lines |
| Remove Duplicates | Remove duplicate lines |

## Custom Scripts

Create Python scripts in `~/.riptext/rips/` with a JSON metadata docstring:

```python
"""
{
  "name": "My Transform",
  "slug": "my_transform",
  "description": "Does something cool",
  "tags": ["custom", "example"],
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
