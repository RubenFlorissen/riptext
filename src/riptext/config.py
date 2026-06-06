"""Configuration loading for riptext."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".riptext" / "config.toml"
VALID_SELECTION_MODES = {"full", "lines", "selection"}


@dataclass(frozen=True)
class RiptextConfig:
    user_rips_dir: Path | None = None
    default_mode: str = "full"
    show_line_numbers: bool = True
    word_wrap: bool = False
    keybindings: dict[str, str] = field(default_factory=dict)


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_simple_toml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current = data
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            current = data.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        current[key.strip()] = _parse_scalar(raw_value)
    return data


def _load_toml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib
    except ModuleNotFoundError:
        return _parse_simple_toml(text)
    return tomllib.loads(text)


def _path_from_config(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser()


def load_config(path: Path | None = None) -> RiptextConfig:
    """Load riptext config, returning defaults when the file is absent."""
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        return RiptextConfig()

    data = _load_toml(config_path)
    display = data.get("display", {})
    if not isinstance(display, dict):
        display = {}
    keybindings = data.get("keybindings", {})
    if not isinstance(keybindings, dict):
        keybindings = {}

    default_mode = str(data.get("default_mode") or "full")
    if default_mode not in VALID_SELECTION_MODES:
        default_mode = "full"

    return RiptextConfig(
        user_rips_dir=_path_from_config(data.get("user_rips_dir")),
        default_mode=default_mode,
        show_line_numbers=bool(display.get("show_line_numbers", True)),
        word_wrap=bool(display.get("word_wrap", False)),
        keybindings={
            str(action): str(keys)
            for action, keys in keybindings.items()
            if str(action).strip() and str(keys).strip()
        },
    )
