import argparse
import json


def main():
    parser = argparse.ArgumentParser(description='Offline evaluation; paid calls are opt-in and not implemented.')
    commands = parser.add_subparsers(dest='command', required=True)
    status = commands.add_parser('status', help='Read offline configuration and budget status')
    status.add_argument('--ledger', default='private/ledger.sqlite3')
    args = parser.parse_args()
    print(json.dumps({'paid_tests_enabled': False}))


if __name__ == '__main__':
    main()
