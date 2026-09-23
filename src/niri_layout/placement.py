from __future__ import annotations

from collections.abc import Mapping


def _coerce_width(width):
    if isinstance(width, (int, float)):
        return float(width)
    if isinstance(width, Mapping):
        proportion = width.get("proportion")
        if proportion is None:
            raise ValueError("column width mapping must include a 'proportion'")
        return float(proportion)
    raise ValueError("column width must be a number or {'proportion': ...}")


def build_column_actions(column_index, width, mode):
    width_value = _coerce_width(width)
    grouping_mode = "tabbed" if str(mode or "split") == "tabbed" else "normal"
    return [
        ["niri", "msg", "action", "set-column-width", f"{width_value * 100:g}%"],
        ["niri", "msg", "action", "set-column-display", grouping_mode],
    ]
