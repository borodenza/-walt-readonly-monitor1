import unittest
from unittest.mock import patch
import walt_market_analysis as scanner

class FuturesScannerTests(unittest.TestCase):
    def test_ema_constant_sequence(self):
        self.assertAlmostEqual(scanner.ema([7.0]*100,20)[-1],7.0)

    def test_rsi_constant_sequence(self):
        self.assertEqual(scanner.rsi([7.0]*100),50.0)

    def test_rsi_rising_sequence(self):
        self.assertEqual(scanner.rsi([float(i) for i in range(100)]),100.0)

    def test_only_mira_futures_strategy(self):
        self.assertEqual(scanner.ASSETS,scanner.MIRA_ASSETS)
        self.assertEqual(len(scanner.ASSETS),8)
        self.assertTrue(scanner.BASE_URL.startswith('https://fapi.binance.com/'))
        self.assertFalse(hasattr(scanner,'evaluate_a'))
        self.assertFalse(hasattr(scanner,'perps_execute_operation'))

    def test_scan_fail_closed_when_futures_unreachable(self):
        with patch.object(scanner,'fetch_candles',side_effect=OSError('API unavailable')):
            result=scanner.scan()
        self.assertEqual(result['strategy'],'MIRA_RECOVERY_ONLY')
        self.assertEqual(result['execution'],'DISABLED')
        self.assertFalse(result['mira']['ok'])
        self.assertEqual(result['mira']['proposals'],[])
        self.assertNotIn('assets',result)
        self.assertNotIn('A',result['limits'])
        
if __name__=='__main__':unittest.main()
