"""Single-strategy Mira Recovery dashboard. Research only; never authorizes orders."""
import datetime as dt
import html
import json
from pathlib import Path

UTC = dt.timezone.utc
WATCH = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT",
         "LINKUSDT", "AVAXUSDT", "ADAUSDT", "XRPUSDT")


def build_status(report, now=None):
    now = now or dt.datetime.now(UTC)
    try:
        generated = dt.datetime.fromisoformat(report['generated_utc'].replace('Z', '+00:00'))
        fresh = generated.tzinfo is not None and 0 <= (now - generated).total_seconds() <= 900
    except (KeyError, TypeError, ValueError, AttributeError):
        fresh = False
    valid = (
        report.get('mode') == 'READ_ONLY_RESEARCH'
        and report.get('strategy') == 'MIRA_RECOVERY_ONLY'
        and report.get('execution') == 'DISABLED'
        and report.get('source') == 'Bybit V5 linear futures public klines'
    )
    fresh = fresh and valid
    mira = report.get('mira') or {}
    if not isinstance(mira, dict):
        mira = {}
    all_obs = mira.get('observations') or {}
    data_ok = fresh and mira.get('ok') is True and set(all_obs) == set(WATCH)
    now_ms = int(now.timestamp() * 1000)
    raw = mira.get('proposals', [])
    candidates = []
    if data_ok and isinstance(raw, list):
        for x in raw:
            if (isinstance(x, dict) and x.get('symbol') in WATCH
                and type(x.get('closed_ms')) is int and type(x.get('expires_ms')) is int
                and x['closed_ms'] <= now_ms < x['expires_ms']):
                candidates.append(x)
    return {
        'strategy': 'MIRA_RECOVERY_ONLY',
        'retired_strategies': ['TREND_FOLLOWING', 'MOMENTUM_BREAKOUT'],
        'operating_mode': 'RESEARCH_ONLY',
        'execution': 'DISABLED',
        'auto_trade_requested': True,
        'auto_trade_enabled': False,
        'trade_ready': False,
        'report_time': report.get('generated_utc'),
        'fresh_at_check': fresh,
        'market_data_ok': bool(data_ok),
        'limits': {'capital_usdt': '9', 'risk_usdt': '0.18',
                   'max_daily_signals': 3, 'leverage': 1,
                   'max_open_positions': 1},
        'research_candidates': candidates[:3],
        'market_observations': all_obs if data_ok else {},
        'market_errors': mira.get('errors', {}) if not data_ok and isinstance(mira.get('errors'), dict) else {},
        'blockers': [
            'Текущее подключение Walt требует индивидуальный preview/confirm для каждой сделки',
            'Нет подтверждённого права автономного исполнения по официальному API/subaccount',
            'GitHub не получает доступный баланс и фьючерсные позиции Walt',
            'Не проверены текущие Walt quote, контракт, глубина/спред и обеспечение',
            'Не проверен чистый риск/стоп/тейк и суточный лимит по каждой заявке',
        ],
        'notice': 'Mira использует Bybit Futures только для исследования; это не торговый терминал.'
    }


def to_html(status):
    e = html.escape
    time = e(str(status.get('report_time') or '—'))
    good = status['market_data_ok']
    cards = []
    for symbol in WATCH:
        row = status['market_observations'].get(symbol, {})
        if not isinstance(row, dict):
            row = {}
        price = row.get('futures_close')
        change = row.get('change24_pct')
        cards.append(
            '<div class="market"><strong>' + e(symbol.replace('USDT', '')) +
            '</strong><div>' + e(str(round(price, 5)) if isinstance(price,(int,float)) else '—') +
            '</div><small>' + e(f'{change:+.2f}%' if isinstance(change,(int,float)) else '—') +
            ' · 24h</small></div>')
    entries = []
    for x in status['research_candidates']:
        symbol = e(x['symbol'])
        entries.append('<div class="candidate"><strong>' + symbol + '</strong>'
                       '<div>24h: ' + e(str(round(x.get('change24_pct',0),2))) +
                       '% · 15m close ' + e(str(x.get('futures_close','—'))) +
                       '</div><small>Технический кандидат · торговля заблокирована</small></div>')
    if not entries:
        entries.append('<p class="muted">Нет действующих технических кандидатов или данные не прошли проверку.</p>')
    reasons=''.join('<li>'+e(x)+'</li>' for x in status['blockers'])
    banner = 'Рыночные данные получены' if good else 'Нет проверенного полного набора свежих данных'
    errors = ''.join('<li>' + e(str(k)) + ': ' + e(str(v)) + '</li>' for k,v in status['market_errors'].items())
    error_panel = '<div class="panel"><h2>Ошибки источника данных</h2><ul>' + errors + '</ul></div>' if errors else ''
    return f"""<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none';style-src 'unsafe-inline';base-uri 'none';form-action 'none'">
<title>Mira Recovery | Walt Futures</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0d151a;color:#eaf3f0;font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1100px;margin:auto;padding:32px 28px 60px}}h1{{font:clamp(42px,7vw,76px)/1 Georgia,serif;letter-spacing:-.04em;margin:12px 0}}
.muted,small{{color:#a1b5ad}}.over{{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#9de7c0}}
.pill{{display:inline-block;border:1px solid #9e8254;color:#f2c87e;padding:6px 12px;border-radius:40px;font-size:12px}}
.panel{{background:#16242b;border:1px solid #32424a;border-radius:18px;padding:22px;margin:18px 0}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.stat{{padding:17px;background:#1c3238;border-radius:12px}}
.stat strong{{display:block;font-size:23px}}h2{{margin:0 0 12px;font:26px Georgia,serif}}
.markets{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.market{{background:#1c3238;padding:14px;border-radius:10px}}.market strong{{color:#ade6ca}}.market div{{font-size:18px}}
.candidate{{padding:15px 0;border-top:1px solid #334750}}.candidate strong{{display:block;font-size:20px}}
li{{padding:4px 0}}footer{{margin-top:25px;color:#94a7a0;font-size:12px}}
@media(max-width:700px){{.stats,.markets{{grid-template-columns:repeat(2,1fr)}}main{{padding:22px 16px}}}}
</style><main><div class="over">WALT / FUTURES RESEARCH</div><h1>Mira Recovery</h1>
<p><span class="pill">Автоматическая торговля НЕ включена</span></p>
<p class="muted">Одна стратегия · поиск восстановления после снижения от 5% за 24 часа · Bybit USDT Linear Futures</p>
<div class="stats">
<div class="stat"><small>Бюджет</small><strong>9 USDT</strong></div>
<div class="stat"><small>Риск на сделку</small><strong>0,18 USDT</strong></div>
<div class="stat"><small>Плечо</small><strong>1×</strong></div>
<div class="stat"><small>Позиции</small><strong>0–1</strong></div></div>
<section class="panel"><h2>Текущий отчёт</h2><p>{e(banner)}</p><small>Время анализа: {time} UTC</small>
<h2 style="margin-top:24px">Кандидаты</h2>{''.join(entries)}</section>
<section class="panel"><h2>Рынки фьючерсов</h2><div class="markets">{''.join(cards)}</div></section>
<section class="panel"><h2>Почему реальные сделки заблокированы</h2><ul>{reasons}</ul></section>
<footer>Статический снимок GitHub Actions. Не является текущей котировкой Walt. Ордеров не создаёт. Trend Following и Momentum Breakout отключены.</footer>
{error_panel}</main></html>"""


def main():
    try:
        report = json.loads(Path('walt-report.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        report = {}
    status = build_status(report)
    Path('walt-system.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    Path('walt-system.html').write_text(to_html(status), encoding='utf-8')
    print('Mira only: source fresh =', status['fresh_at_check'],
          'market data complete =', status['market_data_ok'],
          'autonomous Walt execution =', status['execution'])

if __name__ == '__main__':
    main()
