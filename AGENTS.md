# AGENTS.MD

This project is **riptext**, a cross-platform terminal UI (TUI) text transformation app inspired by Boop semantics. The goal is to ship the core semantics first: picker + search + selection-aware transforms.

## Product shape

### Surfaces

**Editor Surface**
- Main text editor panel.
- Supports:
  - Full-text editing.
  - Multi-selection (multiple independent ranges).
  - Cursor navigation, copy/paste, etc.
- Theming optional; syntax highlighting optional (nice-to-have).

**Picker Overlay**
- Modal overlay that opens/closes over the editor.
- Contains:
  - Search input.
  - List of scripts (“rips”) with keyboard navigation.
  - Status area for info/error/success messages.
- Key bindings:
  - Enter: run highlighted script.
  - Esc: dismiss picker.
  - / or Ctrl+P: open picker (pick one).
- Also:
  - Track last executed script.
  - Support re-run last script quickly from editor (hotkey).

## Script system and execution pipeline

### Script sources
Load scripts from:
- Built-in packaged scripts.
- User script directory (default: `~/.riptext/rips/`), optionally configurable.

### Script format + metadata
Scripts contain a metadata block at the top in Python.
Recommended example:

"""
{
  "name": "JSON Prettify",
  "slug": "json_prettify",
  "description": "Pretty-print JSON",
  "tags": ["json", "format"],
  "bias": 0.1
}
"""

The app must:
- Parse metadata.
- Build a searchable index.
- Show these fields in the picker list.

### Execution semantics (must match Boop)
When running a script:
- If no selection: run on full text, replace full text with result.
- If one selection: run on selection, replace only that selection.
- If multiple selections:
  - Transform each selection independently.
  - Replace in-place.
  - Handle offset correction (process ranges in descending order, or compute edits first then apply safely).

### Host ↔ script contract (the “execution object”)
Expose a single object to scripts that provides:
- `text`: current selection text (or full text depending on selection state).
- `selection`: list of selection ranges (start, end).
- `full_text`: full document text.
- `is_selection`: boolean (any selections exist).
- `insert(replacement: str)`: replace current target (selection or full text).
- `post_info(msg: str)` / `post_error(msg: str)`: push status messages to UI.

In Python implement this as a class instance passed to the script entrypoint.

### Script entrypoint
Each script must implement one of:
- `main(exec: ScriptExecution) -> None` (preferred).
- or `transform(text: str, **kwargs) -> str` (optional compatibility layer).

The host runs:
- Load script module.
- Instantiate execution object.
- Call `main(exec)` (or adapt via wrapper).
- Apply replacements + show status messages.

Timeouts optional (nice-to-have).

### Module loading / dependencies
Simplest: scripts can import stdlib + any pip packages installed in the same environment.

Boop-like “local require” (optional, cool):
- Allow `from riptext_modules import x` for built-ins.
- Allow importing sibling `.py` files from the user rips directory.
- Load modules from file paths via `importlib`.
- If implemented, keep it explicit (e.g., `riptext.require("foo")`) so it’s predictable.

### Search/ranking behavior
Picker search should be fuzzy and ranked:
- Search across: name, description, tags, slug.
- Weighted fields (name > tags > description).
- Optional metadata bias to boost a script.
- Filter out low-quality matches, then sort by score.

(Doesn’t need to be identical—just “feels good”.)

## TUI implementation recommendation
Use Textual (Python). It supports an overlay modal + list + keybindings + status bar. The editor can be a `TextArea`; multi-selection may require extending behavior, but it’s doable.

## Minimal data structures
- `ScriptMetadata(name, slug, description, tags, bias, path, source)`
- `ScriptIndex` that builds list + cached tokens
- `SelectionRange(start, end)`
- `ScriptExecution(full_text, selections, status_sink, insert_sink)`

## Non-goals (keeps it shippable)
- Perfect syntax highlighting.
- Perfect sandboxing.
- Perfect CommonJS emulation.

Ship the core semantics first: picker + search + selection-aware transforms.
