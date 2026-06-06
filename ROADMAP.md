# Riptext Roadmap

Working list for future riptext improvements. Keep this practical: each item should move the app closer to a fast, scriptable text workbench.

## Completed

- [x] Managed multi-selection support
  - Mark multiple independent ranges from the editor.
  - Run one rip across all marked ranges with safe in-place replacement.
  - Keep selection handling understandable in the status bar.
- [x] Macro improvements
  - List, delete, rename, and favorite macros.
  - Show macro steps before running.
- [x] Transform history
  - Multi-step undo/redo.
  - Re-run scripts from history.
- [x] Better picker UX
  - Category/recent/favorite grouping.
  - Show tags and aliases.
- [x] Config file
  - Add `~/.riptext/config.toml` for user rips directory, default mode, keybindings, and display options.
- [x] More built-in rips
  - XML prettify/minify.
  - YAML/JSON conversion.
  - HTML escape/unescape.
  - JWT decode.
  - UUID generate.
  - Timestamp conversion.
  - Regex extract/replace.
  - Slugify.
  - Strip HTML.
  - Word wrap by width.
- [x] Script validation
  - Detect missing metadata, duplicate slugs, invalid JSON metadata, and missing entrypoints.
  - Expose validation through the command palette.
- [x] Script manager commands
  - Show/reload user rips.
  - Create a new rip from a template.
  - Show invalid scripts and metadata errors.

## In Progress

- [x] Native-feeling multi-selection polish
  - Add maintainable visual indicators for marked ranges.
  - [x] Support macro chains over marked ranges without stale offsets.

## Next

- [ ] Editor overlay range highlighting
  - Revisit when Textual exposes a stable range decoration or overlay API for `TextArea`.
