# Task 04: Column mode/width actions + FIFO correlation

## Goal
Restore column topology faithfully: create the correct column widths, apply tabbed/split modes, and ensure multiple windows with the same app ID are matched in a stable order.

## Vertical slice
- A saved workspace with multiple columns and widths restores by emitting `set-column-width` and `set-column-mode` actions.
- Windows are launched in column order and each app is matched with FIFO correlation (`app_id` queue ordering).
- Events for duplicate or repeated app IDs are consumed in the correct order without losing future windows.
- Placement metadata records the correct `column_index` and `window_index` for each restored item.

## Why this is after multi-output mapping
The logic is only useful once the runtime has a real target output. This task adds the actual layout topology and ordering semantics from the PRD.

## Files to change
- `src/niri_layout/placement.py`
- `src/niri_layout/restore.py`
- `tests/test_restore_columns_fifo.py` (new)

## TDD slice
- A two-column layout emits column actions with the saved proportions and mode.
- The output of `restore_columns()` preserves saved order.
- FIFO queue logic handles an `app_id` appearing multiple times across windows.
- A malformed event payload is ignored and does not terminate the restore flow.

## Acceptance criteria
- Column widths and modes are restored from saved layout data.
- Event-stream matching is robust for repeated app IDs and malformed events.
- `column_index` and `window_index` metadata are reported correctly.
- The flow remains testable end-to-end with fake actions and fake streams.
