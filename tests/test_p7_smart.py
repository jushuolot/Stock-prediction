"""P7 sector_linkage 与 readonly_snapshot 单元测试。"""

from __future__ import annotations

import json
import unittest

from src.analysis.sector_linkage import analyze_plate_rows, build_linkage_alerts, links_from_accumulator
from src.export.readonly_snapshot import build_readonly_snapshot, snapshot_to_json_bytes


class SectorLinkageTests(unittest.TestCase):
    def test_shared_plate(self):
        rows = [
            {"stock_code": "600519", "stock_name": "茅台", "plate_code": "BK001", "plate_name": "白酒", "pct": 2.0},
            {"stock_code": "000858", "stock_name": "五粮液", "plate_code": "BK001", "plate_name": "白酒", "pct": 1.5},
        ]
        links = links_from_accumulator(analyze_plate_rows(rows))
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].count, 2)
        alerts = build_linkage_alerts(links)
        self.assertTrue(any("白酒" in a for a in alerts))


class ReadonlySnapshotTests(unittest.TestCase):
    def test_snapshot_json(self):
        snap = build_readonly_snapshot(
            watchlist=[{"名称": "测试", "代码": "000001"}],
            watch_snapshots={"000001": {"score": 50.0}},
            briefs={"000001": "# hi"},
        )
        raw = snapshot_to_json_bytes(snap)
        data = json.loads(raw.decode("utf-8"))
        self.assertEqual(data["schema"], "stock-assistant-readonly-v2")
        self.assertEqual(data["counts"]["briefs"], 1)


if __name__ == "__main__":
    unittest.main()
