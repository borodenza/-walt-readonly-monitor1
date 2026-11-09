import unittest

import walt_market_analysis as scanner


class IndicatorTests(unittest.TestCase):
    def test_ema_constant_sequence(self):
        self.assertAlmostEqual(scanner.ema([7.0] * 100, 20)[-1], 7.0)

    def test_rsi_constant_sequence(self):
        self.assertEqual(scanner.rsi([7.0] * 100), 50.0)

    def test_rsi_rising_sequence(self):
        self.assertEqual(scanner.rsi([float(i) for i in range(100)]), 100.0)

    def test_no_real_order_imports(self):
        self.assertFalse(hasattr(scanner, "place_order"))
        self.assertEqual(scanner.ASSETS, ("BTCUSDT", "ETHUSDT"))


if __name__ == "__main__":
    unittest.main()
