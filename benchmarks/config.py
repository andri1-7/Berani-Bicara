"""Literal, non-executing configuration."""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import os
import re
from pathlib import Path


def limit(value, maximum):
    try:
        if not isinstance(value, str):
            raise ValueError
        amount = Decimal(value)
        _, digits, exponent = amount.as_tuple()
        fractional = isinstance(exponent, int) and exponent < -6 and any(digits[max(0, len(digits) + exponent + 6):])
        if not amount.is_finite() or amount <= 0 or amount > Decimal(maximum) or fractional:
            raise ValueError
        return str(amount)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Invalid budget setting') from None


@dataclass(frozen=True)
class Config:
    paid_tests_enabled: bool = False
    api_key: str = field(default='', repr=False)

    @property
    def key_present(self):
        return bool(self.api_key)

    total_limit: str = '5.00'
    stop_line: str = '4.50'

    def __post_init__(self):
        if type(self.paid_tests_enabled) is not bool or type(self.api_key) is not str:
            raise ValueError('Invalid configuration types')
        total = limit(self.total_limit, '5')
        stop = limit(self.stop_line, '4.50')
        if Decimal(stop) > Decimal(total):
            raise ValueError('Invalid budget setting')


KEYS = {'OPENROUTER_API_KEY', 'PAID_TESTS_ENABLED', 'EVALUATION_BUDGET_USD', 'EVALUATION_STOP_LINE_USD'}


def read_literals(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Z][A-Z0-9_]*)=(.*)', line)
        if not match:
            raise ValueError('Invalid configuration syntax')
        key, value = match.groups()
        if key not in KEYS or key in result:
            raise ValueError('Unknown or duplicate configuration key')
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0] or value[0] in value[1:-1]:
                raise ValueError('Invalid quoted literal')
            value = value[1:-1]
        elif any(char.isspace() or char in "\"'#" for char in value):
            raise ValueError('Invalid unquoted literal')
        result[key] = value
    return result


def load_config(*, environ=None, path=None):
    env = read_literals(path) if path is not None else {}
    overrides = os.environ if environ is None else environ
    env.update({key: value for key, value in overrides.items() if key in KEYS})
    enabled = env.get('PAID_TESTS_ENABLED', 'false')
    if enabled not in ('true', 'false'):
        raise ValueError('Invalid paid test flag')
    total = limit(env.get('EVALUATION_BUDGET_USD', '5.00'), '5')
    stop = limit(env.get('EVALUATION_STOP_LINE_USD', str(min(Decimal(total), Decimal('4.50')))), '4.50')
    if Decimal(stop) > Decimal(total):
        raise ValueError('Invalid budget setting')
    return Config(paid_tests_enabled=enabled == 'true', total_limit=total, stop_line=stop, api_key=env.get('OPENROUTER_API_KEY', ''))
