import tempfile
import unittest
from pathlib import Path

from niri_layout.desktop import resolve_desktop_entry
from niri_layout.snapshot import normalize_snapshot


class DesktopResolutionTests(unittest.TestCase):
    def test_user_desktop_entry_wins_over_system(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            user_dir = tmpdir / "user-applications"
            system_dir = tmpdir / "system-applications"
            user_dir.mkdir()
            system_dir.mkdir()

            (user_dir / "editor.desktop").write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Exec=editor --user --file %U\n",
                encoding="utf-8",
            )
            (system_dir / "editor.desktop").write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Exec=editor --system --file %f\n",
                encoding="utf-8",
            )

            resolution = resolve_desktop_entry("editor", user_dirs=[user_dir], system_dirs=[system_dir])

            self.assertTrue(resolution.resolved)
            self.assertEqual(resolution.desktop_id, "editor.desktop")
            self.assertEqual(resolution.command, ["editor", "--user", "--file"])

    def test_exec_placeholders_are_removed_and_quotes_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            app_dir = tmpdir / "applications"
            app_dir.mkdir()
            desktop = app_dir / "browser.desktop"
            desktop.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Exec=browser --new-window --profile \"my profile\" --title \"%c\" %U %f\n",
                encoding="utf-8",
            )

            resolution = resolve_desktop_entry("browser", user_dirs=[app_dir], system_dirs=[])

            self.assertEqual(resolution.desktop_id, "browser.desktop")
            self.assertEqual(resolution.command, ["browser", "--new-window", "--profile", "my profile", "--title"])

    def test_missing_or_invalid_desktop_entry_is_structured_as_unresolved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            user_dir = tmpdir / "applications"
            user_dir.mkdir()
            (user_dir / "missing.desktop").write_text("[Desktop Entry]\nType=Application\n", encoding="utf-8")

            resolution = resolve_desktop_entry("missing", user_dirs=[user_dir], system_dirs=[])

            self.assertFalse(resolution.resolved)
            self.assertIsNone(resolution.desktop_id)
            self.assertIsNone(resolution.command)
            self.assertIn("missing", resolution.warning)

    def test_app_id_matches_startup_wm_class_of_desktop_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            app_dir = tmpdir / "applications"
            app_dir.mkdir()
            (app_dir / "zen-browser.desktop").write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Exec=zen-browser %u\n"
                "StartupWMClass=zen\n",
                encoding="utf-8",
            )

            resolution = resolve_desktop_entry("zen", user_dirs=[app_dir], system_dirs=[])

            self.assertTrue(resolution.resolved)
            self.assertEqual(resolution.desktop_id, "zen-browser.desktop")
            self.assertEqual(resolution.command, ["zen-browser"])

    def test_flatpak_export_desktop_entry_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            flatpak_dir = Path(tmpdir) / "flatpak" / "exports" / "share" / "applications"
            flatpak_dir.mkdir(parents=True)
            (flatpak_dir / "md.obsidian.Obsidian.desktop").write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "X-Flatpak=md.obsidian.Obsidian\n"
                "Exec=flatpak run md.obsidian.Obsidian %U\n",
                encoding="utf-8",
            )

            resolution = resolve_desktop_entry(
                "md.obsidian.Obsidian",
                user_dirs=[flatpak_dir],
                system_dirs=[],
            )

            self.assertTrue(resolution.resolved)
            self.assertEqual(resolution.desktop_id, "md.obsidian.Obsidian.desktop")
            self.assertEqual(resolution.command, ["gtk-launch", "md.obsidian.Obsidian"])

    def test_snapshot_attaches_resolved_desktop_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            user_dir = tmpdir / "applications"
            user_dir.mkdir()
            (user_dir / "alacritty.desktop").write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Exec=alacritty --working-directory %d\n",
                encoding="utf-8",
            )

            outputs = {
                "DP-1": {"name": "DP-1", "make": "Dell Inc.", "model": "U2720Q", "serial": "123"},
            }
            workspaces = [{
                "id": 1,
                "name": "dev-main",
                "output": "DP-1",
                "is_active": True,
                "columns": [{"mode": "split", "width": {"proportion": 1.0}, "windows": [{"app_id": "alacritty"}]}],
            }]

            document = normalize_snapshot(
                "demo",
                outputs,
                workspaces,
                app_dirs=[user_dir],
            )

            window = document["outputs"][0]["workspaces"][0]["columns"][0]["windows"][0]
            self.assertEqual(window["app_id"], "alacritty")
            self.assertEqual(window["desktop_id"], "alacritty.desktop")
            self.assertEqual(window["command"], ["alacritty"])


if __name__ == "__main__":
    unittest.main()
