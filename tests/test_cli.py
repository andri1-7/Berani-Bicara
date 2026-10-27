import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class TestCLI(unittest.TestCase):
    def test_status_is_offline_and_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, '-m', 'benchmarks', 'status',
                                     '--ledger', tmp+'/ledger.sqlite3'],
                                    capture_output=True, text=True, env={**os.environ, 'PAID_TESTS_ENABLED': 'false'})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIs(json.loads(result.stdout)['paid_tests_enabled'], False)

    def test_status_shows_unknown_and_remaining(self):
        from benchmarks.budget import BudgetLedger, DEFAULT_STAGE_LIMITS
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'private'/'ledger.sqlite3'
            ledger = BudgetLedger(path, DEFAULT_STAGE_LIMITS)
            request = ledger.reserve('smoke', '0.10')
            ledger.settle(request, '0.02')
            ledger.mark_unknown(ledger.reserve('smoke', '0.10'))
            config = Path(tmp)/'fixture.env'
            config.write_text('OPENROUTER_API_KEY="fixture-secret-never-print"\nPAID_TESTS_ENABLED=false\n')
            result = subprocess.run([sys.executable, '-m', 'benchmarks', 'status', '--ledger', str(path), '--config', str(config)],
                                    capture_output=True, text=True, env={key: value for key, value in os.environ.items() if key not in ('OPENROUTER_API_KEY', 'PAID_TESTS_ENABLED', 'EVALUATION_BUDGET_USD', 'EVALUATION_STOP_LINE_USD')})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('fixture-secret-never-print', result.stdout+result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data['budget']['confirmed_micro'], 20000)
            self.assertEqual(data['budget']['reserved_micro'], 100000)
            self.assertEqual(data['budget']['unresolved'], 1)
            self.assertEqual(data['budget']['available_by_stage_micro']['smoke'], 130000)
            self.assertEqual(data['budget']['remaining_micro'], 4380000)
            self.assertFalse(data['budget']['dispatch_allowed'])
