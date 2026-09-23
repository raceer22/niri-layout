import unittest

from niri_layout.snapshot import normalize_snapshot


class SnapshotNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.outputs = {
            "DP-1": {
                "name": "DP-1",
                "make": "Dell Inc.",
                "model": "U2720Q",
                "serial": "123",
            },
            "HDMI-A-1": {
                "name": "HDMI-A-1",
                "make": "LG",
                "model": "Ultra HD",
                "serial": "456",
            },
            "DP-9": {"name": "DP-9", "make": "Disconnected", "is_connected": False},
        }
        self.workspaces = [
            {
                "id": 1,
                "name": "dev-main",
                "output": "DP-1",
                "is_active": True,
                "columns": [
                    {
                        "mode": "split",
                        "width": {"proportion": 0.5},
                        "windows": [{"app_id": "Alacritty"}],
                    }
                ],
            },
            {"id": 2, "name": "old-main", "output": "DP-1", "is_active": False},
            {"id": 3, "name": "docs", "output": "HDMI-A-1", "is_active": True},
            {"id": 4, "name": "unknown", "output": "DP-9", "is_active": True},
        ]
        self.windows = [
            {
                "id": 10,
                "app_id": "Alacritty",
                "workspace_id": 1,
                "layout": {"pos_in_scrolling_layout": [1, 1]},
            },
            {
                "id": 11,
                "app_id": "firefox",
                "workspace_id": 1,
                "layout": {"pos_in_scrolling_layout": [2, 1]},
            },
        ]

    def test_normalizes_connected_outputs_and_active_workspaces(self):
        document = normalize_snapshot("demo", self.outputs, self.workspaces)

        self.assertEqual(document["name"], "demo")
        self.assertEqual(document["version"], 1)
        self.assertEqual(
            [output["identifier"]["fallback_connector"] for output in document["outputs"]],
            ["DP-1", "HDMI-A-1"],
        )
        self.assertEqual([workspace["name"] for workspace in document["outputs"][0]["workspaces"]], ["dev-main"])
        self.assertEqual(document["outputs"][0]["workspaces"][0]["columns"][0]["windows"], [{"app_id": "Alacritty"}])

    def test_all_workspaces_preserves_output_association_and_order(self):
        document = normalize_snapshot("demo", self.outputs, self.workspaces, all_workspaces=True)

        self.assertEqual(
            [workspace["name"] for workspace in document["outputs"][0]["workspaces"]],
            ["dev-main", "old-main"],
        )
        self.assertEqual([workspace["name"] for workspace in document["outputs"][1]["workspaces"]], ["docs"])

    def test_missing_optional_layout_fields_get_explicit_defaults(self):
        document = normalize_snapshot("demo", self.outputs, [self.workspaces[2]])

        workspace = document["outputs"][1]["workspaces"][0]
        self.assertEqual(workspace["columns"], [])

    def test_malformed_required_workspace_output_fails(self):
        with self.assertRaises(ValueError):
            normalize_snapshot("demo", self.outputs, [{"id": 1, "is_active": True}])

    def test_normalizes_windows_response_into_columns(self):
        workspaces = [dict(self.workspaces[0])]
        workspaces[0].pop("columns")
        document = normalize_snapshot("demo", self.outputs, workspaces, windows=self.windows)

        columns = document["outputs"][0]["workspaces"][0]["columns"]
        self.assertEqual([window["app_id"] for window in columns[0]["windows"]], ["Alacritty"])
        self.assertEqual([window["app_id"] for window in columns[1]["windows"]], ["firefox"])


if __name__ == "__main__":
    unittest.main()