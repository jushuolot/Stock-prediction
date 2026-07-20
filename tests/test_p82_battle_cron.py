"""P82 作战清单 cron 单元测试。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.battle_plan_cron import load_store, main, plan_output_path  # noqa: E402


class BattlePlanCronTests(unittest.TestCase):
    def _sample_store(self) -> dict:
        return {
            "watchlist": [{"名称": "茅台", "代码": "600519"}],
            "query_log": [],
            "latest": {
                "watch_snapshots": {
                    "600519": {"pct": 6.0, "score": 70.0, "updated_at": "2026-06-07 10:00:00"},
                },
                "user_prefs": {"alert_pct_up": 5.0},
            },
        }

    def test_plan_output_path_default(self):
        path = plan_output_path(user_id="default", now=datetime(2026, 6, 7))
        self.assertTrue(str(path).endswith("battle_plan_20260607.md"))
        self.assertIn("/data/", str(path).replace("\\", "/"))

    def test_plan_output_path_user(self):
        path = plan_output_path(user_id="alice", now=datetime(2026, 6, 7))
        self.assertIn("/users/alice/", str(path).replace("\\", "/"))

    def test_main_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "user_history.json"
            hist.write_text(json.dumps(self._sample_store()), encoding="utf-8")
            out_dir = Path(tmp) / "data"
            with patch("scripts.battle_plan_cron.history_file_path", return_value=hist):
                with patch("scripts.battle_plan_cron.project_root", return_value=Path(tmp)):
                    with patch.dict(os.environ, {"STOCK_USER": "default"}, clear=False):
                        rc = main()
            self.assertEqual(rc, 0)
            files = list(out_dir.glob("battle_plan_*.md"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            self.assertIn("# 📋 今日作战清单", content)
            self.assertIn("600519", content)

    def test_main_stdout(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self._sample_store(), f)
            hist = Path(f.name)
        try:
            with patch("scripts.battle_plan_cron.history_file_path", return_value=hist):
                with patch.dict(os.environ, {"STOCK_USER": "default"}, clear=False):
                    with patch("sys.argv", ["battle_plan_cron.py", "--stdout"]):
                        from io import StringIO

                        buf = StringIO()
                        with patch("sys.stdout", buf):
                            rc = main()
            self.assertEqual(rc, 0)
            self.assertIn("# 📋 今日作战清单", buf.getvalue())
        finally:
            hist.unlink(missing_ok=True)

    def test_load_store_missing(self):
        with self.assertRaises(FileNotFoundError):
            load_store("missing-user-xyz")


if __name__ == "__main__":
    unittest.main()
