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
