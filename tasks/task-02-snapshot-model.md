# Task 02: Normalized Snapshot Model

## Objective
Turn the raw `outputs` and `workspaces` responses into a validated, versioned snapshot containing connected outputs, selected workspaces, columns, and windows. Add `--all-workspaces`; default saves only the active workspace associated with each connected output.

## Files to create/modify
- `src/niri_layout/model.py`: dataclasses or typed mapping helpers for identifiers, outputs, workspaces, columns, and windows.
- `src/niri_layout/snapshot.py`: raw Niri payload normalization and active/all workspace selection.
- `src/niri_layout/cli.py`: save options and normalized snapshot flow.
- `src/niri_layout/storage.py`: schema version and snapshot document writing.
- `tests/fixtures/niri_outputs.json`, `tests/fixtures/niri_workspaces.json`.
- `tests/test_snapshot.py`: normalization and selection tests.
- Update `tests/test_cli_save.py` for the normalized document.

## Unit test cases (TDD)
- Connected outputs are included and disconnected outputs are excluded.
- Default mode selects one active workspace per connected output.
- `--all-workspaces` retains every workspace while preserving output association.
- Columns retain order, mode, width proportion, and window order.
- Missing optional fields produce explicit defaults or a validation error, never silently shifted data.
- The output document has `name`, `version: 1`, and `outputs` keys.

## Acceptance criteria
- `niri-layout save demo` writes the documented version-1 shape for fixture data.
- `niri-layout save demo --all-workspaces` includes inactive workspaces.
- Normalization is pure and testable without subprocesses.
- Malformed required Niri data fails with a clear user-facing error.
- All tests remain standard-library-only and pass offline.
