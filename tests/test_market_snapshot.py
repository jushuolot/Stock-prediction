import unittest

import pandas as pd

from src.analysis.market_snapshot import (
    capture_market_snapshot,
    diff_snapshots,
    rows_from_universe,
    select_deep_candidates,
)


class TestMarketSnapshot(unittest.TestCase):
    def test_diff_and_select(self):
        df = pd.DataFrame(
            [
                {"代码": "600519", "名称": "茅台", "涨跌幅%": 1.0},
                {"代码": "000001", "名称": "平安", "涨跌幅%": 2.0},
            ]
        )
        prev = capture_market_snapshot(df, day="2026-06-01")
        curr_rows = rows_from_universe(df)
        for r in curr_rows:
            if r["code"] == "600519":
                r["pct"] = 3.0
            if r["code"] == "000001":
                r["pct"] = 1.0
        curr = {"date": "2026-06-02", "rows": curr_rows}
        diff = diff_snapshots(
            prev,
            curr,
            yesterday_picks=[{"code": "600519", "name": "茅台", "signal": "明日偏多"}],
        )
        self.assertEqual(diff.compared, 2)
        self.assertTrue(diff.pick_checks)
        sub, reasons = select_deep_candidates(df, diff.as_dict(), yesterday_picks=[{"code": "600519"}])
        self.assertFalse(sub.empty)


if __name__ == "__main__":
    unittest.main()
