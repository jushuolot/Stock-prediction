"""P40 i18n lite 单元测试。"""

from __future__ import annotations

import unittest

from src.util.i18n_strings import (
    DEFAULT_LOCALE,
    get_locale,
    normalize_locale,
    t,
    tab_label,
    tab_order,
)


class I18nStringsTests(unittest.TestCase):
    def test_normalize_locale(self):
        self.assertEqual(normalize_locale("zh"), "zh")
        self.assertEqual(normalize_locale("EN"), "en")
        self.assertEqual(normalize_locale("fr"), DEFAULT_LOCALE)
        self.assertEqual(normalize_locale(None), DEFAULT_LOCALE)

    def test_tab_labels_zh_en(self):
        self.assertIn("自选", tab_label("watch", locale="zh"))
        self.assertIn("Watchlist", tab_label("watch", locale="en"))
        self.assertIn("发现", tab_label("search", locale="zh"))
        self.assertIn("Discover", tab_label("search", locale="en"))

    def test_tab_order_count(self):
        self.assertEqual(len(tab_order(locale="zh")), 4)
        self.assertEqual(len(tab_order(locale="en")), 4)

    def test_dashboard_metrics(self):
        self.assertEqual(t("dash_watch", locale="zh"), "自选")
        self.assertEqual(t("dash_watch", locale="en"), "Watchlist")
        self.assertEqual(t("dash_alerts", locale="en"), "Alerts Today")

    def test_get_locale_from_dict(self):
        self.assertEqual(get_locale({"locale": "en"}), "en")
        self.assertEqual(get_locale({}), DEFAULT_LOCALE)


if __name__ == "__main__":
    unittest.main()
