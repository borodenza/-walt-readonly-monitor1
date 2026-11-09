import unittest
from mira import candidate, daily_queue, monitor_recovery


class MiraTests(unittest.TestCase):
    def test_queue_is_stable_across_retries(self):
        events = [dict(symbol=s, closed_ms=i) for i, s in enumerate("AABCD")]
        self.assertEqual([e["symbol"] for e in daily_queue(reversed(events))], list("ABC"))

    def test_partial_coverage_blocks_queue(self):
        def offline(*args, **kwargs):
            raise OSError("offline")
        result = monitor_recovery(["BTCUSDT"], offline, 0)
        self.assertFalse(result["ok"])
        self.assertEqual(result["proposals"], [])

    def test_volume_and_recovery_required(self):
        bars = [dict(close=100, low=99, high=101, volume=2, end_ms=i) for i in range(700)]
        bars[-673]["close"] = 90
        for b in bars[-65:]:
            b.update(close=90, low=89, high=91)
        bars[-1].update(close=94, low=90, high=95, volume=5)
        self.assertIsNotNone(candidate("BTCUSDT", bars, len(bars)-1))
        bars[-1]["volume"] = 0
        self.assertIsNone(candidate("BTCUSDT", bars, len(bars)-1))

