import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from niri_layout.cli import main


class ExportCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tmpdir.name)
        self.addCleanup(self.tmpdir.cleanup)

    def _write_layout(self, name: str, payload: dict | None = None):
        layout_dir = self.home / ".config" / "niri" / "layouts"
        layout_dir.mkdir(parents=True, exist_ok=True)
        if payload is None:
            payload = {"name": name, "version": 1, "outputs": []}
        (layout_dir / f"{name}.json").write_text(__import__("json").dumps(payload), encoding="utf-8")

    def test_export_generates_executable_restore_script_for_requested_layout(self):
        self._write_layout("demo")
        output_path = self.home / "bin" / "launch demo.sh"

        rc = main(["export", "demo", str(output_path)], env={"HOME": str(self.home)})

        self.assertEqual(rc, 0)
        self.assertTrue(output_path.exists())
        self.assertTrue(os.access(output_path, os.X_OK))
        script = output_path.read_text(encoding="utf-8")
        self.assertIn("#!/bin/sh", script)
        self.assertIn("niri-layout restore 'demo'", script)
        self.assertNotIn(str(self.home), script)
        self.assertNotIn("python", script.lower())

    def test_export_quotes_layout_names_and_paths_with_metacharacters(self):
        layout_name = 'demo; echo "oops"'
        self._write_layout(layout_name)
        output_path = self.home / "bin" / "launch; demo.sh"

        rc = main(["export", layout_name, str(output_path)], env={"HOME": str(self.home)})

        self.assertEqual(rc, 0)
        script = output_path.read_text(encoding="utf-8")
        self.assertIn("niri-layout restore 'demo; echo \"oops\"'", script)
        self.assertTrue(output_path.exists())

    def test_export_overwrites_existing_target_atomically(self):
        self._write_layout("demo")
        output_path = self.home / "launch.sh"
        output_path.write_text("old payload\n", encoding="utf-8")

        rc = main(["export", "demo", str(output_path)], env={"HOME": str(self.home)})

        self.assertEqual(rc, 0)
        self.assertNotEqual(output_path.read_text(encoding="utf-8"), "old payload\n")
        self.assertTrue(os.access(output_path, os.X_OK))

    def test_export_rejects_missing_layout_before_touching_destination(self):
        output_path = self.home / "missing.sh"

        with self.assertRaises(FileNotFoundError):
            main(["export", "missing", str(output_path)], env={"HOME": str(self.home)})

        self.assertFalse(output_path.exists())

    def test_generated_script_runs_using_fake_path_binary(self):
        self._write_layout("demo")
        fake_bin = self.home / "fake-bin"
        fake_bin.mkdir(parents=True, exist_ok=True)
        log_path = self.home / "niri-call.log"
        fake_niri = fake_bin / "niri-layout"
        fake_niri.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' \"$@\" > \"$HOME/niri-call.log\"\n",
            encoding="utf-8",
        )
        fake_niri.chmod(fake_niri.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        output_path = self.home / "launch.sh"
        rc = main(["export", "demo", str(output_path)], env={"HOME": str(self.home), "PATH": str(fake_bin)})
        self.assertEqual(rc, 0)

        working_dir = self.home / "elsewhere"
        working_dir.mkdir(parents=True, exist_ok=True)
        env = {"HOME": str(self.home), "PATH": str(fake_bin)}
        subprocess.run([str(output_path)], cwd=str(working_dir), env=env, check=True)

        logged = log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(logged[0], "restore")
        self.assertEqual(logged[1], "demo")


if __name__ == "__main__":
    unittest.main()
