# niri-layout

`niri-layout` captures and restores Niri workspace layouts.

## Quick usage

```bash
niri-layout save dev-dual
niri-layout restore dev-dual
niri-layout export dev-dual ~/.config/niri/scripts/launch-dev.sh
```

The export command writes a standalone shell launcher that replicates the actions of the `niri-layout restore` command for the selected layout. The generated script is deterministic, executable, and does not embed project paths or Python dependencies.

## Installation

From a clone of this repository, create and activate a virtual environment,
then install the project in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

This installs the `niri-layout` command in the virtual environment and points it
at the source in this checkout. Activate `.venv` whenever you want to run the
command:

```bash
niri-layout --help
```
