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
    column_number = int(column_index)
    width_value = _coerce_width(width)
    grouping_mode = str(mode or "split")
    return [
        ["niri", "msg", "action", "set-column-width", "--column", str(column_number), "--width", str(width_value)],
        ["niri", "msg", "action", "set-column-mode", "--column", str(column_number), "--mode", grouping_mode],
    ]
