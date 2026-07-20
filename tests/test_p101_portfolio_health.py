"""P101 自选健康分单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from src.analysis.portfolio_health import (
    compute_portfolio_health,
    portfolio_health_markdown,
)


def _fresh_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class PortfolioHealthTests(unittest.TestCase):
    def test_healthy_portfolio_high_score(self):
        wl = [
            {"名称": "A", "代码": "1"},
            {"名称": "B", "代码": "2"},
            {"名称": "C", "代码": "3"},
            {"名称": "D", "代码": "4"},
        ]
        snaps = {
            "1": {"pct": 1.0, "score": 58.0, "sector": "银行", "updated_at": _fresh_ts()},
            "2": {"pct": 0.5, "score": 55.0, "sector": "医药", "updated_at": _fresh_ts()},
            "3": {"pct": -0.5, "score": 60.0, "sector": "科技", "updated_at": _fresh_ts()},
            "4": {"pct": 0.0, "score": 62.0, "sector": "消费", "updated_at": _fresh_ts()},
        }
        health = compute_portfolio_health(
            wl,
            snaps,
            pct_up=5.0,
            pct_down=-5.0,
            score_low=40.0,
            score_high=65.0,
            stale_hours=24.0,
        )
        self.assertGreaterEqual(health.score, 70)
        self.assertEqual(health.label, "健康")
        self.assertAlmostEqual(health.avg_score or 0, (58 + 55 + 60 + 62) / 4, places=1)

    def test_attention_when_many_alerts_and_stale(self):
        wl = [
            {"名称": "A", "代码": "1"},
            {"名称": "B", "代码": "2"},
        ]
        old = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
        snaps = {
            "1": {"pct": 8.0, "score": 30.0, "sector": "银行", "updated_at": old},
            "2": {"pct": -7.0, "score": 35.0, "sector": "银行", "updated_at": old},
        }
        health = compute_portfolio_health(
            wl,
            snaps,
            pct_up=5.0,
            pct_down=-5.0,
            score_low=40.0,
            score_high=65.0,
            stale_hours=24.0,
        )
        self.assertLess(health.score, 45)
        self.assertEqual(health.label, "需关注")
        self.assertGreater(health.alert_ratio, 0.0)
        self.assertGreater(health.stale_ratio, 0.0)

    def test_empty_watchlist(self):
        health = compute_portfolio_health([], {})
        self.assertEqual(health.score, 0)
        self.assertEqual(health.label, "需关注")
        self.assertEqual(health.watch_count, 0)

    def test_markdown_contains_score_and_label(self):
        wl = [{"名称": "A", "代码": "1"}]
        snaps = {"1": {"pct": 0.0, "score": 60.0, "sector": "银行", "updated_at": _fresh_ts()}}
        health = compute_portfolio_health(wl, snaps)
        md = portfolio_health_markdown(health)
        self.assertIn(str(health.score), md)
        self.assertIn(health.label, md)
        self.assertIn("均分", md)


if __name__ == "__main__":
    unittest.main()
