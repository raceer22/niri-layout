from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .desktop import resolve_desktop_entry
from .model import ColumnSnapshot, OutputSnapshot, SNAPSHOT_VERSION, WorkspaceSnapshot


def _output_items(raw_outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> list[tuple[str, Mapping[str, Any]]]:
    if isinstance(raw_outputs, Mapping):
        return [(str(connector), details) for connector, details in raw_outputs.items()]
    if isinstance(raw_outputs, Sequence) and not isinstance(raw_outputs, (str, bytes)):
        items = []
        for details in raw_outputs:
            if not isinstance(details, Mapping):
                raise ValueError("each Niri output must be an object")
            connector = details.get("name") or details.get("connector")
            if not connector:
                raise ValueError("Niri output is missing its connector name")
            items.append((str(connector), details))
        return items
    raise ValueError("Niri outputs must be an object or list")


def _resolve_window_metadata(raw_window: Mapping[str, Any], *, app_dirs: Sequence[str | Path] | None = None) -> dict[str, Any]:
    app_id = raw_window.get("app_id")
    if not app_id:
        return {"app_id": app_id}

    window = {"app_id": app_id}
    if raw_window.get("desktop_id") is not None:
        window["desktop_id"] = raw_window["desktop_id"]
    if raw_window.get("command") is not None:
        window["command"] = raw_window["command"]

    if app_dirs is None:
        return window

    user_dirs = []
    system_dirs = []
    for directory in app_dirs:
        path = Path(directory).expanduser()
        if path.name == "applications":
            if user_dirs and path == user_dirs[-1]:
                continue
        if not user_dirs:
            user_dirs.append(path)
        else:
            system_dirs.append(path)

    resolution = resolve_desktop_entry(str(app_id), user_dirs=user_dirs, system_dirs=system_dirs)
    if resolution.resolved:
        window["desktop_id"] = resolution.desktop_id
        window["command"] = resolution.command
    elif resolution.warning:
        window["warning"] = resolution.warning
    return window


def _columns_from_windows(raw_windows: Sequence[Mapping[str, Any]], *, app_dirs: Sequence[str | Path] | None = None) -> list[ColumnSnapshot]:
    grouped: dict[int, list[tuple[int, Mapping[str, Any]]]] = {}
    for order, raw_window in enumerate(raw_windows):
        if not isinstance(raw_window, Mapping):
            raise ValueError("each Niri window must be an object")
        app_id = raw_window.get("app_id")
        if not app_id:
            raise ValueError("Niri window is missing its app_id")
        layout = raw_window.get("layout", {})
        position = layout.get("pos_in_scrolling_layout", [1, order]) if isinstance(layout, Mapping) else [1, order]
        column_index = position[0] if isinstance(position, list) and position and isinstance(position[0], int) else 1
        window = _resolve_window_metadata(raw_window, app_dirs=app_dirs)
        grouped.setdefault(column_index, []).append((order, window))

    return [
        ColumnSnapshot(windows=[window for _, window in grouped[index]])
        for index in sorted(grouped)
    ]


def _columns(raw_workspace: Mapping[str, Any], raw_windows: Sequence[Mapping[str, Any]] | None = None, *, app_dirs: Sequence[str | Path] | None = None) -> list[ColumnSnapshot]:
    raw_columns = raw_workspace.get("columns", [])
    if not raw_columns and raw_windows:
        return _columns_from_windows(raw_windows, app_dirs=app_dirs)
    if not isinstance(raw_columns, list):
        raise ValueError("workspace columns must be a list")

    columns = []
    for raw_column in raw_columns:
        if not isinstance(raw_column, Mapping):
            raise ValueError("each workspace column must be an object")
        width = raw_column.get("width", {"proportion": 1.0})
        if isinstance(width, (int, float)):
            width = {"proportion": width}
        if not isinstance(width, Mapping):
            raise ValueError("column width must be an object or number")
        windows = raw_column.get("windows", [])
        if not isinstance(windows, list) or any(not isinstance(window, Mapping) for window in windows):
            raise ValueError("column windows must be a list of objects")
        columns.append(
            ColumnSnapshot(
                mode=str(raw_column.get("mode", "split")),
                width=dict(width),
                windows=[_resolve_window_metadata(window, app_dirs=app_dirs) for window in windows],
            )
        )
    return columns


def normalize_snapshot(
    name: str,
    raw_outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    raw_workspaces: Sequence[Mapping[str, Any]],
    *,
    all_workspaces: bool = False,
    windows: Sequence[Mapping[str, Any]] | None = None,
    app_dirs: Sequence[str | Path] | None = None,
) -> dict[str, Any]:
    if not isinstance(name, str) or not name:
        raise ValueError("snapshot name must not be empty")
    if not isinstance(raw_workspaces, Sequence) or isinstance(raw_workspaces, (str, bytes)):
        raise ValueError("Niri workspaces must be a list")
    if windows is not None and (not isinstance(windows, Sequence) or isinstance(windows, (str, bytes))):
        raise ValueError("Niri windows must be a list")

    workspace_by_output: dict[str, list[WorkspaceSnapshot]] = {}
    active_outputs: set[str] = set()
    output_connectors = {connector for connector, details in _output_items(raw_outputs) if details.get("is_connected", True)}
    for raw_workspace in raw_workspaces:
        if not isinstance(raw_workspace, Mapping):
            raise ValueError("each Niri workspace must be an object")
        connector = raw_workspace.get("output")
        if not connector:
            raise ValueError("Niri workspace is missing its output")
        connector = str(connector)
        if connector not in output_connectors:
            continue
        if not all_workspaces and not raw_workspace.get("is_active", False):
            continue
        if not all_workspaces and connector in active_outputs:
            continue
        active_outputs.add(connector)
        workspace_id = raw_workspace.get("id")
        workspace_windows = [
            window for window in (windows or [])
            if isinstance(window, Mapping) and window.get("workspace_id") == workspace_id
        ]
        workspace_by_output.setdefault(connector, []).append(
            WorkspaceSnapshot(
                name=raw_workspace.get("name"),
                columns=_columns(raw_workspace, workspace_windows, app_dirs=app_dirs),
            )
        )

    outputs = []
    for connector, details in _output_items(raw_outputs):
        if not details.get("is_connected", True):
            continue
        identifier = {
            "make": details.get("make"),
            "model": details.get("model"),
            "serial": details.get("serial"),
            "fallback_connector": connector,
        }
        outputs.append(OutputSnapshot(identifier, workspace_by_output.get(connector, [])).to_dict())

    return {"name": name, "version": SNAPSHOT_VERSION, "outputs": outputs}