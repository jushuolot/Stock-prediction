"""score_stock 单元测试。"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.analysis.signals import ScoreBreakdown, score_stock


def _sample_df(n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = 100 + np.cumsum(rng.normal(0.2, 1.0, n))
    return pd.DataFrame(
        {
            "日期": pd.date_range("2024-01-01", periods=n, freq="B").strftime("%Y-%m-%d"),
            "收盘": close,
            "成交量": rng.integers(1_000_000, 3_000_000, n),
        }
    )


class ScoreStockTests(unittest.TestCase):
    def test_score_stock_returns_breakdown(self):
        score = score_stock(_sample_df())
        self.assertIsInstance(score, ScoreBreakdown)
        self.assertGreaterEqual(score.total, -50)
        self.assertLessEqual(score.total, 80)
        self.assertTrue(score.notes)

    def test_score_stock_requires_close_column(self):
        with self.assertRaises(ValueError):
            score_stock(pd.DataFrame({"成交量": [1, 2, 3]}))


if __name__ == "__main__":
    unittest.main()
