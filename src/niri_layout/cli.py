import argparse
import json
import os
import warnings
from pathlib import Path

from . import NiriLayoutError
from .export import write_export_script
from .ipc import query_niri
from .restore import build_restore_plan, load_layout, restore_layout
from .snapshot import normalize_snapshot
from .storage import save_layout, validate_layout_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="niri-layout")
    subparsers = parser.add_subparsers(dest="command", required=True)

    save_parser = subparsers.add_parser("save", help="save the active layout")
    save_parser.add_argument("name", help="layout name")
    save_parser.add_argument("--all-workspaces", action="store_true", help="save inactive workspaces too")

    restore_parser = subparsers.add_parser("restore", help="plan a layout restore against active outputs")
    restore_parser.add_argument("name", help="layout name")
    restore_parser.add_argument("--plan", action="store_true", help="print a restore plan without mutating Niri")

    export_parser = subparsers.add_parser("export", help="export a standalone restore launcher")
    export_parser.add_argument("name", help="layout name")
    export_parser.add_argument("output_path", help="destination shell script path")
    return parser


def main(argv=None, env=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    home_dir = Path((env or os.environ).get("HOME", str(Path.home())))

    if args.command == "save":
        validate_layout_name(args.name)
        user_app_dir = home_dir / ".local" / "share" / "applications"
        system_app_dir = Path("/usr/share/applications")
        outputs = query_niri("outputs")
        workspaces = query_niri("workspaces")
        windows = query_niri("windows")
        payload = normalize_snapshot(
            args.name,
            outputs,
            workspaces,
            all_workspaces=args.all_workspaces,
            windows=windows,
            app_dirs=[user_app_dir, system_app_dir],
        )
        for output in payload.get("outputs", []):
            for workspace in output.get("workspaces", []):
                for column in workspace.get("columns", []):
                    for window in column.get("windows", []):
                        warning = window.get("warning")
                        if warning:
                            warnings.warn(f"desktop entry warning for {window.get('app_id')!r}: {warning}")
        save_layout(args.name, payload, home_dir=home_dir)
        return 0

    if args.command == "restore":
        validate_layout_name(args.name)
        snapshot = load_layout(args.name, home_dir=home_dir)
        current_outputs = query_niri("outputs")
        current_workspaces = query_niri("workspaces")
        plan = build_restore_plan(snapshot, current_outputs)
        if args.plan:
            print(json.dumps(plan, separators=(", ", ": "), sort_keys=True))
            return 0

        result = restore_layout(snapshot, current_outputs)
        print(json.dumps(result, separators=(", ", ": "), sort_keys=True))
        return 0

    if args.command == "export":
        validate_layout_name(args.name)
        write_export_script(args.name, args.output_path, home_dir=home_dir)
        return 0

    raise NiriLayoutError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
