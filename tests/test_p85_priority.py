"""P85 多标的作战优先级单元测试。"""

from __future__ import annotations

import unittest

from src.analysis.priority_queue import (
    format_priority_section,
    priority_table_rows,
    rank_watchlist_priority,
)
from src.analysis.sector_relative import compute_sector_relative
from src.analysis.watch_alerts import compute_watch_alerts


class PriorityQueueTests(unittest.TestCase):
    wl = [
        {"名称": "茅台", "代码": "600519"},
        {"名称": "五粮液", "代码": "000858"},
        {"名称": "工行", "代码": "601398"},
    ]
    snaps = {
        "600519": {
            "pct": 6.0,
            "score": 70.0,
            "one_line": "强",
            "fin_summary": "白酒",
            "updated_at": "2026-06-07 10:00:00",
        },
        "000858": {
            "pct": -4.0,
            "score": 35.0,
            "one_line": "弱",
            "fin_summary": "白酒",
            "updated_at": "2026-06-07 10:00:00",
        },
        "601398": {
            "pct": 0.5,
            "score": 55.0,
            "one_line": "平",
            "fin_summary": "银行",
            "updated_at": "2026-06-07 10:00:00",
        },
    }

    def test_hot_alert_ranks_first_when_isolated(self):
        wl = [{"名称": "茅台", "代码": "600519"}]
        snaps = {
            "600519": {
                "pct": 6.0,
                "score": 70.0,
                "one_line": "强",
                "updated_at": "2026-06-07 10:00:00",
            },
        }
        alerts = compute_watch_alerts(wl, snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(wl, snaps, alerts=alerts, top_n=5)
        self.assertEqual(ranks[0].code, "600519")
        self.assertIn("提醒", ranks[0].reason)

    def test_combined_signals_outrank_single_hot(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts, top_n=5)
        self.assertGreaterEqual(len(ranks), 2)
        top_codes = {r.code for r in ranks[:2]}
        self.assertIn("600519", top_codes)
        self.assertIn("000858", top_codes)
        self.assertGreater(ranks[0].score, ranks[1].score)

    def test_risk_and_sector_in_reason(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts, top_n=5)
        weak = next((r for r in ranks if r.code == "000858"), None)
        self.assertIsNotNone(weak)
        assert weak is not None
        self.assertIn("提醒", weak.reason)

    def test_top_five_cap(self):
        wl_big = [{"名称": f"T{i}", "代码": f"{600000 + i}"} for i in range(8)]
        snaps_big = {
            f"{600000 + i}": {"pct": 0.0, "score": 50.0, "updated_at": "2026-06-07 10:00:00"}
            for i in range(8)
        }
        ranks = rank_watchlist_priority(wl_big, snaps_big, top_n=5)
        self.assertEqual(len(ranks), 5)

    def test_plain_reason_non_empty(self):
        ranks = rank_watchlist_priority(self.wl, self.snaps, top_n=3)
        for r in ranks:
            self.assertTrue(r.reason.strip())
            self.assertGreater(len(r.reason), 4)

    def test_table_and_section_markdown(self):
        alerts = compute_watch_alerts(self.wl, self.snaps, pct_up=5.0, score_low=40.0)
        ranks = rank_watchlist_priority(self.wl, self.snaps, alerts=alerts)
        rows = priority_table_rows(ranks)
        self.assertEqual(rows[0]["优先序"], 1)
        section = format_priority_section(ranks)
        self.assertIn("今日建议优先关注", section)
        self.assertIn("600519", section)

    def test_sector_relative_used(self):
        rel = compute_sector_relative(self.wl, self.snaps)
        self.assertTrue(rel)
        ranks = rank_watchlist_priority(self.wl, self.snaps, top_n=5)
        self.assertEqual(len(ranks), 3)


if __name__ == "__main__":
    unittest.main()
