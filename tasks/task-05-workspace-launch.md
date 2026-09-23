# Task 05: Workspace Creation and Single-Window Launch

## Objective
Make restore perform one complete placement slice: append one isolated workspace on a matched output, launch one application from its resolved desktop command, and wait for its first matching `WindowOpenedOrChanged` event. Keep IPC actions and event streaming injectable.

## Files to create/modify
- `src/niri_layout/ipc.py`: action invocation and event-stream process interfaces.
- `src/niri_layout/restore.py`: workspace creation, launch, and one-window correlation.
- `src/niri_layout/launcher.py`: safe argument-based process launch.
- `tests/test_restore_single_window.py`: fake IPC, fake launcher, and event-stream tests.

## Unit test cases (TDD)
- Workspace creation occurs before application launch.
- The target output is included in the workspace-creation action.
- A matching app ID event returns the new window ID.
- Events for other app IDs remain available for later consumers.
- A process launch receives an argument list and never uses a shell.
- No matching event within the configured timeout returns a failure result without hanging.

## Acceptance criteria
- `niri-layout restore demo` can restore a fixture with one workspace and one window through fake services.
- The implementation appends a new workspace and does not delete or rewrite existing workspaces.
- Per-window timeout defaults to 5 seconds and is injectable for tests.
- A timeout logs a warning and returns control to the caller.
- The event listener lifecycle is closed on success and timeout.
