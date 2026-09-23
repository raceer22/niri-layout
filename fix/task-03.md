# Task 03: Multi-output matching and fallback restore plan

## Goal
Enable restore logic to map saved outputs to current physical outputs using EDID metadata and connector fallback, including recovery when an output is unplugged or missing.

## Vertical slice
- A saved layout with two outputs is matched against current connected outputs.
- Exact `make/model/serial` match wins when available.
- If metadata is incomplete, the saved connector is used as a fallback.
- If a saved output is absent, the workflow collapses onto the primary connected output and continues.
- The restore plan produced by the CLI reflects those target mappings.

## Why this comes after the basic restore path
Once the system can restore a real workspace, the next question is “where does it go?”. This task closes the display-targeting requirement in an end-to-end manner.

## Files to change
- `src/niri_layout/matching.py`
- `src/niri_layout/restore.py`
- `tests/test_restore_multi_output.py` (new)

## TDD slice
- Match saved outputs to current outputs by make/model/serial.
- If metadata is partial, fall back to connector names.
- If a saved output is disconnected, route to the primary output.
- `build_restore_plan()` returns deterministic `source_output`, `target_output`, and `workspace_order` data.
- The CLI `restore --plan` flow is still preserved but now reflects actual mapping logic.

## Acceptance criteria
- Saved outputs are assigned to the correct current monitor.
- Connector fallback works when metadata is incomplete.
- Disconnected outputs are collapsed to a valid target without failing the restore run.
- The restore plan remains deterministic and testable.
