import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from niri_layout import NiriLayoutError
from niri_layout.cli import main


class SaveCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tmpdir.name)
        self.addCleanup(self.tmpdir.cleanup)

    def test_save_name_calls_ipc_in_order_and_writes_normalized_json(self):
        outputs = {"DP-1": {"name": "DP-1", "make": "Dell", "model": "U2720Q"}}
        workspaces = [{"id": 1, "name": "dev-main", "output": "DP-1", "is_active": True}]
        calls = []

        def fake_query(query, *, runner=None):
            calls.append(query)
            if query == "outputs":
                return outputs
            if query == "workspaces":
                return workspaces
            if query == "windows":
                return []
            raise AssertionError(f"Unexpected query: {query}")

        with patch("niri_layout.cli.query_niri", side_effect=fake_query):
            rc = main(["save", "smoke"], env={"HOME": str(self.home)})

        self.assertEqual(rc, 0)
        self.assertEqual(calls, ["outputs", "workspaces", "windows"])

        layout_path = self.home / ".config" / "niri" / "layouts" / "smoke.json"
        self.assertTrue(layout_path.exists())
        payload = json.loads(layout_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "smoke")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["outputs"][0]["identifier"]["fallback_connector"], "DP-1")
        self.assertEqual(payload["outputs"][0]["workspaces"][0]["name"], "dev-main")
        self.assertIn("\n  \"outputs\":", layout_path.read_text(encoding="utf-8"))

    def test_save_all_workspaces_flag_is_forwarded_to_normalizer(self):
        outputs = {"DP-1": {"name": "DP-1"}}
        workspaces = [
            {"id": 1, "name": "active", "output": "DP-1", "is_active": True},
            {"id": 2, "name": "inactive", "output": "DP-1", "is_active": False},
        ]

        def fake_query(query, *, runner=None):
            if query == "outputs":
                return outputs
            if query == "workspaces":
                return workspaces
            return []

        with patch("niri_layout.cli.query_niri", side_effect=fake_query):
            rc = main(["save", "smoke", "--all-workspaces"], env={"HOME": str(self.home)})

        self.assertEqual(rc, 0)
        layout_path = self.home / ".config" / "niri" / "layouts" / "smoke.json"
        payload = json.loads(layout_path.read_text(encoding="utf-8"))
        self.assertEqual(
            [workspace["name"] for workspace in payload["outputs"][0]["workspaces"]],
            ["active", "inactive"],
        )

    def test_save_name_raises_and_does_not_write_partial_file_on_ipc_failure(self):
        layout_path = self.home / ".config" / "niri" / "layouts" / "smoke.json"

        def fail_query(query, *, runner=None):
            raise NiriLayoutError(f"ipc failed for {query}")

        with patch("niri_layout.cli.query_niri", side_effect=fail_query):
            with self.assertRaises(NiriLayoutError):
                main(["save", "smoke"], env={"HOME": str(self.home)})

        self.assertFalse(layout_path.exists())

    def test_save_name_rejects_path_traversal_names(self):
        with self.assertRaises(ValueError):
            main(["save", "../escape"], env={"HOME": str(self.home)})


if __name__ == "__main__":
    unittest.main()
