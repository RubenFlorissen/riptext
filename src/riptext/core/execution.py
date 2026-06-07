from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Sequence
import contextlib
import importlib.util
import sys

from .models import ScriptMetadata, SelectionRange

StatusSink = Callable[[str], None]
InsertSink = Callable[[str], None]


@dataclass
class ScriptExecution:
    full_text: str
    selection: list[SelectionRange]
    is_selection: bool
    _status_info: StatusSink
    _status_error: StatusSink
    _insert: InsertSink
    _active_range: SelectionRange

    @property
    def text(self) -> str:
        if self.is_selection:
            return self.full_text[self._active_range.start : self._active_range.end]
        return self.full_text

    def insert(self, replacement: str) -> None:
        self._insert(replacement)

    def post_info(self, msg: str) -> None:
        self._status_info(msg)

    def post_error(self, msg: str) -> None:
        self._status_error(msg)


@contextlib.contextmanager
def _script_sys_path(path: Path):
    path_str = str(path)
    sys.path.insert(0, path_str)
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(path_str)


def _load_module(script: ScriptMetadata) -> ModuleType:
    module_name = f"riptext.script.{script.slug}"
    spec = importlib.util.spec_from_file_location(module_name, script.path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script {script.path}")
    module = importlib.util.module_from_spec(spec)
    with _script_sys_path(script.path.parent):
        spec.loader.exec_module(module)
    return module


def _apply_replacements(
    full_text: str,
    replacements: list[tuple[SelectionRange, str]],
) -> str:
    if not replacements:
        return full_text

    parts: list[str] = []
    cursor = 0
    for current_range, replacement in sorted(
        replacements,
        key=lambda item: item[0].start,
    ):
        parts.append(full_text[cursor : current_range.start])
        parts.append(replacement)
        cursor = current_range.end
    parts.append(full_text[cursor:])
    return "".join(parts)


def _replace_range(
    full_text: str,
    current_range: SelectionRange,
    replacement: str,
) -> str:
    return full_text[: current_range.start] + replacement + full_text[current_range.end :]


def _run_module_on_range(
    module: ModuleType,
    full_text: str,
    selection_list: list[SelectionRange],
    is_selection: bool,
    current_range: SelectionRange,
    info_messages: list[str],
    error_messages: list[str],
) -> str:
    replacement: str | None = None

    def insert_sink(value: str) -> None:
        nonlocal replacement
        replacement = value

    execution = ScriptExecution(
        full_text=full_text,
        selection=selection_list,
        is_selection=is_selection,
        _status_info=info_messages.append,
        _status_error=error_messages.append,
        _insert=insert_sink,
        _active_range=current_range,
    )

    try:
        if hasattr(module, "main"):
            module.main(execution)
        elif hasattr(module, "transform"):
            result = module.transform(execution.text)
            execution.insert(result)
        else:
            error_messages.append("Script has no main() or transform() entrypoint.")
    except Exception as exc:  # noqa: BLE001
        error_messages.append(f"Script error: {exc}")
        replacement = None

    if replacement is None:
        replacement = execution.text
    return replacement


def run_script(
    script: ScriptMetadata,
    full_text: str,
    selections: list[SelectionRange],
) -> tuple[str, list[str], list[str]]:
    info_messages: list[str] = []
    error_messages: list[str] = []

    if selections:
        selection_list = [s.normalized() for s in selections]
        ranges = sorted(selection_list, key=lambda s: s.start, reverse=True)
        is_selection = True
    else:
        ranges = [SelectionRange(0, len(full_text))]
        selection_list = []
        is_selection = False

    try:
        module = _load_module(script)
    except Exception as exc:  # noqa: BLE001
        return full_text, info_messages, [f"Failed to load script: {exc}"]

    replacements: list[tuple[SelectionRange, str]] = []
    for current_range in ranges:
        replacement = _run_module_on_range(
            module,
            full_text,
            selection_list,
            is_selection,
            current_range,
            info_messages,
            error_messages,
        )
        replacements.append((current_range, replacement))

    return _apply_replacements(full_text, replacements), info_messages, error_messages


def run_script_sequence(
    scripts: Sequence[ScriptMetadata],
    full_text: str,
    selections: list[SelectionRange],
) -> tuple[str, list[str], list[str]]:
    """Run scripts as a chain over full text or each selected range.

    When selections are present, each range is transformed independently by the
    entire script sequence, then replaced once. That keeps original offsets valid
    even when earlier scripts in the chain change the target length.
    """
    info_messages: list[str] = []
    error_messages: list[str] = []

    if not selections:
        for script in scripts:
            full_text, info, errors = run_script(script, full_text, [])
            info_messages.extend(info)
            error_messages.extend(errors)
        return full_text, info_messages, error_messages

    loaded_modules: list[tuple[ScriptMetadata, ModuleType]] = []
    for script in scripts:
        try:
            loaded_modules.append((script, _load_module(script)))
        except Exception as exc:  # noqa: BLE001
            error_messages.append(f"Failed to load script: {exc}")

    selection_list = [selection.normalized() for selection in selections]
    ranges = sorted(selection_list, key=lambda selection: selection.start, reverse=True)
    replacements: list[tuple[SelectionRange, str]] = []
    for current_range in ranges:
        target_text = full_text[current_range.start : current_range.end]
        for _, module in loaded_modules:
            target_range = SelectionRange(
                current_range.start,
                current_range.start + len(target_text),
            )
            target_full_text = _replace_range(full_text, current_range, target_text)
            replacement = _run_module_on_range(
                module,
                target_full_text,
                selection_list,
                True,
                target_range,
                info_messages,
                error_messages,
            )
            target_text = replacement
        replacements.append((current_range, target_text))

    return _apply_replacements(full_text, replacements), info_messages, error_messages
