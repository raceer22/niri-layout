import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from niri_layout import NiriIPCError, NiriIPCJSONError
from niri_layout.ipc import query_niri


class QueryNiriTests(unittest.TestCase):
    def test_query_niri_uses_expected_subprocess_and_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = ["niri", "msg", "--json", "outputs"]
            payload = [{"identifier": {"make": "Dell"}}]
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = subprocess.CompletedProcess(
                    cmd, 0, stdout=json.dumps(payload), stderr=""
                )
                result = query_niri("outputs", runner=mock_run)
                self.assertEqual(result, payload)
                mock_run.assert_called_once_with(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )

    def test_query_niri_raises_on_nonzero_return_code(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                ["niri", "msg", "--json", "outputs"], 1, stdout='', stderr='bad'
            )
            with self.assertRaises(NiriIPCError):
                query_niri("outputs", runner=mock_run)

    def test_query_niri_raises_on_invalid_json(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                ["niri", "msg", "--json", "outputs"], 0, stdout='not-json', stderr=''
            )
            with self.assertRaises(NiriIPCJSONError):
                query_niri("outputs", runner=mock_run)


if __name__ == "__main__":
    unittest.main()
