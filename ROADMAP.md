# Riptext Roadmap

Working list for future riptext improvements. Keep this practical: each item should move the app closer to a fast, scriptable text workbench.

## Completed

- [x] Managed multi-selection support
  - Mark multiple independent ranges from the editor.
  - Run one rip across all marked ranges with safe in-place replacement.
  - Keep selection handling understandable in the status bar.

## In Progress

- [ ] Native-feeling multi-selection polish
  - Add visual indicators for marked ranges if Textual supports a maintainable overlay.
  - [x] Support macro chains over marked ranges without stale offsets.

## Next

- [ ] Script manager commands
  - Open/reload user rips.
  - Create a new rip from a template.
  - Show invalid scripts and metadata errors.
- [ ] Macro improvements
  - List, delete, rename, and favorite macros.
  - Show macro steps before running.
- [ ] Transform history
  - Multi-step undo/redo.
  - Re-run scripts from history.
- [ ] Better picker UX
  - Category/recent/favorite grouping.
  - Show tags and aliases.
- [ ] Script validation
  - Detect missing metadata, duplicate slugs, invalid JSON metadata, and missing entrypoints.
- [ ] Config file
  - Add `~/.riptext/config.toml` for user rips directory, default mode, keybindings, and display options.
- [ ] More built-in rips
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
