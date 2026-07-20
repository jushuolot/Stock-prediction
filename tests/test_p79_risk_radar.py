"""P79 风险雷达单元测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from src.analysis.risk_radar import compute_risk_radar, risk_radar_markdown
from src.analysis.sector_relative import SectorRelativeRow
from src.analysis.signals import ScoreBreakdown
from src.util.query_time import format_query_datetime


class RiskRadarTests(unittest.TestCase):
    def test_returns_three_flags(self):
        snap = {"pct": 1.0, "score": 55.0, "updated_at": format_query_datetime(datetime.now())}
        flags = compute_risk_radar(snap)
        self.assertEqual(len(flags), 3)

    def test_volatility_from_breakdown(self):
        snap = {"pct": 0.5, "score": 55.0, "updated_at": format_query_datetime(datetime.now())}
        bd = ScoreBreakdown(total=55.0, trend=20.0, momentum=5.0, risk=-12.0, liquidity=5.0, notes=[])
        flags = compute_risk_radar(snap, score_breakdown=bd)
        kinds = {f.kind for f in flags}
        self.assertIn("波动", kinds)
        vol = next(f for f in flags if f.kind == "波动")
        self.assertTrue(vol.triggered)
        self.assertIn("波动偏高", vol.message)

    def test_low_score_flag(self):
        snap = {"pct": 0.0, "score": 35.0, "updated_at": format_query_datetime(datetime.now())}
        flags = compute_risk_radar(snap)
        low = next(f for f in flags if f.kind == "评分偏低")
        self.assertTrue(low.triggered)
        self.assertIn("偏低", low.message)

    def test_stale_flag(self):
        old = datetime.now() - timedelta(hours=48)
        snap = {"pct": 1.0, "score": 60.0, "updated_at": format_query_datetime(old)}
        flags = compute_risk_radar(snap, stale_hours=24.0, now=datetime.now())
        stale = next(f for f in flags if f.kind == "stale")
        self.assertTrue(stale.triggered)
        self.assertIn("过期", stale.message)

    def test_underperform_sector(self):
        snap = {"pct": -2.0, "score": 50.0, "updated_at": format_query_datetime(datetime.now())}
        sr = SectorRelativeRow(
            code="600519",
            name="茅台",
            sector="白酒",
            ticker_pct=-2.0,
            ticker_score=50.0,
            sector_avg_pct=3.0,
            sector_avg_score=68.0,
            pct_vs_sector=-5.0,
            score_vs_sector=-18.0,
            label="跑输板块",
            fool_conclusion="相对同板块自选，涨跌幅或评分至少一项明显偏弱。",
        )
        flags = compute_risk_radar(snap, sector_relative=sr)
        sector = next(f for f in flags if f.kind == "跑输板块")
        self.assertTrue(sector.triggered)

    def test_prioritize_triggered(self):
        snap = {"pct": -6.0, "score": 35.0, "updated_at": format_query_datetime(datetime.now() - timedelta(hours=48))}
        flags = compute_risk_radar(snap, stale_hours=24.0, now=datetime.now())
        triggered = [f for f in flags if f.triggered]
        self.assertGreaterEqual(len(triggered), 2)
        self.assertTrue(all(f.triggered for f in flags[: len(triggered)]))

    def test_markdown_plain_chinese(self):
        snap = {"pct": 1.0, "score": 55.0, "updated_at": format_query_datetime(datetime.now())}
        md = risk_radar_markdown(compute_risk_radar(snap), name="茅台", code="600519")
        self.assertIn("600519", md)
        self.assertIn("波动", md)


if __name__ == "__main__":
    unittest.main()
