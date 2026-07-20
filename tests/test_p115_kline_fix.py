import unittest
from unittest.mock import MagicMock

import numpy
import pandas as pd

from src.analysis.tomorrow_picks import rank_tomorrow_a_picks
from src.providers.market_data import _normalize_kline_period


class TestP115KlineFix(unittest.TestCase):
    def test_normalize_daily(self):
        self.assertEqual(_normalize_kline_period("daily"), "日线")
        self.assertEqual(_normalize_kline_period("日K"), "日K")

    def test_rank_uses_日线_for_fetch(self):
        universe = pd.DataFrame(
            [
                {
                    "代码": "600519",
                    "名称": "贵州茅台",
                    "涨跌幅%": 2.0,
                    "换手率%": 1.0,
                }
            ]
        )
        n = 60
        close = 10.0 + numpy.cumsum(numpy.linspace(0.01, 0.5, n))
        df = pd.DataFrame({"收盘": close, "成交量": numpy.full(n, 1e6)})

        fetch_fn = MagicMock(return_value=(df, "新浪财经"))
        picks, stats = rank_tomorrow_a_picks(universe, fetch_fn, max_scan=5, max_picks=3)
        self.assertEqual(stats.get("errors"), 0)
        fetch_fn.assert_called()
        self.assertEqual(fetch_fn.call_args.kwargs.get("kline"), "日线")


if __name__ == "__main__":
    unittest.main()
