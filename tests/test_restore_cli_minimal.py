import io
import json
import shlex
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from niri_layout.cli import main


class FakeStream:
    def __init__(self, events):
        self._events = list(events)
        self.stdout = io.StringIO("".join(json.dumps(event) + "\n" for event in self._events))
        self.closed = False

    def readline(self):
        line = self.stdout.readline()
        return line if line else ""

    def close(self):
        self.closed = True

    def terminate(self):
        self.closed = True

    def kill(self):
        self.closed = True


class RestoreCLIMinimalTests(unittest.TestCase):
    def test_restore_command_executes_real_restore_flow_for_single_window(self):
        snapshot = {
            "name": "demo",
            "version": 1,
            "focus": {
                "output_match": "Dell Inc. DELL U2720Q 123",
                "column_index": 0,
                "window_index": 0,
            },
            "outputs": [{
                "identifier": {
                    "make": "Dell Inc.",
                    "model": "DELL U2720Q",
                    "serial": "123",
                    "fallback_connector": "DP-1",
                },
                "workspaces": [{
                    "name": "dev-main",
                    "columns": [{
                        "mode": "split",
                        "width": {"proportion": 1.0},
                        "windows": [{
                            "app_id": "Alacritty",
                            "command": ["alacritty"],
                        }],
                    }],
                }],
            }],
        }
        current_outputs = {
            "DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "is_connected": True},
        }
        action_calls = []
        launched = []

        def fake_action(command, **kwargs):
            tokens = shlex.split(command)
            action_calls.append(tuple(tokens))
            return ["niri", "msg", "action", *tokens]

        def fake_launch(command, **kwargs):
            launched.append(tuple(command))
            return SimpleNamespace(pid=101)

        with tempfile.TemporaryDirectory() as tmpdir:
            layout_dir = Path(tmpdir) / ".config" / "niri" / "layouts"
            layout_dir.mkdir(parents=True)
            (layout_dir / "demo.json").write_text(json.dumps(snapshot), encoding="utf-8")

            with patch("niri_layout.cli.query_niri", side_effect=lambda query: current_outputs if query == "outputs" else []):
                with patch("niri_layout.restore.niri_action", side_effect=fake_action):
                    with patch("niri_layout.restore.start_event_stream", return_value=FakeStream([
                        {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 42},
                    ])):
                        with patch("niri_layout.restore.launch_process", side_effect=fake_launch):
                            rc = main(["restore", "demo"], env={"HOME": tmpdir})

        self.assertEqual(rc, 0)
        self.assertIn(("new-workspace", "--output", "DP-1"), action_calls)
        self.assertEqual(launched[0], ("alacritty",))

    def test_restore_command_resolves_missing_window_command_from_desktop_entry(self):
        snapshot = {
            "name": "demo",
            "version": 1,
            "outputs": [{
                "identifier": {
                    "make": "Dell Inc.",
                    "model": "DELL U2720Q",
                    "serial": "123",
                    "fallback_connector": "DP-1",
                },
                "workspaces": [{
                    "name": "dev-main",
                    "columns": [{
                        "mode": "split",
                        "width": {"proportion": 1.0},
                        "windows": [{"app_id": "Alacritty"}],
                    }],
                }],
            }],
        }
        current_outputs = {
            "DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "is_connected": True},
        }
        launched = []

        def fake_action(command, **kwargs):
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append(tuple(command))
            return SimpleNamespace(pid=101)

        with patch("niri_layout.restore.resolve_desktop_entry", return_value=SimpleNamespace(
            resolved=True,
            desktop_id="Alacritty.desktop",
            command=["alacritty"],
            warning=None,
        )):
            with patch("niri_layout.restore.start_event_stream", return_value=FakeStream([
                {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 42},
            ])):
                result = __import__("niri_layout.restore", fromlist=["restore_layout"]).restore_layout(
                    snapshot,
                    current_outputs,
                    action_runner=fake_action,
                    launch_runner=fake_launch,
                    timeout=0.01,
                )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(launched[0], ("alacritty",))

    def test_restore_command_missing_layout_raises_missing_file_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("niri_layout.cli.query_niri", return_value={}):
                with self.assertRaises(FileNotFoundError):
                    main(["restore", "missing"], env={"HOME": tmpdir})


if __name__ == "__main__":
    unittest.main()
