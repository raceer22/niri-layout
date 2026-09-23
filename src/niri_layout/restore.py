from __future__ import annotations

import json
import time
import warnings
from collections import defaultdict, deque
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .ipc import close_event_stream, niri_action, start_event_stream
from .launcher import launch_process
from .matching import match_output
from .placement import build_column_actions
from .storage import layout_directory, validate_layout_name


def load_layout(name: str, home_dir: str | Path | None = None) -> dict[str, Any]:
    safe_name = validate_layout_name(name)
    layout_path = layout_directory(home_dir) / f"{safe_name}.json"
    if not layout_path.exists():
        raise FileNotFoundError(f"layout {safe_name!r} was not found at {layout_path}")
    with layout_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("layout file does not contain a JSON object")
    return dict(payload)


def build_restore_plan(snapshot: Mapping[str, Any], current_outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(snapshot, Mapping):
        raise ValueError("snapshot must be a mapping")

    outputs = snapshot.get("outputs", [])
    if not isinstance(outputs, list):
        raise ValueError("snapshot outputs must be a list")

    current = current_outputs
    plan: list[dict[str, Any]] = []
    for saved_output in outputs:
        if not isinstance(saved_output, Mapping):
            raise ValueError("each saved output must be a mapping")
        identifier = saved_output.get("identifier", {})
        if not isinstance(identifier, Mapping):
            identifier = {}
        source_connector = str(identifier.get("fallback_connector") or identifier.get("name") or identifier.get("connector") or "unknown")
        target_connector = match_output(identifier, current)
        workspaces = saved_output.get("workspaces", [])
        if not isinstance(workspaces, list):
            raise ValueError("saved output workspaces must be a list")
        workspace_order = []
        for workspace in workspaces:
            if isinstance(workspace, Mapping):
                workspace_name = workspace.get("name")
                if workspace_name is not None:
                    workspace_order.append(str(workspace_name))
        plan.append({
            "source_output": source_connector,
            "target_output": target_connector,
            "workspace_order": workspace_order,
        })
    return plan


def _consume_matching_event(
    stream,
    deadline: float,
    pending_by_app_id: defaultdict[str, deque],
    event_buffer: defaultdict[str, deque],
):
    while True:
        if pending_by_app_id:
            for app_id, queue in list(pending_by_app_id.items()):
                if queue and app_id in event_buffer and event_buffer[app_id]:
                    event = event_buffer[app_id].popleft()
                    if not event_buffer[app_id]:
                        del event_buffer[app_id]
                    queue_entry = pending_by_app_id[app_id].popleft()
                    if not pending_by_app_id[app_id]:
                        del pending_by_app_id[app_id]
                    return {
                        "status": "ok",
                        "window_id": event.get("id"),
                        "app_id": app_id,
                        "name": queue_entry.get("name"),
                        "window": queue_entry.get("window"),
                    }

        line = stream.readline()
        if not line:
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.01)
            continue

        payload = line.strip()
        if not payload:
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue

        if event.get("kind") != "WindowOpenedOrChanged":
            continue

        app_id = event.get("app_id")
        if app_id is None:
            continue

        if app_id in pending_by_app_id and pending_by_app_id[app_id]:
            queue_entry = pending_by_app_id[app_id].popleft()
            if not pending_by_app_id[app_id]:
                del pending_by_app_id[app_id]
            return {
                "status": "ok",
                "window_id": event.get("id"),
                "app_id": app_id,
                "name": queue_entry.get("name"),
                "window": queue_entry.get("window"),
            }

        event_buffer[app_id].append(event)


def restore_single_window(
    name: str,
    output_name: str,
    window: Mapping[str, Any],
    *,
    action_runner=None,
    launch_runner=None,
    event_stream=None,
    timeout: float = 5.0,
):
    if not isinstance(window, Mapping):
        raise ValueError("window must be a mapping")

    app_id = window.get("app_id")
    command = window.get("command")
    if app_id is None:
        raise ValueError("window is missing its app_id")
    if not command:
        raise ValueError("window is missing its command")

    action_runner = action_runner or (lambda command, **kwargs: None)
    launch_runner = launch_runner or launch_process
    stream = event_stream
    if stream is None:
        stream = start_event_stream()

    try:
        action_command = niri_action(f"new-workspace --output {output_name}")
        action_runner(action_command, shell=False)

        launch_proc = launch_runner(command, shell=False)
        if not hasattr(launch_proc, "pid"):
            raise RuntimeError("process launcher did not return a process with a pid")

        deadline = time.monotonic() + float(timeout)
        pending_by_app_id: defaultdict[str, deque] = defaultdict(deque)
        event_buffer: defaultdict[str, deque] = defaultdict(deque)
        pending_by_app_id[app_id].append({"name": name, "window": dict(window)})
        while True:
            matched = _consume_matching_event(stream, deadline, pending_by_app_id, event_buffer)
            if matched is not None:
                return matched
            if time.monotonic() >= deadline:
                warnings.warn(f"timed out waiting for app_id {app_id!r} on output {output_name!r}")
                if app_id in pending_by_app_id and pending_by_app_id[app_id]:
                    pending_by_app_id[app_id].popleft()
                    if not pending_by_app_id[app_id]:
                        del pending_by_app_id[app_id]
                return {"status": "timeout", "window_id": None, "app_id": app_id, "name": name}
            time.sleep(0.01)
    finally:
        close_event_stream(stream)


def restore_windows(
    name: str,
    output_name: str,
    windows: Sequence[Mapping[str, Any]],
    *,
    action_runner=None,
    launch_runner=None,
    event_stream=None,
    timeout: float = 5.0,
):
    if not isinstance(windows, Sequence) or isinstance(windows, (str, bytes)):
        raise ValueError("windows must be a sequence of mappings")

    action_runner = action_runner or (lambda command, **kwargs: None)
    launch_runner = launch_runner or launch_process
    stream = event_stream
    if stream is None:
        stream = start_event_stream()

    pending_by_app_id: defaultdict[str, deque] = defaultdict(deque)
    event_buffer: defaultdict[str, deque] = defaultdict(deque)
    results: list[dict[str, Any]] = []

    try:
        action_runner(niri_action(f"new-workspace --output {output_name}"), shell=False)
        for window in windows:
            if not isinstance(window, Mapping):
                raise ValueError("window must be a mapping")
            app_id = window.get("app_id")
            command = window.get("command")
            if app_id is None:
                raise ValueError("window is missing its app_id")
            if not command:
                raise ValueError("window is missing its command")

            pending_by_app_id[app_id].append({"name": name, "window": dict(window)})
            launch_proc = launch_runner(command, shell=False)
            if not hasattr(launch_proc, "pid"):
                raise RuntimeError("process launcher did not return a process with a pid")

            deadline = time.monotonic() + float(timeout)
            while True:
                matched = _consume_matching_event(stream, deadline, pending_by_app_id, event_buffer)
                if matched is not None:
                    results.append(matched)
                    break
                if time.monotonic() >= deadline:
                    warnings.warn(f"timed out waiting for app_id {app_id!r} on output {output_name!r}")
                    if app_id in pending_by_app_id and pending_by_app_id[app_id]:
                        pending_by_app_id[app_id].popleft()
                        if not pending_by_app_id[app_id]:
                            del pending_by_app_id[app_id]
                    results.append({"status": "timeout", "window_id": None, "app_id": app_id, "name": name})
                    break
                time.sleep(0.01)
        return results
    finally:
        close_event_stream(stream)


def restore_columns(
    name: str,
    output_name: str,
    columns: Sequence[Mapping[str, Any]],
    *,
    action_runner=None,
    launch_runner=None,
    event_stream=None,
    timeout: float = 5.0,
):
    if not isinstance(columns, Sequence) or isinstance(columns, (str, bytes)):
        raise ValueError("columns must be a sequence of mappings")

    results: list[dict[str, Any]] = []
    for index, column in enumerate(columns):
        if not isinstance(column, Mapping):
            raise ValueError("column must be a mapping")
        mode = str(column.get("mode", "split"))
        width = column.get("width", {"proportion": 1.0})
        for action in build_column_actions(index, width, mode):
            (action_runner or (lambda command, **kwargs: None))(action, shell=False)
        windows = column.get("windows", [])
        if windows:
            results.extend(
                restore_windows(
                    name,
                    output_name,
                    windows,
                    action_runner=action_runner,
                    launch_runner=launch_runner,
                    event_stream=event_stream,
                    timeout=timeout,
                )
            )
    return results
