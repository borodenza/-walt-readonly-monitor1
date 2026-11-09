import unittest
import datetime as dt
from walt_status import WATCH, build_status, to_html

class MiraStatusTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,11,9,9,45,tzinfo=dt.timezone.utc)
        ms=int(self.now.timestamp()*1000)
        self.report={
            'mode':'READ_ONLY_RESEARCH', 'execution':'DISABLED',
            'strategy':'MIRA_RECOVERY_ONLY',
            'source':'Binance USDS-M futures public klines',
            'generated_utc':'2026-11-09T09:40:00+00:00',
            'mira':{
                'ok':True,'observations':{k:{'futures_close':12,'change24_pct':-6} for k in WATCH},
                'proposals':[{'symbol':'ETHUSDT','closed_ms':ms-100000,
                              'expires_ms':ms+800000,'futures_close':12,'change24_pct':-6}]}}
    def test_only_mira_exists_and_auto_is_disabled(self):
        x=build_status(self.report,self.now)
        self.assertEqual(x['strategy'],'MIRA_RECOVERY_ONLY')
        self.assertNotIn('strategy_a',x)
        self.assertFalse(x['auto_trade_enabled'])
        self.assertFalse(x['trade_ready'])
        self.assertEqual(len(x['research_candidates']),1)
    def test_expired_candidates_ignored(self):
        self.report['mira']['proposals'][0]['expires_ms']=int(self.now.timestamp()*1000)-1
        self.assertFalse(build_status(self.report,self.now)['research_candidates'])
    def test_old_report_stops_candidates(self):
        x=build_status(self.report,self.now+dt.timedelta(hours=1))
        self.assertFalse(x['market_data_ok'])
        self.assertEqual(x['research_candidates'],[])
    def test_partial_market_coverage_fails_closed(self):
        del self.report['mira']['observations']['BTCUSDT']
        self.assertFalse(build_status(self.report,self.now)['market_data_ok'])
    def test_untrusted_executable_report_rejected(self):
        self.report['execution']='ENABLED'
        self.assertFalse(build_status(self.report,self.now)['fresh_at_check'])
    def test_static_html_no_controls(self):
        h=to_html(build_status(self.report,self.now))
        self.assertIn('Автоматическая торговля НЕ включена',h)
        self.assertNotIn('<script',h)
        self.assertNotIn('Подтвердить',h)

if __name__=='__main__':unittest.main()
