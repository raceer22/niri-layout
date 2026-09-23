# Task 02: Single-output workspace + app launch flow

## Goal
Extend the minimal restore flow so a single saved workspace can restore multiple windows on the same output in their saved order, while preserving app launch sequencing.

## Vertical slice
- A restore payload with one output and one workspace produces a workspace on the target output.
- Each window command is launched in order using the saved `command` payload.
- Each launched app is matched to a `WindowOpenedOrChanged` event by `app_id` and its `window_id` is recorded.
- The result is returned as a structured placement record, not just warnings.

## Why this follows Task 01
Task 01 proves the path exists; this task proves it can handle an actual saved workspace with multiple windows and real ordering semantics.

## Files to change
- `src/niri_layout/restore.py`
- `src/niri_layout/cli.py` (if the CLI needs reporting changes)
- `tests/test_restore_single_workspace.py` (new)

## TDD slice
- Restore a workspace containing two windows on one output.
- Launcher order follows saved window order.
- Event correlation matches both windows by `app_id`.
- Non-matching or missing events do not crash the flow.
- Restore returns a `placements` list with correct `window_id` and index metadata.

## Acceptance criteria
- One workspace on one output restores with stable ordering.
- App events are correlated via a FIFO queue per `app_id`.
- The output is end-to-end testable with fake IPC and fake launchers.
- This prepares the restore path for multi-output mapping and column actions.
