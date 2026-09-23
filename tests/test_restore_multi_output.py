import unittest

from niri_layout.matching import match_output
from niri_layout.restore import build_restore_plan


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


if __name__ == "__main__":
    unittest.main()
