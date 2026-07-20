import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

from src.util.cloud_picks_loader import _normalize_payload, load_cloud_picks


class TestBuddhaSelfCheck(unittest.TestCase):
    def test_script_runs(self):
        r = subprocess.run(
            [sys.executable, "scripts/buddha_self_check.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)


class TestCloudRemoteLoader(unittest.TestCase):
    def test_normalize_requires_content(self):
        self.assertIsNone(_normalize_payload({"picks": [], "generated_at": ""}))

    @patch("src.util.cloud_picks_loader._load_local")
    @patch("src.util.cloud_picks_loader.is_streamlit_cloud", return_value=False)
    def test_prefers_local_when_not_cloud(self, _cloud, mock_local):
        mock_local.return_value = {"picks": [{"code": "1"}], "generated_at": "x"}
        data = load_cloud_picks()
        self.assertEqual(len(data["picks"]), 1)


if __name__ == "__main__":
    unittest.main()
