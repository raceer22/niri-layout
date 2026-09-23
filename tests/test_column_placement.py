import unittest

from niri_layout.placement import build_column_actions


class ColumnPlacementTests(unittest.TestCase):
    def test_build_column_actions_sets_width_then_grouping_mode(self):
        actions = build_column_actions(0, {"proportion": 0.5}, "split")
        self.assertEqual(
            actions,
            [
                ["niri", "msg", "action", "set-column-width", "--column", "0", "--width", "0.5"],
                ["niri", "msg", "action", "set-column-mode", "--column", "0", "--mode", "split"],
            ],
        )

    def test_tabbed_grouping_has_distinct_action(self):
        actions = build_column_actions(2, {"proportion": 0.75}, "tabbed")
        self.assertEqual(
            actions,
            [
                ["niri", "msg", "action", "set-column-width", "--column", "2", "--width", "0.75"],
                ["niri", "msg", "action", "set-column-mode", "--column", "2", "--mode", "tabbed"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
