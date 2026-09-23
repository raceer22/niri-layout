# niri-layout

`niri-layout` captures and restores Niri workspace layouts.

## Quick usage

```bash
niri-layout save dev-dual
niri-layout restore dev-dual
niri-layout export dev-dual ~/.config/niri/scripts/launch-dev.sh
```

The export command writes a standalone shell launcher that invokes `niri-layout restore` for the selected layout. The generated script is deterministic, executable, and does not embed project paths or Python dependencies.
