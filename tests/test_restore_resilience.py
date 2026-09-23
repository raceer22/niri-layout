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


class RestoreResilienceTests(unittest.TestCase):
    def test_restore_continues_after_launch_failure_and_records_warning(self):
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
        actions = []
        launched = []

        def fake_action(command, **kwargs):
            actions.append(tuple(command))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append(tuple(command))
            if command == ("alacritty",):
                raise RuntimeError("launch failed")
            return SimpleNamespace(pid=10)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 9},
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
        self.assertEqual(len(launched), 2)
        self.assertEqual(result["warnings"][0]["app_id"], "Alacritty")

    def test_restore_ignores_malformed_event_payloads_and_keeps_running(self):
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

        def fake_action(command, **kwargs):
            return {"ok": True}

        def fake_launch(command, **kwargs):
            return SimpleNamespace(pid=10)

        stream = FakeStream([
            "not-json",
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 77},
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
        self.assertEqual(result["placements"][0]["window_id"], 77)

    def test_restore_returns_failure_status_only_for_fatal_conditions(self):
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

        def fake_action(command, **kwargs):
            raise RuntimeError("fatal action failed")

        with self.assertRaises(RuntimeError):
            restore_layout(snapshot, current_outputs, action_runner=fake_action, launch_runner=lambda *a, **k: SimpleNamespace(pid=1), event_stream=FakeStream([]), timeout=0.01)


if __name__ == "__main__":
    unittest.main()
