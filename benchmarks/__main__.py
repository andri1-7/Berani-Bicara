"""Offline-only commands. Never implicitly load the private .env file."""
import argparse
import json
import sqlite3
from .budget import BudgetLedger, DEFAULT_STAGE_LIMITS
from .config import load_config


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, 'Invalid command arguments; use --help.\n')


def main():
    parser = PrivateArgumentParser(description='Offline evaluation; paid calls are opt-in and not implemented.')
    commands = parser.add_subparsers(dest='command', required=True)
    for name, help_text in [('status', 'Read-only offline configuration and budget status'),
                            ('init-ledger', 'Explicitly initialize a NEW private ledger; refuses existing paths')]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument('--ledger', default='private/ledger.sqlite3')
        command.add_argument('--config', help='Explicit literal configuration path; no implicit .env read')
    args = parser.parse_args()
    try:
        config = load_config(path=args.config)
        try:
            opener = BudgetLedger.initialize if args.command == 'init-ledger' else BudgetLedger
            ledger = opener(args.ledger, DEFAULT_STAGE_LIMITS, config.total_limit, config.stop_line)
            budget = ledger.summary()
        except FileNotFoundError:
            if args.command != 'status':
                raise
            budget = {'initialized': False}
        print(json.dumps({'paid_tests_enabled': config.paid_tests_enabled,
                          'api_key_present': config.key_present,
                          'paid_dispatch_implemented': False,
                          'budget': budget}, sort_keys=True))
        return 0
    except (ValueError, OSError, sqlite3.Error):
        print(json.dumps({'error': 'Offline configuration or ledger unavailable'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
