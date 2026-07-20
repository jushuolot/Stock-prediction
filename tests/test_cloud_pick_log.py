import unittest
from unittest.mock import MagicMock

import pandas as pd

from src.storage.cloud_pick_log import load_cloud_pick_log, save_cloud_pick_log, sync_cloud_pick_log


class TestCloudPickLog(unittest.TestCase):
    def test_append_and_summary(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cloud_pick_log.json"

            def fetch_fn(item, **kwargs):
                dates = pd.date_range("2020-01-01", periods=5, freq="B")
                df = pd.DataFrame(
                    {
                        "日期": dates,
                        "收盘": [100.0, 101.0, 102.0, 103.0, 104.0],
                        "成交量": [1e6] * 5,
                    }
                )
                return df, "test"

            picks = [
                {
                    "code": "600519",
                    "name": "茅台",
                    "signal": "明日偏多",
                    "score": 80,
                    "pct": 1.0,
                    "hold_days": "1",
                    "reason": "[趋势延续] test",
                    "pattern": "趋势延续",
                }
            ]
            meta = sync_cloud_pick_log(
                picks,
                pick_day="2020-01-01",
                fetch_fn=fetch_fn,
                path=path,
            )
            self.assertEqual(len(meta["log"]), 1)
            self.assertIn("hit_summary", meta)
            loaded = load_cloud_pick_log(path=path)
            self.assertEqual(len(loaded), 1)
            save_cloud_pick_log(loaded, path=path)
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
