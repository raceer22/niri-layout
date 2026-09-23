from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _normalize(value: Any) -> str:
    return str(value).strip().lower()


def _coerce_outputs(current_outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if isinstance(current_outputs, Mapping):
        return {str(connector): details for connector, details in current_outputs.items()}
    if isinstance(current_outputs, Sequence) and not isinstance(current_outputs, (str, bytes)):
        coerced: dict[str, Mapping[str, Any]] = {}
        for details in current_outputs:
            if not isinstance(details, Mapping):
                continue
            connector = details.get("name") or details.get("connector")
            if connector is None:
                continue
            coerced[str(connector)] = details
        return coerced
    raise ValueError("current outputs must be a mapping or list of output objects")


def _primary_output(current_outputs: Mapping[str, Mapping[str, Any]]) -> str:
    for connector, details in current_outputs.items():
        if details.get("is_connected", True):
            return str(connector)
    raise ValueError("no connected outputs are available to host a restore plan")


def match_output(saved: Mapping[str, Any] | None, current_outputs: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> str:
    current = _coerce_outputs(current_outputs)
    if not current:
        raise ValueError("no current outputs are available to match against")

    primary = _primary_output(current)
    saved_identifier = {} if saved is None else dict(saved)

    match_fields = {}
    for field in ("make", "model", "serial"):
        wanted = saved_identifier.get(field)
        if wanted not in (None, ""):
            match_fields[field] = str(wanted)

    if len(match_fields) >= 2:
        for connector, details in current.items():
            if not details.get("is_connected", True):
                continue
            matches = 0
            for field in ("make", "model", "serial"):
                wanted = match_fields.get(field)
                if wanted is None:
                    continue
                value = details.get(field)
                if value is not None and _normalize(value) == _normalize(wanted):
                    matches += 1
            if matches == len(match_fields):
                return str(connector)

    fallback_connector = saved_identifier.get("fallback_connector") or saved_identifier.get("name") or saved_identifier.get("connector")
    if fallback_connector is not None:
        target = str(fallback_connector)
        if target in current:
            if current[target].get("is_connected", True):
                return target
            return primary

    return primary
