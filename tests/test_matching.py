import unittest

from niri_layout.matching import match_output


class MatchingTests(unittest.TestCase):
    def test_match_output_prefers_hardware_metadata(self):
        saved = {
            "make": "Dell Inc.",
            "model": "DELL P2217H",
            "serial": "RH81R71J17EB",
            "fallback_connector": "DP-2",
        }
        current_outputs = {
            "DP-3": {"name": "DP-3", "make": "Lenovo Group Limited", "model": "LEN P27u-10", "serial": "0x59333159"},
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816"},
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB"},
        }

        self.assertEqual(match_output(saved, current_outputs), "DP-2")

    def test_match_output_uses_fallback_connector_when_metadata_is_incomplete(self):
        saved = {
            "make": "Dell Inc.",
            "model": None,
            "serial": None,
            "fallback_connector": "HDMI-A-1",
        }
        current_outputs = {
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816"},
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB"},
        }

        self.assertEqual(match_output(saved, current_outputs), "HDMI-A-1")

    def test_match_output_uses_single_metadata_field_when_it_uniquely_identifies_a_monitor(self):
        saved = {
            "make": "Lenovo Group Limited",
            "model": None,
            "serial": None,
            "fallback_connector": "DP-9",
        }
        current_outputs = {
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB", "is_connected": True},
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816", "is_connected": True},
        }

        self.assertEqual(match_output(saved, current_outputs), "HDMI-A-1")

    def test_missing_saved_output_collapses_to_primary_connected_output(self):
        saved = {
            "make": "Unknown",
            "model": "Missing",
            "serial": "0000",
            "fallback_connector": "DP-9",
        }
        current_outputs = {
            "DP-2": {"name": "DP-2", "make": "Dell Inc.", "model": "DELL P2217H", "serial": "RH81R71J17EB"},
            "HDMI-A-1": {"name": "HDMI-A-1", "make": "Lenovo Group Limited", "model": "T24i-10", "serial": "VT490816"},
        }

        self.assertEqual(match_output(saved, current_outputs), "DP-2")

    def test_no_connected_outputs_raises_a_clear_error(self):
        saved = {"make": "Unknown", "model": "Missing", "serial": "0000", "fallback_connector": "DP-9"}

        with self.assertRaises(ValueError):
            match_output(saved, {})


if __name__ == "__main__":
    unittest.main()
