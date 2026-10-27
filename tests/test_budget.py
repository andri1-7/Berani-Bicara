from pathlib import Path
import tempfile
import unittest
from benchmarks.budget import BudgetLedger, BudgetExceeded

LIMITS = {'smoke': '0.25', 'grammar': '0.75', 'transcription': '0.75',
          'tts': '0.75', 'conversation': '1.00'}

class TestBudget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'private'/'ledger.sqlite3'
        self.ledger = BudgetLedger(self.path, LIMITS)

    def test_reservation_blocks_overspend(self):
        self.ledger.reserve('smoke', '0.20')
        with self.assertRaises(BudgetExceeded):
            self.ledger.reserve('smoke', '0.06')

    def test_total_reservation_stops_at_four_fifty(self):
        path = Path(self.tmp.name)/'total'/'ledger.sqlite3'
        ledger = BudgetLedger(path, {'evaluation': '5.00'})
        ledger.reserve('evaluation', '4.50')
        with self.assertRaises(BudgetExceeded):
            ledger.reserve('evaluation', '0.000001')

    def test_invalid_limits_and_locked_contingency(self):
        for total, stop in [('5.01', '4.50'), ('5', '4.51'), ('0', '0'), ('1', '2')]:
            with self.subTest(total=total, stop=stop), self.assertRaises(ValueError):
                BudgetLedger(Path(self.tmp.name)/'invalid'/'ledger.sqlite3', LIMITS, total, stop)
        with self.assertRaises(BudgetExceeded):
            self.ledger.reserve('contingency', '0.01')
        with self.assertRaises(ValueError):
            self.ledger.reserve('smoke', '0')

    def test_reopen_preserves_outstanding_reservation(self):
        self.ledger.reserve('smoke', '0.20')
        reopened = BudgetLedger(self.path, LIMITS)
        with self.assertRaises(BudgetExceeded):
            reopened.reserve('smoke', '0.06')
        for limits, total, stop in [({**LIMITS, 'smoke': '0.30'}, '5', '4.50'),
                                    (LIMITS, '4.90', '4.50'), (LIMITS, '5', '4.40')]:
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                BudgetLedger(self.path, limits, total, stop)

    def test_two_processes_cannot_both_reserve(self):
        import subprocess
        import sys
        script = """import sys
from benchmarks.budget import BudgetLedger, BudgetExceeded, DEFAULT_STAGE_LIMITS
ledger = BudgetLedger(sys.argv[1], DEFAULT_STAGE_LIMITS)
sys.stdin.readline()
try:
    ledger.reserve('smoke', '0.01')
    print('reserved')
except BudgetExceeded:
    print('blocked')
"""
        processes = [subprocess.Popen([sys.executable, '-c', script, str(self.path)], stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        for process in processes:
            process.stdin.write('go\n')
            process.stdin.flush()
        outputs = [process.communicate(timeout=20) for process in processes]
        self.assertEqual(sorted(out.strip() for out, err in outputs), ['blocked', 'reserved'], outputs)
        self.assertTrue(all(process.returncode == 0 for process in processes), outputs)

    def test_unknown_cost_blocks_new_requests(self):
        request = self.ledger.reserve('smoke', '0.10')
        getattr(self.ledger, 'mark_unknown', lambda request: None)(request)
        import sqlite3
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT status FROM requests WHERE id=?', (request,)).fetchone()[0], 'unknown')
        with self.assertRaises(BudgetExceeded):
            BudgetLedger(self.path, LIMITS).reserve('grammar', '0.01')

    def test_timeout_does_not_release_reservation(self):
        request = self.ledger.reserve('smoke', '0.10')
        try:
            raise TimeoutError('offline timeout fixture')
        except TimeoutError:
            self.ledger.mark_unknown(request)
        summary = getattr(BudgetLedger(self.path, LIMITS), 'summary', lambda: {})()
        self.assertEqual(summary.get('reserved_micro'), 100000)
        self.assertEqual(summary.get('unresolved'), 1)
        with self.assertRaises(BudgetExceeded):
            self.ledger.reserve('grammar', '0.01')

    def test_duplicate_settlement_is_rejected(self):
        request = self.ledger.reserve('smoke', '0.20')
        getattr(self.ledger, 'settle', lambda *args: None)(request, '0.05')
        self.assertEqual(self.ledger.summary()['confirmed_micro'], 50000)
        self.assertEqual(self.ledger.summary()['reserved_micro'], 0)
        with self.assertRaises(ValueError):
            self.ledger.settle(request, '0.01')
        with self.assertRaises(ValueError):
            self.ledger.settle('nonexistent', '0')
        self.ledger.reserve('smoke', '0.20')
