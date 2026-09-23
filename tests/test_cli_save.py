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

    def test_save_name_calls_ipc_in_order_and_writes_json(self):
        outputs = [{"identifier": {"make": "Dell", "model": "U2720Q"}}]
        workspaces = [{"name": "dev-main"}]
        calls = []

        def fake_query(query, *, runner=None):
            calls.append(query)
            if query == "outputs":
                return outputs
            if query == "workspaces":
                return workspaces
            raise AssertionError(f"Unexpected query: {query}")

        with patch("niri_layout.cli.query_niri", side_effect=fake_query):
            rc = main(["save", "smoke"], env={"HOME": str(self.home)})

        self.assertEqual(rc, 0)
        self.assertEqual(calls, ["outputs", "workspaces"])

        layout_path = self.home / ".config" / "niri" / "layouts" / "smoke.json"
        self.assertTrue(layout_path.exists())
        payload = json.loads(layout_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["outputs"], outputs)
        self.assertEqual(payload["workspaces"], workspaces)
        self.assertIn("\n  \"outputs\":", layout_path.read_text(encoding="utf-8"))

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
