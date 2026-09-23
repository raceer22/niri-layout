from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PLACEHOLDER_RE = re.compile(r"%[A-Za-z0-9]")
PLACEHOLDER_TOKENS = {"%U", "%u", "%F", "%f", "%c", "%k", "%d", "%D", "%i", "%m", "%n", "%N", "%v", "%V", "%e", "%x", "%X"}
DROP_WITH_PLACEHOLDER = {"--working-directory"}


@dataclass
class DesktopResolution:
    app_id: str
    desktop_id: str | None = None
    command: list[str] | None = None
    resolved: bool = False
    warning: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "app_id": self.app_id,
            "desktop_id": self.desktop_id,
            "command": self.command,
            "resolved": self.resolved,
            "warning": self.warning,
        }


def _coerce_dirs(values: Sequence[str | Path] | None) -> list[Path]:
    if values is None:
        return []
    return [Path(value).expanduser() for value in values]


def _clean_exec(exec_value: str) -> str:
    return PLACEHOLDER_RE.sub("", exec_value).strip()


def _parse_exec(exec_value: str) -> list[str]:
    try:
        tokens = shlex.split(exec_value, posix=True)
    except ValueError:
        tokens = exec_value.split()

    cleaned: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in PLACEHOLDER_TOKENS or (token.startswith("%") and len(token) > 1):
            index += 1
            continue
        if index + 1 < len(tokens) and token in DROP_WITH_PLACEHOLDER and tokens[index + 1] in PLACEHOLDER_TOKENS:
            index += 2
            continue
        cleaned.append(token)
        index += 1
    return cleaned


def _read_desktop_entry(path: Path) -> tuple[str | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None

    exec_value = None
    startup_wm_class = None
    in_desktop_entry = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_desktop_entry = stripped == "[Desktop Entry]"
            continue
        if not in_desktop_entry:
            continue
        if stripped.startswith("Exec="):
            exec_value = stripped.split("=", 1)[1]
        elif stripped.startswith("StartupWMClass="):
            startup_wm_class = stripped.split("=", 1)[1]
    return exec_value, startup_wm_class


def resolve_desktop_entry(
    app_id: str,
    *,
    user_dirs: Sequence[str | Path] | None = None,
    system_dirs: Sequence[str | Path] | None = None,
) -> DesktopResolution:
    if not app_id or not str(app_id).strip():
        raise ValueError("desktop app_id must be non-empty")

    normalized = str(app_id).strip()
    desktop_id = normalized if normalized.endswith(".desktop") else f"{normalized}.desktop"

    search_dirs: list[Path] = _coerce_dirs(user_dirs) + _coerce_dirs(system_dirs)
    if not search_dirs:
        search_dirs = [Path.home() / ".local/share/applications", Path("/usr/share/applications")]

    candidates: list[Path] = []
    for directory in search_dirs:
        direct = Path(directory) / desktop_id
        if direct.is_file():
            candidates.append(direct)
        for child in Path(directory).glob("*.desktop"):
            if child.name == desktop_id:
                continue
            exec_value, startup_wm_class = _read_desktop_entry(child)
            if exec_value and startup_wm_class and startup_wm_class == normalized:
                candidates.append(child)

    seen: set[Path] = set()
    for desktop_path in candidates:
        if desktop_path in seen:
            continue
        seen.add(desktop_path)

        exec_value, _ = _read_desktop_entry(desktop_path)
        if exec_value is None:
            return DesktopResolution(
                app_id=normalized,
                desktop_id=None,
                resolved=False,
                warning=f"desktop entry {desktop_path.name!r} is missing an Exec field",
            )

        command = _parse_exec(exec_value)
        if not command:
            return DesktopResolution(
                app_id=normalized,
                desktop_id=None,
                resolved=False,
                warning=f"desktop entry {desktop_path.name!r} does not define a valid Exec command",
            )

        return DesktopResolution(
            app_id=normalized,
            desktop_id=desktop_path.name,
            command=command,
            resolved=True,
        )

    return DesktopResolution(
        app_id=normalized,
        desktop_id=None,
        command=None,
        resolved=False,
        warning=f"no matching desktop entry was found for {normalized!r}",
    )
