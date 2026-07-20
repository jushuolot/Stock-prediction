"""P29 摘要刷新缓存单元测试。"""

from __future__ import annotations

import unittest

from src.util.fetch_cache import (
    batch_cache_key,
    clear_fetch_cache,
    get_cached_snapshots,
    set_cached_snapshots,
)


class FetchCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_fetch_cache()

    def tearDown(self) -> None:
        clear_fetch_cache()

    def test_batch_cache_key_order_independent(self):
        self.assertEqual(
            batch_cache_key(["601398", "600519"]),
            batch_cache_key(["600519", "601398"]),
        )

    def test_cache_hit_within_ttl(self):
        codes = ["600519", "601398"]
        payload = {"600519": {"pct": 1.0}, "601398": {"pct": -0.5}}
        set_cached_snapshots(codes, payload, now=1000.0)
        hit = get_cached_snapshots(codes, ttl=60.0, now=1040.0)
        self.assertEqual(hit, payload)

    def test_cache_miss_after_ttl(self):
        codes = ["600519"]
        set_cached_snapshots(codes, {"600519": {"pct": 1.0}}, now=1000.0)
        miss = get_cached_snapshots(codes, ttl=60.0, now=1061.0)
        self.assertIsNone(miss)

    def test_different_batches_different_keys(self):
        set_cached_snapshots(["600519"], {"600519": {"pct": 1.0}}, now=1000.0)
        self.assertIsNone(get_cached_snapshots(["601398"], ttl=60.0, now=1020.0))


if __name__ == "__main__":
    unittest.main()
