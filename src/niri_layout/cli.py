import argparse
import os
from pathlib import Path

from . import NiriLayoutError
from .ipc import query_niri
from .storage import save_layout, validate_layout_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="niri-layout")
    subparsers = parser.add_subparsers(dest="command", required=True)

    save_parser = subparsers.add_parser("save", help="save the active layout")
    save_parser.add_argument("name", help="layout name")
    return parser


def main(argv=None, env=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        validate_layout_name(args.name)
        home_dir = Path((env or os.environ).get("HOME", str(Path.home())))
        outputs = query_niri("outputs")
        workspaces = query_niri("workspaces")
        payload = {"outputs": outputs, "workspaces": workspaces}
        save_layout(args.name, payload, home_dir=home_dir)
        return 0

    raise NiriLayoutError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
