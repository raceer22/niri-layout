# Task 03: Desktop Entry Resolution

## Objective
Resolve each captured window's `app_id` to a desktop entry and store the launch metadata required for restoration. Search the user application directory before the system directory, parse only the desktop-entry fields needed by this project, and preserve unresolved windows as explicit warnings or errors according to a documented policy.

## Files to create/modify
- `src/niri_layout/desktop.py`: application-directory search, desktop-entry parsing, and `Exec` token handling.
- `src/niri_layout/snapshot.py`: attach `desktop_id` and normalized launch command to windows.
- `src/niri_layout/cli.py`: surface unresolved-entry warnings without aborting unrelated captures.
- `tests/fixtures/applications/user-editor.desktop`, `tests/fixtures/applications/system-editor.desktop`.
- `tests/test_desktop.py`: precedence, parsing, and quoting tests.
- Update `tests/test_snapshot.py` for resolved window metadata.

## Unit test cases (TDD)
- A matching user desktop entry wins over a system entry.
- Desktop IDs map correctly to `<desktop-id>.desktop` files.
- `Exec` field code placeholders such as `%U` and `%f` are removed for the stored base launch command.
- Quoted arguments and escaped spaces are parsed without shell evaluation.
- An absent or invalid desktop entry produces a structured unresolved result and a warning.
- Two windows with the same `app_id` retain independent order.

## Acceptance criteria
- Captured windows include `app_id`, resolved `desktop_id` when available, and a safe launch argument representation.
- No `shell=True` or ad hoc shell execution is used.
- Search order is `~/.local/share/applications` then `/usr/share/applications`.
- Snapshot save succeeds when one window cannot be resolved, while reporting that condition.
- All tests use temporary fixture directories and standard-library `unittest`.
