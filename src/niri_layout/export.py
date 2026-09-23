import os
import tempfile
from pathlib import Path

from .storage import layout_directory, validate_layout_name


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def render_export_script(layout_name: str, *, home_dir: str | Path | None = None) -> str:
    safe_name = validate_layout_name(layout_name)
    layout_path = layout_directory(home_dir) / f"{safe_name}.json"
    if not layout_path.exists():
        raise FileNotFoundError(f"layout {safe_name!r} was not found at {layout_path}")

    quoted_name = shell_quote(safe_name)
    return "#!/bin/sh\nset -eu\nexec niri-layout restore " + quoted_name + "\n"


def write_export_script(layout_name: str, output_path: str | Path, *, home_dir: str | Path | None = None) -> Path:
    safe_name = validate_layout_name(layout_name)
    target = Path(output_path)
    layout_path = layout_directory(home_dir) / f"{safe_name}.json"
    if not layout_path.exists():
        raise FileNotFoundError(f"layout {safe_name!r} was not found at {layout_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    script = render_export_script(safe_name, home_dir=home_dir)

    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(script)
        os.chmod(temp_path, 0o755)
        os.replace(temp_path, target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return target
