import json
from pathlib import Path
from typing import Any


def validate_layout_name(name: str) -> str:
    if not name or not str(name).strip():
        raise ValueError("layout name must not be empty")

    candidate = str(name)
    if candidate in {".", ".."}:
        raise ValueError("layout name is invalid")
    if Path(candidate).is_absolute() or ".." in Path(candidate).parts:
        raise ValueError("layout name must stay within the layouts directory")
    if candidate != Path(candidate).name:
        raise ValueError("layout name must not contain path separators")
    return candidate


def _validate_layout_name(name: str) -> str:
    return validate_layout_name(name)


def layout_directory(home_dir: str | Path | None = None) -> Path:
    base = Path(home_dir) if home_dir is not None else Path.home()
    return base / ".config" / "niri" / "layouts"


def save_layout(name: str, payload: dict[str, Any], home_dir: str | Path | None = None) -> Path:
    safe_name = validate_layout_name(name)
    target = layout_directory(home_dir) / f"{safe_name}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
