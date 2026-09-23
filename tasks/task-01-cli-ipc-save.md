# Task 01: CLI IPC Save Skeleton

## Objective
Create the smallest functional `niri-layout save <name>` slice: parse the CLI command, query Niri's JSON IPC for `outputs` and `workspaces`, and save the received data as deterministic JSON. Keep subprocess execution behind an injectable client so unit tests never require a running Niri session.

## Files to create/modify
- `src/niri_layout/__init__.py`: package marker and version constant.
- `src/niri_layout/cli.py`: `argparse` entry point and `save` command.
- `src/niri_layout/ipc.py`: standard-library subprocess client for `niri msg --json <query>`.
- `src/niri_layout/storage.py`: layout-directory resolution and formatted JSON writing.
- `tests/test_cli_save.py`: end-to-end command test with fake IPC and temporary home/config directory.
- `tests/test_ipc.py`: subprocess argument, JSON parsing, and error tests.

## Unit test cases (TDD)
- `save name` calls IPC with `outputs` and `workspaces` in that order.
- The save command writes valid, indented JSON to `<config>/niri/layouts/name.json`.
- The persisted document contains the two raw query results without mutation.
- A non-zero subprocess result raises a project-level error and does not write a partial file.
- Invalid IPC JSON raises a useful project-level error.
- Names that would escape the layouts directory are rejected.

## Acceptance criteria
- `python -m niri_layout save smoke` is a valid invocation.
- The implementation uses only Python 3.10+ standard-library modules.
- The exact subprocess calls are `niri msg --json outputs` and `niri msg --json workspaces`.
- A successful save creates parent directories and writes stable, human-readable JSON.
- All tests pass without Niri, Wayland, or external packages installed.
