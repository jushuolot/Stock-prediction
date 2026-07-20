import unittest
from unittest.mock import patch

from src.analysis.stock_quality import evaluate_stock_quality
from src.providers.eastmoney_fund_holdings import FundHoldingsSnapshot
from src.providers.eastmoney_shareholder import ShareholderSnapshot


class TestStockQuality(unittest.TestCase):
    def test_reject_locked_top1(self):
        sh = ShareholderSnapshot(
            code="301418",
            holder_count=8000,
            hold_focus="非常集中",
            top1_name="测试",
            top1_ratio=35.0,
            top1_locked=True,
            top3_ratio=60.0,
            free_top_ratio=17.0,
            holder_chg_pct=3.0,
        )
        v = evaluate_stock_quality(
            "301418", shareholder=sh, fetch_shareholder=False, fetch_fund_holdings=False, fetch_f10=False
        )
        self.assertFalse(v.ok)
        self.assertIn("限售", v.reject_reason)

    def test_main_board_bonus(self):
        sh = ShareholderSnapshot(
            code="600519",
            holder_count=200000,
            hold_focus="非常分散",
            top1_name="集团",
            top1_ratio=54.0,
            top1_locked=False,
            top3_ratio=70.0,
            free_top_ratio=68.0,
            holder_chg_pct=-2.0,
        )
        v = evaluate_stock_quality(
            "600519", shareholder=sh, fetch_shareholder=False, fetch_fund_holdings=False, fetch_f10=False
        )
        self.assertTrue(v.ok)
        self.assertGreater(v.score_delta, 0)

    def test_fund_new_entry_bonus(self):
        sh = ShareholderSnapshot(
            code="600519",
            holder_count=100000,
            hold_focus="非常分散",
            top1_name="集团",
            top1_ratio=54.0,
            top1_locked=False,
            top3_ratio=70.0,
            free_top_ratio=68.0,
            holder_chg_pct=1.0,
        )
        fh = FundHoldingsSnapshot(
            code="600519",
            report_date="2025-12-31",
            fund_chg="新进",
            fund_chg_shares=1_000_000,
            fund_hold_ratio=2.5,
            fund_org_count=20,
            fund_ratio_chg=0.8,
            fund_count_chg=8,
            qfii_chg="新进",
            qfii_hold_ratio=0.5,
            inst_net_chg_shares=500_000,
            inst_hold_ratio=10.0,
            inst_org_count=50,
        )
        v = evaluate_stock_quality(
            "600519",
            shareholder=sh,
            fund_holdings=fh,
            fetch_shareholder=False,
            fetch_fund_holdings=False,
            fetch_f10=False,
        )
        self.assertTrue(v.ok)
        self.assertIn("公募基金新进", v.tags)
        self.assertIn("QFII新进", v.tags)
        self.assertGreater(v.score_delta, 8)

    def test_fund_reduce_penalty(self):
        sh = ShareholderSnapshot(
            code="301418",
            holder_count=15000,
            hold_focus="集中",
            top1_name="测试",
            top1_ratio=30.0,
            top1_locked=False,
            top3_ratio=50.0,
            free_top_ratio=40.0,
            holder_chg_pct=0.0,
        )
        fh = FundHoldingsSnapshot(
            code="301418",
            report_date="2026-03-31",
            fund_chg="减仓",
            fund_chg_shares=-200_000,
            fund_hold_ratio=1.1,
            fund_org_count=4,
            fund_ratio_chg=-0.6,
            fund_count_chg=-59,
            qfii_chg="—",
            qfii_hold_ratio=None,
            inst_net_chg_shares=200_000,
            inst_hold_ratio=3.2,
            inst_org_count=6,
        )
        base = evaluate_stock_quality(
            "301418",
            shareholder=sh,
            fund_holdings=None,
            fetch_shareholder=False,
            fetch_fund_holdings=False,
            fetch_f10=False,
        )
        v = evaluate_stock_quality(
            "301418",
            shareholder=sh,
            fund_holdings=fh,
            fetch_shareholder=False,
            fetch_fund_holdings=False,
            fetch_f10=False,
        )
        self.assertIn("基金减持", v.tags)
        self.assertIn("基金家数减", v.tags)
        self.assertLess(v.score_delta, base.score_delta)


if __name__ == "__main__":
    unittest.main()
