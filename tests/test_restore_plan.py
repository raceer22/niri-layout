import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from niri_layout.cli import main
from niri_layout.restore import build_restore_plan


class RestorePlanTests(unittest.TestCase):
    def test_plan_restore_matches_outputs_and_preserves_workspace_order(self):
        snapshot = {
            "name": "demo",
            "version": 1,
            "outputs": [
                {
                    "identifier": {
                        "make": "Dell Inc.",
                        "model": "DELL P2217H",
                        "serial": "RH81R71J17EB",
                        "fallback_connector": "DP-2",
                    },
                    "workspaces": [
                        {"name": "dev-main", "columns": []},
                        {"name": "notes", "columns": []},
                    ],
                },
                {
                    "identifier": {
                        "make": "Lenovo Group Limited",
                        "model": "T24i-10",
                        "serial": "VT490816",
                        "fallback_connector": "HDMI-A-1",
                    },
                    "workspaces": [{"name": "docs", "columns": []}],
                },
                {
                    "identifier": {
                        "make": "Missing",
                        "model": "Missing",
                        "serial": "Missing",
                        "fallback_connector": "DP-9",
                    },
                    "workspaces": [{"name": "ghost", "columns": []}],
                },
            ],
        }
        current_outputs = {
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB", "is_connected": True},
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816", "is_connected": True},
            "DP-3": {"name": "DP-3", "make": "Lenovo Group Limited", "model": "LEN P27u-10", "serial": "0x59333159", "is_connected": True},
        }

        plan = build_restore_plan(snapshot, current_outputs)

        self.assertEqual(
            [item["source_output"] for item in plan],
            ["DP-2", "HDMI-A-1", "DP-9"],
        )
        self.assertEqual(
            [item["target_output"] for item in plan],
            ["DP-2", "HDMI-A-1", "DP-2"],
        )
        self.assertEqual(
            [item["workspace_order"] for item in plan],
            [["dev-main", "notes"], ["docs"], ["ghost"]],
        )

    def test_restore_command_prints_deterministic_plan_without_mutating_niri(self):
        current_outputs = {
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB"},
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816"},
        }
        snapshot = {
            "name": "demo",
            "version": 1,
            "outputs": [
                {
                    "identifier": {"make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB", "fallback_connector": "DP-2"},
                    "workspaces": [{"name": "dev-main", "columns": []}],
                },
                {
                    "identifier": {"make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816", "fallback_connector": "HDMI-A-1"},
                    "workspaces": [{"name": "docs", "columns": []}],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            layout_dir = Path(tmpdir) / ".config" / "niri" / "layouts"
            layout_dir.mkdir(parents=True)
            (layout_dir / "demo.json").write_text(json.dumps(snapshot), encoding="utf-8")

            with patch("niri_layout.cli.query_niri", side_effect=lambda query: current_outputs if query == "outputs" else []):
                with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    rc = main(["restore", "demo", "--plan"], env={"HOME": tmpdir})

            self.assertEqual(rc, 0)
            printed = stdout.getvalue()
            self.assertIn('"source_output": "DP-2"', printed)
            self.assertIn('"target_output": "DP-2"', printed)
            self.assertIn('"workspace_order": ["dev-main"]', printed)

    def test_restore_plan_errors_when_no_active_output_exists(self):
        snapshot = {"name": "demo", "version": 1, "outputs": [{"identifier": {"make": "Unknown", "model": "Unknown", "serial": "1", "fallback_connector": "DP-9"}, "workspaces": []}]}

        with self.assertRaises(ValueError):
            build_restore_plan(snapshot, {})


if __name__ == "__main__":
    unittest.main()
