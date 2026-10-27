"""Exact decimal-string USD to integer microUSD, always rounded upward."""
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
import re


MAX_MICRO = 2**63 - 1


def reserve_micro(value):
    if not isinstance(value, str) or not re.fullmatch(r'[+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', value) or len(value) > 200:
        raise ValueError('Invalid USD amount')
    try:
        with localcontext() as ctx:
            ctx.prec = 250
            amount = Decimal(value)
            if amount and abs(amount.adjusted()) > 200:
                raise ValueError
            micro = (amount * 1000000).to_integral_value(rounding=ROUND_CEILING)
            if not amount.is_finite() or amount < 0 or micro > MAX_MICRO:
                raise ValueError
            return int(micro)
    except (InvalidOperation, OverflowError, ValueError):
        raise ValueError('Invalid USD amount') from None


def actual_micro(value):
    return reserve_micro(value)
