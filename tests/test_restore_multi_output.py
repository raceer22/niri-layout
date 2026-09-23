import io
import json
import unittest
from types import SimpleNamespace

from niri_layout.matching import match_output
from niri_layout.restore import build_restore_plan, restore_layout


class RestoreMultiOutputTests(unittest.TestCase):
    def test_partial_metadata_match_beats_connector_fallback(self):
        saved = {
            "make": "Dell Inc.",
            "model": "DELL P2217H",
            "serial": None,
            "fallback_connector": "HDMI-A-1",
        }
        current_outputs = {
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816", "is_connected": True},
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB", "is_connected": True},
        }

        self.assertEqual(match_output(saved, current_outputs), "DP-2")

    def test_restore_plan_maps_missing_output_to_primary_output(self):
        snapshot = {
            "name": "demo",
            "version": 1,
            "outputs": [
                {
                    "identifier": {
                        "make": "Dell Inc.",
                        "model": "DELL P2217H",
                        "serial": None,
                        "fallback_connector": "DP-2",
                    },
                    "workspaces": [{"name": "dev-main", "columns": []}],
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
        }

        plan = build_restore_plan(snapshot, current_outputs)

        self.assertEqual([item["source_output"] for item in plan], ["DP-2", "DP-9"])
        self.assertEqual([item["target_output"] for item in plan], ["DP-2", "DP-2"])

    def test_restore_layout_keeps_a_live_event_stream_open_across_outputs(self):
        class FakeStream:
            def __init__(self, events):
                self.stdout = io.StringIO("".join(json.dumps(event) + "\n" for event in events))
                self.closed = False

            def readline(self):
                if self.closed:
                    return ""
                line = self.stdout.readline()
                if not line:
                    return ""
                return line

            def close(self):
                self.closed = True

        stream = FakeStream([
            {"kind": "WindowOpenedOrChanged", "app_id": "kitty", "id": 10},
            {"kind": "WindowOpenedOrChanged", "app_id": "kitty", "id": 11},
        ])
        snapshot = {
            "name": "demo",
            "version": 1,
            "outputs": [
                {
                    "identifier": {"make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB", "fallback_connector": "DP-2"},
                    "workspaces": [{"name": "left", "columns": [{"mode": "split", "width": {"proportion": 1.0}, "windows": [{"app_id": "kitty", "command": ["kitty"]}]}]}],
                },
                {
                    "identifier": {"make": "Lenovo Group Limited", "model": "LEN P27u-10", "serial": "0x59333159", "fallback_connector": "DP-3"},
                    "workspaces": [{"name": "right", "columns": [{"mode": "split", "width": {"proportion": 1.0}, "windows": [{"app_id": "kitty", "command": ["kitty"]}]}]}],
                },
            ],
        }
        current_outputs = {
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB", "is_connected": True},
            "DP-3": {"name": "DP-3", "make": "Lenovo Group Limited", "model": "LEN P27u-10", "serial": "0x59333159", "is_connected": True},
        }

        result = restore_layout(
            snapshot,
            current_outputs,
            action_runner=lambda command, **kwargs: None,
            launch_runner=lambda command, **kwargs: SimpleNamespace(pid=1),
            event_stream=stream,
            timeout=0.05,
        )

        self.assertEqual([item["window_id"] for item in result["placements"]], [10, 11])
        self.assertFalse(stream.closed)


if __name__ == "__main__":
    unittest.main()
