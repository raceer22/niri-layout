import io
import json
import unittest
from types import SimpleNamespace

from niri_layout.placement import build_column_actions
from niri_layout.restore import restore_columns


class FakeStream:
    def __init__(self, events):
        self._events = list(events)
        self.stdout = io.StringIO("".join(json.dumps(event) + "\n" if isinstance(event, (dict, list, str, int, float, bool, type(None))) else "" for event in self._events))
        self.closed = False

    def readline(self):
        line = self.stdout.readline()
        if not line:
            return ""
        return line

    def close(self):
        self.closed = True


class RestoreColumnsFifoTests(unittest.TestCase):
    def test_build_column_actions_use_width_and_mode_actions(self):
        actions = build_column_actions(1, {"proportion": 0.25}, "tabbed")
        self.assertEqual(actions, [
            ["niri", "msg", "action", "set-column-width", "25%"],
            ["niri", "msg", "action", "set-column-mode", "tabbed"],
        ])

    def test_restore_columns_applies_actions_in_order_and_records_metadata(self):
        action_calls = []

        def fake_action(command, **kwargs):
            action_calls.append(tuple(command))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            return SimpleNamespace(pid=100 + len(action_calls))

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 10},
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 20},
        ])

        results = restore_columns(
            "demo",
            "DP-2",
            [
                {
                    "mode": "split",
                    "width": {"proportion": 0.4},
                    "windows": [{"app_id": "Alacritty", "command": ["alacritty"]}],
                },
                {
                    "mode": "tabbed",
                    "width": {"proportion": 0.6},
                    "windows": [{"app_id": "firefox", "command": ["firefox"]}],
                },
            ],
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=stream,
            timeout=0.05,
        )

        self.assertEqual([item["status"] for item in results], ["ok", "ok"])
        self.assertEqual([item["column_index"] for item in results], [0, 1])
        self.assertEqual([item["window_index"] for item in results], [0, 0])
        self.assertEqual(
            action_calls[:4],
            [
                ("niri", "msg", "action", "set-column-width", "40%"),
                ("niri", "msg", "action", "set-column-mode", "split"),
                ("niri", "msg", "action", "set-column-width", "60%"),
                ("niri", "msg", "action", "set-column-mode", "tabbed"),
            ],
        )

    def test_restore_columns_keeps_fifo_order_across_repeated_app_ids_and_malformed_events(self):
        def fake_action(command, **kwargs):
            return {"ok": True}

        def fake_launch(command, **kwargs):
            return SimpleNamespace(pid=200)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 1},
            "not-json",
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 2},
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 9},
        ])

        results = restore_columns(
            "demo",
            "DP-2",
            [
                {
                    "mode": "split",
                    "width": {"proportion": 0.5},
                    "windows": [
                        {"app_id": "Alacritty", "command": ["alacritty"]},
                        {"app_id": "Alacritty", "command": ["alacritty"]},
                        {"app_id": "firefox", "command": ["firefox"]},
                    ],
                }
            ],
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=stream,
            timeout=0.05,
        )

        self.assertEqual([item["window_id"] for item in results], [1, 2, 9])
        self.assertEqual([item["app_id"] for item in results], ["Alacritty", "Alacritty", "firefox"])
        self.assertEqual([item["window_index"] for item in results], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
