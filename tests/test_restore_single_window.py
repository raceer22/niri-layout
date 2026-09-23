import io
import json
import unittest
from types import SimpleNamespace

from niri_layout.ipc import close_event_stream, niri_action, start_event_stream
from niri_layout.launcher import launch_process
from niri_layout.restore import restore_single_window


class FakeStream:
    def __init__(self, events):
        self._events = list(events)
        self.stdout = io.StringIO("".join(json.dumps(event) + "\n" for event in self._events))
        self.closed = False
        self.terminated = False
        self.killed = False

    def readline(self):
        line = self.stdout.readline()
        if not line:
            return ""
        return line

    def close(self):
        self.closed = True

    def terminate(self):
        self.terminated = True
        self.closed = True

    def kill(self):
        self.killed = True
        self.closed = True


class RestoreSingleWindowTests(unittest.TestCase):
    def test_restore_single_window_creates_workspace_before_launch_and_waits_for_event(self):
        action_calls = []
        launched = []

        def fake_action(command, **kwargs):
            action_calls.append((tuple(command), kwargs))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append((tuple(command), kwargs))
            return SimpleNamespace(pid=101, stdout=None)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 42},
        ])

        result = restore_single_window(
            "demo",
            "DP-2",
            {"app_id": "Alacritty", "command": ["alacritty"]},
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=stream,
            timeout=0.1,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["window_id"], 42)
        self.assertEqual(action_calls[0][0], ("niri", "msg", "action", "new-workspace", "--output", "DP-2"))
        self.assertEqual(launched[0][0], ("alacritty",))
        self.assertTrue(stream.closed)

    def test_restore_single_window_ignores_other_app_ids_and_times_out_without_hanging(self):
        action_calls = []
        launched = []

        def fake_action(command, **kwargs):
            action_calls.append((tuple(command), kwargs))
            return {"ok": True}

        def fake_launch(command, **kwargs):
            launched.append((tuple(command), kwargs))
            return SimpleNamespace(pid=202, stdout=None)

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "firefox", "id": 99},
        ])

        result = restore_single_window(
            "demo",
            "DP-2",
            {"app_id": "Alacritty", "command": ["alacritty"]},
            action_runner=fake_action,
            launch_runner=fake_launch,
            event_stream=stream,
            timeout=0.01,
        )

        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["window_id"], None)
        self.assertEqual(len(action_calls), 1)
        self.assertEqual(len(launched), 1)

    def test_launch_process_uses_argument_list_without_shell(self):
        observed = {}

        def fake_runner(command, **kwargs):
            observed["command"] = command
            observed["kwargs"] = kwargs
            return SimpleNamespace(pid=7)

        proc = launch_process(["/usr/bin/firefox", "--new-window"], runner=fake_runner)

        self.assertEqual(proc.pid, 7)
        self.assertEqual(observed["command"], ["/usr/bin/firefox", "--new-window"])
        self.assertFalse(observed["kwargs"].get("shell", False))

    def test_ipc_helpers_build_action_and_start_event_stream(self):
        action = niri_action("new-workspace --output DP-2")
        self.assertEqual(action, ["niri", "msg", "action", "new-workspace", "--output", "DP-2"])

        fake_process = SimpleNamespace(
            cmd=["niri", "msg", "--json", "event-stream"],
            stdout=io.StringIO('{"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 7}\n'),
            stderr=io.StringIO(),
            terminate=lambda: None,
            kill=lambda: None,
            close=lambda: None,
        )
        started = start_event_stream(runner=lambda cmd, **kwargs: fake_process)
        self.assertEqual(started.cmd, ["niri", "msg", "--json", "event-stream"])
        self.assertEqual(started.readline(), '{"kind": "WindowOpenedOrChanged", "app_id": "Alacritty", "id": 7}\n')

        closed = close_event_stream(started)
        self.assertTrue(closed)


if __name__ == "__main__":
    unittest.main()
