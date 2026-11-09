import unittest
import datetime as dt
from walt_status import build_status, to_html

class StatusTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 11, 9, 9, 45, tzinfo=dt.timezone.utc)
        self.report = {'mode':'READ_ONLY_RESEARCH','execution':'DISABLED',
                       'generated_utc':'2026-11-09T09:40:00+00:00',
                       'assets':{'BTCUSDT':{'strategy_a':'Условный технический кандидат LONG',
                                          'timeframes':{'1h':{}}}},
                       'mira':{'ok':True,'proposals':[{'symbol':'BTCUSDT'}]}}
    def test_never_trade_ready_even_for_candidate(self):
        r=build_status(self.report, self.now)
        self.assertEqual(r['strategy_a']['assets']['BTCUSDT']['state'], 'RESEARCH_CANDIDATE')
        self.assertFalse(r['strategy_a']['trade_ready'])
        self.assertEqual(r['execution'], 'DISABLED')
    def test_stale_report_hides_candidates(self):
        r=build_status(self.report, self.now+dt.timedelta(hours=1))
        self.assertFalse(r['fresh_at_check'])
        self.assertEqual(r['strategy_a']['assets']['BTCUSDT']['state'], 'NO_VERIFIED_DATA')
        self.assertEqual(r['strategy_b']['proposals_observed'], 0)
    def test_untrusted_execution_never_creates_signal(self):
        self.report['execution']='ENABLED'
        self.assertFalse(build_status(self.report, self.now)['fresh_at_check'])
    def test_dashboard_static_no_scripts(self):
        h=to_html(build_status(self.report, self.now))
        self.assertIn('Автоматическое исполнение выключено',h)
        self.assertNotIn('<script',h)

if __name__=='__main__': unittest.main()
