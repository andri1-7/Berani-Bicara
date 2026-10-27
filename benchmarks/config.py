"""Literal, non-executing configuration."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import os


def limit(value, maximum):
    try:
        amount = Decimal(value)
        if not amount.is_finite() or amount <= 0 or amount > Decimal(maximum) or amount * 1000000 != (amount * 1000000).to_integral_value():
            raise ValueError
        return str(amount)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Invalid budget setting') from None


@dataclass(frozen=True)
class Config:
    paid_tests_enabled: bool = False
    total_limit: str = '5.00'
    stop_line: str = '4.50'


def load_config(*, environ=None, path=None):
    env = os.environ if environ is None else environ
    total = limit(env.get('EVALUATION_BUDGET_USD', '5.00'), '5')
    stop = limit(env.get('EVALUATION_STOP_LINE_USD', min(Decimal(total), Decimal('4.50'))), '4.50')
    if Decimal(stop) > Decimal(total):
        raise ValueError('Invalid budget setting')
    return Config(total_limit=total, stop_line=stop)
