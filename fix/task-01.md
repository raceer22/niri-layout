# Task 01: Minimal restore execution path

## Goal
Make the CLI restore command actually execute a real restore flow for a single saved layout, even in the smallest possible case: one connected output, one workspace, one window.

## Vertical slice
- `niri-layout restore demo` resolves the saved layout and current outputs without the `--plan` shortcut.
- The CLI calls the real restore logic instead of exiting early.
- The restore flow creates a workspace on the target output and launches the first app command.
- The result is observable through a fake action runner, launch runner, and event stream in an end-to-end test.

## Why this is first
This is the minimal viable restoration path: no multi-monitor complexity, no column widths, no resilience gymnastics. It proves the command is connected end-to-end before we layer on matching and spacing behavior.

## Files to change
- `src/niri_layout/cli.py`
- `src/niri_layout/restore.py`
- `tests/test_restore_cli_minimal.py` (new)

## TDD slice
- CLI restore returns success for a valid saved layout.
- A fake action runner receives `new-workspace --output <target>`.
- A fake launch runner receives the first window command.
- The generated restore status includes a placement entry and no fatal errors.
- A missing layout still raises the expected error instead of silently doing nothing.

## Acceptance criteria
- `niri-layout restore demo` no longer exits after printing a plan.
- A valid restore emits actual Niri actions and process launches.
- The single-window smoke path is covered by an automated integration-style test.
- This slice passes before moving to multi-output and multi-column work.
