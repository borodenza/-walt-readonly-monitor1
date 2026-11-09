"""Build a safe offline cockpit from research data. No Walt API calls or orders."""
import datetime as dt
import html
import json
from pathlib import Path

UTC = dt.timezone.utc


def build_status(report, now=None):
    now = now or dt.datetime.now(UTC)
    try:
        generated = dt.datetime.fromisoformat(report['generated_utc'].replace('Z', '+00:00'))
        fresh = generated.tzinfo is not None and 0 <= (now - generated).total_seconds() <= 900
    except (KeyError, TypeError, ValueError):
        fresh = False
    valid_source = report.get('mode') == 'READ_ONLY_RESEARCH' and report.get('execution') == 'DISABLED'
    fresh = fresh and valid_source
    assets = {}
    for symbol in ('BTCUSDT', 'ETHUSDT'):
        asset = report.get('assets', {}).get(symbol, {})
        message = asset.get('strategy_a', 'NO_SIGNAL')
        candidate = fresh and 'Условный технический кандидат' in message and bool(asset.get('timeframes'))
        assets[symbol] = {
            'state': 'RESEARCH_CANDIDATE' if candidate else ('MONITORING' if fresh and asset.get('timeframes') else 'NO_VERIFIED_DATA'),
            'analysis': message if fresh else 'Данные недоступны или устарели',
            'trade_ready': False,
            'reasons': [
                'Нет подтверждённого доступного обеспечения USDC и валюты риска',
                'Нет исполнимого расчёта SL/TP, издержек и чистого RR по Walt',
                'Нет автономного исполнителя, разрешённого правилами Walt',
            ],
        }
    mira = report.get('mira', {})
    proposals = mira.get('proposals', []) if fresh and mira.get('ok') is True else []
    return {
        'mode': 'READ_ONLY_RESEARCH', 'execution': 'DISABLED',
        'report_time': report.get('generated_utc'), 'fresh_at_check': fresh,
        'strategy_a': {'capital_limit_usdt': '9', 'risk_limit_usdt': '0.09',
                       'max_trades_daily': 2, 'min_rr_net': 2, 'leverage': 1,
                       'assets': assets, 'trade_ready': False},
        'strategy_b': {'label': 'Mira Recovery', 'capital_limit_usdt': '9',
                       'risk_limit_usdt': '0.18', 'max_daily_proposals': 3,
                       'proposals_observed': len(proposals),
                       'execution': 'REQUIRES_PREVIEW_AND_CONFIRMATION',
                       'trade_ready': False},
        'global_blockers': ['Недоступен автономный путь исполнения Walt',
                            'Обеспечение USDC не подтверждено',
                            'Проверка ограничений риска/ликвидности не завершена'],
        'note': 'Никакой торговли, симулированного PnL или разрешения на сделку не создаётся.',
    }


def to_html(status):
    e = html.escape
    assets = status['strategy_a']['assets']
    sections = ''.join(
        '<article><div class="top"><strong>'+e(sym)+'</strong><span>'+e(item['state'])+'</span></div>'
        '<p>'+e(item['analysis'])+'</p><p class="warn">Сделка запрещена: нужен допуск Walt и подтверждение покрытия риска.</p></article>'
        for sym, item in assets.items())
    source = e(str(status['report_time'] or 'неизвестно'))
    fresh = 'В пределах 15 мин при формировании отчёта' if status['fresh_at_check'] else 'Нет проверенного свежего отчёта'
    return """<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Walt · Центр стратегий</title><style>
*{box-sizing:border-box}body{background:#f1f3ef;color:#18322a;font:15px/1.55 system-ui,sans-serif;margin:0}
main{max-width:1000px;margin:0 auto;padding:32px 24px 55px}h1{font:clamp(36px,6vw,68px)/1.05 Georgia,serif;letter-spacing:-.05em;margin:28px 0}
small{color:#677a72}.label{letter-spacing:.16em;text-transform:uppercase;color:#497060;font-size:11px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.panel{background:white;border:1px solid #cbd7ce;border-radius:18px;padding:22px}
.pill{display:inline-block;border-radius:40px;padding:5px 12px;background:#f9e9ce;color:#704e12;font-size:12px}
strong{font-size:20px}article{padding:18px 0;border-top:1px solid #e0e7df}.top{display:flex;justify-content:space-between;align-items:center;gap:12px}
.top span{font-size:11px;letter-spacing:.04em;color:#718578}.warn{color:#876038}ul{padding-left:20px}footer{margin-top:24px;font-size:13px;color:#637c72}
@media(max-width:680px){.grid{grid-template-columns:1fr}main{padding:22px 16px}}</style><main>
<div class="label">Walt / Risk Control · Только чтение</div><h1>Центр стратегий</h1>
<p><span class="pill">Автоматическое исполнение выключено</span></p>
<p><small>Отчёт: """+source+""" · """+fresh+"""</small></p>
<div class="grid"><section class="panel"><div class="label">A / Trend Following</div><h2>Поиск тренда</h2>
<p>BTC + ETH · 5m/15m/1h · бюджет 9 USDT · риск ≤0,09 USDT · 1× · чистый RR ≥2</p>
"""+sections+"""</section>
<section class="panel"><div class="label">B / Mira Recovery</div><h2>Подтверждение вручную</h2>
<p>Бюджет 9 USDT · риск ≤0,18 USDT · максимум 3 исследовательских предложения в день · плечо 1×.</p>
<p>Сигналы, обнаруженные в этом исследовательском отчёте: <strong>"""+str(status['strategy_b']['proposals_observed'])+"""</strong></p>
<p>Карточки и кнопки подтверждения находятся в соседнем файле <strong>mira-recovery.html</strong>, внутри того же артефакта.</p>
<p class="warn">Нажатие «Подтвердить» не отправляет ордер. Необходим отдельный предпросмотр Walt.</p>
<h3>Проверки перед любой сделкой</h3><ul>
<li>USDC и допустимый размер контракта</li><li>Проверка позиции и ожидающих ордеров</li>
<li>Цена Walt, OI, объём, глубина и спред</li><li>Стоп/цель, проскальзывание, комиссии, funding, RR</li>
<li>Суточные лимиты и отдельное подтверждение</li></ul></section></div>
<footer>Панель — статический снимок GitHub Actions, а не живой торговый терминал. Обновляйте файл из последнего запуска.</footer></main></html>"""


def main():
    p = Path('walt-report.json')
    try:
        report = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        report = {}
    status = build_status(report)
    Path('walt-system.json').write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
    Path('walt-system.html').write_text(to_html(status), encoding='utf-8')
    print('Walt system status: market report fresh=', status['fresh_at_check'],
          'live execution=', status['execution'])


if __name__ == '__main__':
    main()
