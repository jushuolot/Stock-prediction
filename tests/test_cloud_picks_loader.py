import json
import tempfile
import unittest
from pathlib import Path

from src.util.cloud_picks_loader import load_cloud_picks


class TestCloudPicksLoader(unittest.TestCase):
    def test_load_valid(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "latest_picks.json"
            p.write_text(
                json.dumps(
                    {
                        "generated_at": "2025-06-08T20:00:00",
                        "picks": [{"code": "600519", "name": "茅台"}],
                    }
                ),
                encoding="utf-8",
            )
            data = load_cloud_picks(p, prefer_remote=False)
            self.assertIsNotNone(data)
            self.assertEqual(len(data["picks"]), 1)

    def test_load_empty(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "latest_picks.json"
            p.write_text('{"picks": [], "generated_at": ""}', encoding="utf-8")
            self.assertIsNone(load_cloud_picks(p, prefer_remote=False))


if __name__ == "__main__":
    unittest.main()
