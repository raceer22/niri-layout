from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

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
