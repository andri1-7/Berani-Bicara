"""Offline-only commands. Never implicitly load the private .env file."""
import argparse
import json
import sqlite3
from .budget import BudgetLedger, DEFAULT_STAGE_LIMITS
from .config import load_config


def main():
    parser = argparse.ArgumentParser(description='Offline evaluation; paid calls are opt-in and not implemented.')
    commands = parser.add_subparsers(dest='command', required=True)
    status = commands.add_parser('status', help='Read offline configuration and budget status')
    status.add_argument('--ledger', default='private/ledger.sqlite3')
    status.add_argument('--config', help='Explicit literal configuration path; no implicit .env read')
    args = parser.parse_args()
    try:
        config = load_config(path=args.config)
        ledger = BudgetLedger(args.ledger, DEFAULT_STAGE_LIMITS, config.total_limit, config.stop_line)
        print(json.dumps({'paid_tests_enabled': config.paid_tests_enabled,
                          'api_key_present': config.key_present,
                          'paid_dispatch_implemented': False,
                          'budget': ledger.summary()}, sort_keys=True))
        return 0
    except (ValueError, OSError, sqlite3.Error):
        print(json.dumps({'error': 'Offline configuration or ledger unavailable'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
