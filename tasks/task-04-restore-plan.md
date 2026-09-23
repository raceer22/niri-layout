# Task 04: Display Matching and Restore Plan

## Objective
Add `niri-layout restore <name>` as a side-effect-free planning slice. Load a saved snapshot, query current outputs/workspaces, match saved displays by make/model/serial, fall back to connector names, and collapse unmatched saved outputs onto a selected primary active output. Emit a deterministic restore plan without creating workspaces yet.

## Files to create/modify
- `src/niri_layout/matching.py`: display identity and fallback matching.
- `src/niri_layout/restore.py`: snapshot loading and restore-plan construction.
- `src/niri_layout/cli.py`: `restore` command and human-readable plan output.
- `tests/test_matching.py`: exact metadata, incomplete metadata, connector fallback, and missing-display tests.
- `tests/test_restore_plan.py`: deterministic workspace assignment tests.

## Unit test cases (TDD)
- Full make/model/serial metadata matches the intended current output.
- Incomplete metadata uses the saved fallback connector.
- A disconnected saved output is assigned to the primary connected output.
- Multiple saved outputs collapsing to one target preserve saved output/workspace order.
- No active output produces a clear error instead of an invalid plan.
- Repeated planning with the same inputs returns byte-for-byte equivalent JSON.

## Acceptance criteria
- `niri-layout restore demo --plan` works without mutating Niri.
- Matching prefers hardware metadata and only then uses connector fallback.
- The plan explicitly records source output, target output, and workspace order.
- Missing display behavior matches the PRD's collapse requirement.
- Unit tests run with fake IPC responses and no live Niri process.
