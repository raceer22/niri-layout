import io
import json
import unittest
from collections import deque
from types import SimpleNamespace

from niri_layout.restore import restore_windows


class FakeStream:
    def __init__(self, events):
        self._events = list(events)
        self.stdout = io.StringIO("".join(json.dumps(event) + "\n" for event in self._events))
        self.closed = False

    def readline(self):
        line = self.stdout.readline()
        if not line:
            return ""
        return line

    def close(self):
        self.closed = True


class RestoreWindowQueueTests(unittest.TestCase):
    def test_fifo_queue_matches_repeated_app_ids_in_launch_order(self):
        action_calls = []
        launched = []

        def fake_action(command, **kwargs):
            action_calls.append((tuple(command), kwargs))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append((tuple(command), kwargs))
            return SimpleNamespace(pid=100 + len(launched), stdout=None)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 10},
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 11},
        ])

        results = restore_windows(
            "demo",
            "DP-2",
            [
                {"app_id": "Alacritty", "command": ["alacritty"]},
                {"app_id": "Alacritty", "command": ["alacritty"]},
            ],
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=stream,
            timeout=0.05,
        )

        self.assertEqual([item["window_id"] for item in results], [10, 11])
        self.assertEqual(len(launched), 2)

    def test_interleaved_events_are_routed_to_the_correct_pending_queue(self):
        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 1},
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 9},
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 2},
        ])

        results = restore_windows(
            "demo",
            "DP-2",
            [
                {"app_id": "Alacritty", "command": ["alacritty"]},
                {"app_id": "firefox", "command": ["firefox"]},
                {"app_id": "Alacritty", "command": ["alacritty"]},
            ],
            action_runner=lambda command, **kwargs: {"ok": True},
            launch_runner=lambda command, **kwargs: SimpleNamespace(pid=1, stdout=None),
            event_stream=stream,
            timeout=0.05,
        )

        self.assertEqual([item["app_id"] for item in results], ["Alacritty", "firefox", "Alacritty"])
        self.assertEqual([item["window_id"] for item in results], [1, 9, 2])

    def test_missing_event_times_out_one_window_without_blocking_later_windows(self):
        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 99},
        ])

        results = restore_windows(
            "demo",
            "DP-2",
            [
                {"app_id": "Alacritty", "command": ["alacritty"]},
                {"app_id": "firefox", "command": ["firefox"]},
            ],
            action_runner=lambda command, **kwargs: {"ok": True},
            launch_runner=lambda command, **kwargs: SimpleNamespace(pid=1, stdout=None),
            event_stream=stream,
            timeout=0.01,
        )

        self.assertEqual(results[0]["status"], "timeout")
        self.assertEqual(results[1]["status"], "ok")
        self.assertEqual(results[1]["window_id"], 99)


if __name__ == "__main__":
    unittest.main()
