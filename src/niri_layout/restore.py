from __future__ import annotations

import json
import time
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .ipc import close_event_stream, niri_action, start_event_stream
from .launcher import launch_process
from .matching import match_output
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
    close_after = True

    if stream is None:
        stream = start_event_stream()
        close_after = True

    try:
        action_command = niri_action(f"new-workspace --output {output_name}")
        action_runner(action_command, shell=False)

        launch_proc = launch_runner(command, shell=False)
        if not hasattr(launch_proc, "pid"):
            raise RuntimeError("process launcher did not return a process with a pid")

        deadline = time.monotonic() + float(timeout)
        while True:
            line = stream.readline()
            if not line:
                if time.monotonic() >= deadline:
                    warnings.warn(f"timed out waiting for app_id {app_id!r} on output {output_name!r}")
                    return {"status": "timeout", "window_id": None, "app_id": app_id, "name": name}
                time.sleep(0.01)
                continue

            payload = line.strip()
            if not payload:
                continue
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue

            if event.get("kind") == "WindowOpenedOrChanged" and event.get("app_id") == app_id:
                return {"status": "ok", "window_id": event.get("id"), "app_id": app_id, "name": name}

            if time.monotonic() >= deadline:
                warnings.warn(f"timed out waiting for app_id {app_id!r} on output {output_name!r}")
                return {"status": "timeout", "window_id": None, "app_id": app_id, "name": name}
    finally:
        if close_after:
            close_event_stream(stream)
