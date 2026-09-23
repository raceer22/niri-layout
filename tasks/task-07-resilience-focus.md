# Task 07: Resilience and Focus Preservation

## Objective
Finish the restore workflow's failure handling and focus behavior. Capture focus during save, continue after launch or event failures, summarize warnings, and refocus the captured target window after successful placement when its restored ID is known.

## Files to create/modify
- `src/niri_layout/snapshot.py`: capture focused output/column/window identity.
- `src/niri_layout/restore.py`: failure aggregation and focus restoration.
- `src/niri_layout/cli.py`: concise restore summary and non-zero exit policy.
- `tests/test_focus.py`: capture, resolve, and focus-action tests.
- `tests/test_restore_resilience.py`: launch failure, timeout, malformed event, and continuation tests.

## Unit test cases (TDD)
- Focus metadata is saved when Niri reports a focused window.
- The corresponding restored window receives a final focus action.
- Missing focus metadata skips refocus without failing restore.
- Launch failure records a warning and continues with subsequent windows.
- Malformed event data is isolated and does not terminate the event loop.
- Restore returns a failure status only when the documented fatal conditions occur.

## Acceptance criteria
- Restore attempts every independent window despite non-fatal failures.
- Every per-window failure includes enough context to identify output, workspace, column, and app.
- Focus is restored only after all placement attempts finish.
- The CLI reports a useful summary and uses a stable exit status policy.
- Tests prove there are no hangs and no focus action is issued for an unknown window.
