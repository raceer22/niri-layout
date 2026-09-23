from dataclasses import dataclass, field
from typing import Any


SNAPSHOT_VERSION = 1


@dataclass
class ColumnSnapshot:
    mode: str = "split"
    width: dict[str, Any] = field(default_factory=lambda: {"proportion": 1.0})
    windows: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode, "width": self.width, "windows": self.windows}


@dataclass
class WorkspaceSnapshot:
    name: str | None
    columns: list[ColumnSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "columns": [column.to_dict() for column in self.columns]}


@dataclass
class OutputSnapshot:
    identifier: dict[str, Any]
    workspaces: list[WorkspaceSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identifier": self.identifier,
            "workspaces": [workspace.to_dict() for workspace in self.workspaces],
        }