# Task 08: Standalone Export Script

## Objective
Add `niri-layout export <name> <output_path>` to generate a standalone executable shell launcher that invokes the installed restoration command for the selected layout. Make output deterministic, shell-safe, and independent of the current working directory.

## Files to create/modify
- `src/niri_layout/export.py`: script rendering and atomic file writing.
- `src/niri_layout/cli.py`: `export` command.
- `tests/test_export.py`: script content, quoting, overwrite, and permissions tests.
- `README.md` or `docs/usage.md`: final CLI examples and supported behavior.

## Unit test cases (TDD)
- Export references the requested layout name and `niri-layout restore`.
- A layout name and output path containing shell metacharacters are safely represented.
- The output is written atomically and receives executable permissions.
- Existing output behavior is explicit and tested rather than accidental.
- Export rejects a missing layout before creating or truncating the destination.
- Generated scripts run in a fake `PATH` with a fake `niri-layout` executable.

## Acceptance criteria
- `niri-layout export demo /tmp/launch-demo.sh` creates an executable script.
- Running the generated script invokes restore for exactly the requested layout.
- The script does not embed secrets, absolute project paths, or external Python dependencies.
- Export errors leave the destination unchanged when possible.
- The complete standard-library test suite passes and the documented PRD workflows are covered.
