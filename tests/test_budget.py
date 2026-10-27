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
