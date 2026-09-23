import io
import json
import unittest
from types import SimpleNamespace

from niri_layout.restore import restore_layout
from niri_layout.snapshot import normalize_snapshot


class FakeStream:
    def __init__(self, events):
        self.stdout = io.StringIO("".join(json.dumps(event) + "\n" for event in events))
        self.closed = False

    def readline(self):
        line = self.stdout.readline()
        return line if line else ""

    def close(self):
        self.closed = True

    def terminate(self):
        self.closed = True


class FocusCaptureTests(unittest.TestCase):
    def test_normalize_snapshot_records_focus_target_for_focused_window(self):
        outputs = {
            "DP-1": {
                "name": "DP-1",
                "make": "Dell Inc.",
                "model": "DELL U2720Q",
                "serial": "123",
                "is_connected": True,
            }
        }
        workspaces = [{
            "id": 1,
            "name": "dev-main",
            "output": "DP-1",
            "is_active": True,
            "is_focused": True,
            "columns": [{
                "mode": "split",
                "width": {"proportion": 1.0},
                "windows": [{
                    "app_id": "Alacritty",
                    "is_focused": True,
                    "layout": {"pos_in_scrolling_layout": [1, 1]},
                }],
            }],
        }]

        snapshot = normalize_snapshot("demo", outputs, workspaces)

        self.assertEqual(snapshot["focus"]["output_match"], "Dell Inc. DELL U2720Q 123")
        self.assertEqual(snapshot["focus"]["column_index"], 0)
        self.assertEqual(snapshot["focus"]["window_index"], 0)

    def test_restore_layout_focuses_final_target_window_after_placement(self):
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
                        "windows": [{"app_id": "Alacritty", "command": ["alacritty"]}],
                    }],
                }],
            }],
        }
        current_outputs = {"DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "is_connected": True}}

        actions = []
        launched = []
        stream_events = [
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 42},
        ]

        def fake_action(command, **kwargs):
            actions.append(tuple(command))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append(tuple(command))
            return SimpleNamespace(pid=101)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 42},
        ])

        result = restore_layout(
            snapshot,
            current_outputs,
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=stream,
            timeout=0.01,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn(("niri", "msg", "action", "focus-window", "--id", "42"), actions)

    def test_missing_focus_metadata_skips_refocus_without_failing_restore(self):
        snapshot = {
            "name": "demo",
            "version": 1,
            "outputs": [{
                "identifier": {"make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "fallback_connector": "DP-1"},
                "workspaces": [{
                    "name": "dev-main",
                    "columns": [{
                        "mode": "split",
                        "width": {"proportion": 1.0},
                        "windows": [{"app_id": "Alacritty", "command": ["alacritty"]}],
                    }],
                }],
            }],
        }
        current_outputs = {"DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "is_connected": True}}

        actions = []

        def fake_action(command, **kwargs):
            actions.append(tuple(command))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            return SimpleNamespace(pid=1)

        result = restore_layout(
            snapshot,
            current_outputs,
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=FakeStream([
                {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 55},
            ]),
            timeout=0.01,
        )

        self.assertEqual(result["status"], "ok")
        self.assertNotIn(("niri", "msg", "action", "focus-window", "--id", "55"), actions)


if __name__ == "__main__":
    unittest.main()
