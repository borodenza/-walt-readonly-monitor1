import unittest
from decimal import Decimal
from walt_guard import RiskInputError, minimum_cost_floor, scenario

BTC={
    'quote_asset':'USDC','is_active':True,'price_slippage':'0.01',
    'taker_fee_pct':'0.0009','min_size_base':'0.00007','step_size':'0.00001',
    'min_size_quote':'1','max_size_quote':'25000','funding_rate_hourly':'0.000096'}
ETH=dict(BTC,min_size_base='0.002',step_size='0.0001')
class MiraRiskGuardTests(unittest.TestCase):
    def test_min_size_slippage_cost_has_been_accounted_for(self):
        for contract,price in ((BTC,'74223.6'),(ETH,'2106.29')):
            floor=minimum_cost_floor(contract,price)
            self.assertGreater(Decimal(floor['round_trip_slippage_and_taker_fee_usdc']),Decimal('.09'))
            self.assertFalse(floor['trade_ready'])
    def test_risk_can_exceed_mira_limit_with_stop(self):
        x=scenario(BTC,side='long',reference_price='74223.6',stop_price='72500',
            target_price='81000',margin_usdc='9')
        self.assertGreater(Decimal(x['stress_loss_usdc']),Decimal('.18'))
        self.assertFalse(x['trade_ready'])
    def test_no_trading_authorized_even_for_high_rr(self):
        x=scenario(ETH,side='long',reference_price='2106.29',
            stop_price='2095',target_price='4000',margin_usdc='9')
        self.assertFalse(x['trade_ready'])
    def test_invalid_stop_rejected(self):
        with self.assertRaises(RiskInputError):
            scenario(BTC,side='short',reference_price='74223.6',
                stop_price='74000',target_price='75000',margin_usdc='9')
    def test_small_margin_fails_min_size(self):
        with self.assertRaises(RiskInputError):
            scenario(BTC,side='long',reference_price='74223.6',
                stop_price='74000',target_price='76000',margin_usdc='1')

if __name__=='__main__':unittest.main()
