import unittest

from src.ui.simple_result import (
    overall_verdict,
    plain_pct_label,
    plain_score_label,
)


class TestSimpleResult(unittest.TestCase):
    def test_plain_score(self):
        self.assertEqual(plain_score_label(70), "偏强")
        self.assertEqual(plain_score_label(50), "中性")
        self.assertEqual(plain_score_label(30), "偏弱")
        self.assertEqual(plain_score_label(None), "待分析")

    def test_plain_pct(self):
        self.assertIn("上涨", plain_pct_label(5.2))
        self.assertIn("下跌", plain_pct_label(-4.1))

    def test_overall_verdict_strong(self):
        title, _, level = overall_verdict(72, 2.0)
        self.assertEqual(title, "整体偏强")
        self.assertEqual(level, "good")

    def test_overall_verdict_weak(self):
        title, _, level = overall_verdict(35, -1.0)
        self.assertEqual(title, "需要留意")
        self.assertEqual(level, "bad")


if __name__ == "__main__":
    unittest.main()
