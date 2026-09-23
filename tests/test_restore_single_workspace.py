import io
import json
import unittest
from types import SimpleNamespace

from niri_layout.restore import restore_layout


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


class RestoreSingleWorkspaceTests(unittest.TestCase):
    def test_restore_layout_handles_multiple_windows_in_order_on_one_output(self):
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
                        "windows": [
                            {"app_id": "Alacritty", "command": ["alacritty"]},
                            {"app_id": "firefox", "command": ["firefox"]},
                        ],
                    }],
                }],
            }],
        }
        current_outputs = {
            "DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "is_connected": True},
        }
        actions = []
        launched = []

        def fake_action(command, **kwargs):
            actions.append(tuple(command))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append(tuple(command))
            return SimpleNamespace(pid=100 + len(launched))

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 10},
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 20},
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
        self.assertEqual([entry["app_id"] for entry in result["placements"]], ["Alacritty", "firefox"])
        self.assertEqual([entry["window_id"] for entry in result["placements"]], [10, 20])
        self.assertEqual([entry["window_index"] for entry in result["placements"]], [0, 1])
        self.assertEqual(launched, [("alacritty",), ("firefox",)])
        self.assertIn(("niri", "msg", "action", "new-workspace", "--output", "DP-1"), actions)

    def test_restore_layout_ignores_missing_window_events_without_crashing(self):
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
                        "windows": [
                            {"app_id": "Alacritty", "command": ["alacritty"]},
                            {"app_id": "firefox", "command": ["firefox"]},
                        ],
                    }],
                }],
            }],
        }
        current_outputs = {"DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "DELL U2720Q", "serial": "123", "is_connected": True}}

        def fake_action(command, **kwargs):
            return {"ok": True}

        def fake_launch(command, **kwargs):
            return SimpleNamespace(pid=200)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 99},
            "not-json",
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
        self.assertEqual(len(result["placements"]), 2)
        self.assertEqual(result["placements"][0]["status"], "timeout")
        self.assertEqual(result["placements"][0]["app_id"], "Alacritty")


if __name__ == "__main__":
    unittest.main()
