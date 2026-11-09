"""Pure, fail-closed Walt perps risk scenarios. Never connects to Wallet and never trades.

All contract inputs are supplied by a trusted caller at evaluation time. The
price_slippage field is a stress assumption, NOT a guaranteed stop fill bound.
No output from this module grants trade permission.
"""
from decimal import Decimal, ROUND_FLOOR


class RiskInputError(ValueError):
    pass


def d(value):
    try:
        x = Decimal(str(value))
    except Exception as exc:
        raise RiskInputError('Invalid numeric input') from exc
    if not x.is_finite():
        raise RiskInputError('Nonfinite numeric input')
    return x


def _floor_step(x, step):
    return (x / step).to_integral_value(rounding=ROUND_FLOOR) * step


def scenario(contract, *, side, reference_price, stop_price, target_price,
             margin_usdc, holding_hours=1):
    """Illustrative two-sided adverse slippage/fee scenario, never an order."""
    if side not in ('long', 'short'):
        raise RiskInputError('side must be long or short')
    if contract.get('quote_asset') != 'USDC' or not contract.get('is_active'):
        raise RiskInputError('Inactive or non-USDC contract')
    price, stop, target, margin = map(d, (reference_price, stop_price, target_price, margin_usdc))
    slippage, taker, min_base, step, min_margin = map(d, (
        contract['price_slippage'], contract['taker_fee_pct'],
        contract['min_size_base'], contract['step_size'], contract['min_size_quote']))
    funding = abs(d(contract.get('funding_rate_hourly', '0')))
    hours = d(holding_hours)
    if min(price, stop, target, margin, min_base, step, min_margin) <= 0 or hours < 0:
        raise RiskInputError('Expected positive price, amount, size and step')
    if not (0 <= slippage < 1 and 0 <= taker < 1):
        raise RiskInputError('Invalid cost assumptions')
    if margin < min_margin or margin > d(contract['max_size_quote']):
        raise RiskInputError('Margin outside contract limits')
    if side == 'long' and not (stop < price < target):
        raise RiskInputError('Long stop/target invalid')
    if side == 'short' and not (target < price < stop):
        raise RiskInputError('Short stop/target invalid')

    # 1x, taker fee deducted from posted collateral; adverse entry price.
    notional = margin / (Decimal(1) + taker)
    adverse_entry = price * (Decimal(1) + slippage if side == 'long' else Decimal(1) - slippage)
    qty = _floor_step(notional / adverse_entry, step)
    if qty < min_base:
        raise RiskInputError('Minimum base size not met with 1x margin')
    stop_fill = stop * (Decimal(1) - slippage if side == 'long' else Decimal(1) + slippage)
    target_fill = target * (Decimal(1) - slippage if side == 'long' else Decimal(1) + slippage)
    if side == 'long':
        gross_loss = (adverse_entry - stop_fill) * qty
        gross_profit = (target_fill - adverse_entry) * qty
    else:
        gross_loss = (stop_fill - adverse_entry) * qty
        gross_profit = (adverse_entry - target_fill) * qty
    fee_loss = (adverse_entry + stop_fill) * qty * taker
    fee_profit = (adverse_entry + target_fill) * qty * taker
    funding_reserve = price * qty * funding * hours
    worst_case_loss = gross_loss + fee_loss + funding_reserve
    net_profit = gross_profit - fee_profit - funding_reserve
    rr = net_profit / worst_case_loss if worst_case_loss > 0 else Decimal(0)
    return {
        'base_quantity': str(qty), 'margin_usdc': str(margin),
        'stress_slippage_each_side': str(slippage),
        'stress_loss_usdc': str(worst_case_loss),
        'stress_net_profit_usdc': str(net_profit),
        'stress_net_rr': str(rr),
        'trade_ready': False,
        'notice': 'Scenario only. No assured fill bounds, verified USDC, liquidity, or executable stop.'
    }


def minimum_cost_floor(contract, reference_price):
    """Min-size round trip stress cost floor, without stop movement and funding."""
    price, size = d(reference_price), d(contract['min_size_base'])
    fee, slip = d(contract['taker_fee_pct']), d(contract['price_slippage'])
    if price <= 0 or size <= 0 or fee < 0 or slip < 0:
        raise RiskInputError('Invalid floor parameters')
    notional = price * size
    return {
        'min_notional_usdc': str(notional),
        'round_trip_slippage_and_taker_fee_usdc': str(notional * (2 * slip + 2 * fee)),
        'trade_ready': False,
        'notice': 'Stress floor; NOT a guarantee, excludes stop movement and funding.'
    }
