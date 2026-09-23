# Task 05: Resilience, focus restoration, and standalone export

## Goal
Close the remaining PRD-level reliability and usability gaps: continue after failed launches, restore the saved focus target, and generate a usable export script that can be dropped into a launcher or `niri.kdl` workflow.

## Vertical slice
- A failed app launch records a warning and the restore continues with the next window.
- The focused window from the saved layout is re-targeted by `focus-window --id <id>` after successful placements.
- The generated export script is executable, shell-safe, and invokes the restore command without embedding project-local paths.
- The full workflow is testable as a coherent end-to-end scenario rather than as isolated helper behavior.

## Why this is the final slice
This is the reliability and workflow completion layer on top of the working restore logic. It ensures the end-user experience matches the PRD rather than just the internal data model.

## Files to change
- `src/niri_layout/restore.py`
- `src/niri_layout/export.py`
- `src/niri_layout/cli.py`
- `tests/test_restore_resilience_focus_export.py` (new)

## TDD slice
- One app launch failure does not abort the rest of the layout restore.
- Focus is regained only for the saved target when a valid window ID exists.
- Export writes executable shell content that invokes `niri-layout restore <layout>` safely.
- The generated script can be executed under a fake `PATH` and still behaves predictably.

## Acceptance criteria
- Restore continues after per-window launch or waiting failures without hanging the overall operation.
- Focus is preserved after layout restoration completes.
- Export creates a standalone executable launcher script for the saved layout.
- The complete workflow is covered by a realistic end-to-end test suite.
