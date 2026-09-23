# Task 06: Columns, Modes, and FIFO Correlation

## Objective
Extend restore from one window to complete columns and workspaces. Correlate repeated launches with the same `app_id` using a FIFO queue, then issue actions that set each column's width and grouping mode (`split` or `tabbed`).

## Files to create/modify
- `src/niri_layout/restore.py`: ordered workspace/column/window traversal and FIFO event correlation.
- `src/niri_layout/placement.py`: column width and grouping action builders.
- `tests/test_fifo_correlation.py`: repeated app IDs, interleaved events, and unmatched events.
- `tests/test_column_placement.py`: width and mode action ordering.

## Unit test cases (TDD)
- Two launches with the same `app_id` consume two matching events in launch order.
- Interleaved events for different app IDs are routed to the correct pending queue.
- A missing event times out one window and does not block later windows.
- Width proportions are translated into the documented Niri action values.
- `split` and `tabbed` generate distinct grouping actions.
- Columns and windows are processed in snapshot order.

## Acceptance criteria
- A fixture containing multiple columns and repeated applications restores deterministically.
- One timed-out window does not prevent later columns or windows from being attempted.
- Every successful column receives its width and grouping configuration.
- FIFO state is isolated per restore operation and cannot leak between runs.
- Tests use fake event streams and complete quickly with a sub-second timeout.
