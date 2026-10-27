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
        self.ledger = BudgetLedger.initialize(self.path, LIMITS)

    def test_initial_policy_rejects_unapproved_caps_and_names(self):
        for limits in ({'smoke': '4.50'}, {'evaluation': '5.00'}, {'first': '0.01'}):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                BudgetLedger(Path(self.tmp.name)/(next(iter(limits))+'.sqlite3'), limits)
            with self.subTest(initialization=limits), self.assertRaises(ValueError):
                BudgetLedger.initialize(Path(self.tmp.name)/'unauthorized.sqlite3', limits)
        self.assertFalse((Path(self.tmp.name)/'unauthorized.sqlite3').exists())

    def test_reservation_blocks_overspend(self):
        self.ledger.reserve('smoke', '0.20')
        with self.assertRaises(BudgetExceeded):
            self.ledger.reserve('smoke', '0.06')

    def test_total_reservation_stops_at_four_fifty(self):
        path = Path(self.tmp.name)/'total'/'ledger.sqlite3'
        ledger = BudgetLedger.initialize(path, LIMITS, stop_line='0.20')
        request = ledger.reserve('smoke', '0.20')
        ledger.settle(request, '0.20')
        with self.assertRaises(BudgetExceeded):
            ledger.reserve('grammar', '0.000001')

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

    def test_actual_cost_above_reservation_halts_account(self):
        request = self.ledger.reserve('smoke', '0.10')
        self.ledger.settle(request, '5.01')
        reopened = BudgetLedger(self.path, LIMITS)
        self.assertEqual(reopened.summary()['confirmed_micro'], 5010000)
        self.assertTrue(reopened.summary().get('halted', False))
        with self.assertRaises(BudgetExceeded):
            reopened.reserve('grammar', '0.01')

    def test_small_overrun_also_permanently_halts(self):
        request = self.ledger.reserve('smoke', '0.10')
        self.ledger.settle(request, '0.100001')
        with self.assertRaises(BudgetExceeded):
            BudgetLedger(self.path, LIMITS).reserve('grammar', '0.01')

    def test_symlink_ledger_is_rejected_without_touching_target(self):
        target = Path(self.tmp.name)/'untouched'
        target.write_text('fixture')
        target.chmod(0o644)
        link = self.path.parent/'link.sqlite3'
        link.symlink_to(target)
        with self.assertRaises((ValueError, OSError)):
            BudgetLedger(link, LIMITS)
        self.assertEqual(target.stat().st_mode & 0o777, 0o644)

    def test_fractional_micro_limits_are_rejected(self):
        for value in ('0.2500001', '0.2000000000000000000000000001'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                BudgetLedger.initialize(Path(self.tmp.name)/'fractional'/'ledger.sqlite3', {'smoke': value})
        for value in ('0.2500001', '0.2000000000000000000000000001'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                BudgetLedger(self.path, {'smoke': value})

    def test_stage_cap_after_settlement_not_just_inflight_guard(self):
        request = self.ledger.reserve('smoke', '0.20')
        self.ledger.settle(request, '0.20')
        with self.assertRaises(BudgetExceeded):
            self.ledger.reserve('smoke', '0.06')
        self.assertEqual(self.ledger.summary()['confirmed_micro'], 200000)
        self.ledger.reserve('smoke', '0.05')

    def test_total_stop_line_after_settlements_across_stages(self):
        path = Path(self.tmp.name)/'sequential'/'ledger.sqlite3'
        ledger = BudgetLedger.initialize(path, LIMITS, stop_line='1.00')
        request = ledger.reserve('smoke', '0.25')
        ledger.settle(request, '0.25')
        request = ledger.reserve('grammar', '0.75')
        ledger.settle(request, '0.75')
        with self.assertRaises(BudgetExceeded):
            ledger.reserve('transcription', '0.000001')
        self.assertEqual(ledger.summary()['remaining_micro'], 0)

    def test_reconcile_unknown_releases_only_unused_reservation(self):
        request = self.ledger.reserve('smoke', '0.20')
        self.ledger.mark_unknown(request)
        self.ledger.settle(request, '0.01')
        self.assertEqual(self.ledger.summary()['unresolved'], 0)
        self.assertEqual(self.ledger.summary()['reserved_micro'], 0)
        self.assertTrue(self.ledger.summary()['dispatch_allowed'])
        with self.assertRaises(ValueError):
            self.ledger.mark_unknown(request)
        self.ledger.reserve('smoke', '0.24')

    def test_private_permissions(self):
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)

    def test_invalid_cost_does_not_release_reservation(self):
        request = self.ledger.reserve('smoke', '0.10')
        with self.assertRaises(ValueError):
            self.ledger.settle(request, 'NaN')
        self.assertEqual(self.ledger.summary()['reserved_micro'], 100000)
        with self.assertRaises(BudgetExceeded):
            self.ledger.reserve('smoke', '0.01')


    def test_open_missing_does_not_create_or_chmod(self):
        parent = Path(self.tmp.name)/'unrelated'
        parent.mkdir(mode=0o755)
        path = parent/'missing.sqlite3'
        with self.assertRaises((ValueError, OSError)):
            BudgetLedger(path, LIMITS)
        self.assertFalse(path.exists())
        self.assertEqual(parent.stat().st_mode & 0o777, 0o755)

    def test_open_missing_schema_or_policy_fails_without_repair(self):
        import sqlite3
        for remove in ("DELETE FROM metadata WHERE key='policy'", 'DROP TABLE requests'):
            path = Path(self.tmp.name)/('broken'+str(len(remove)))/'ledger.sqlite3'
            BudgetLedger.initialize(path, LIMITS)
            with sqlite3.connect(path) as db:
                db.execute(remove)
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                BudgetLedger(path, LIMITS)
            self.assertEqual(path.read_bytes(), before)

    def test_open_empty_or_foreign_database_fails_without_changes(self):
        import sqlite3
        for foreign in (False, True):
            path = Path(self.tmp.name)/('foreign' if foreign else 'empty')
            with sqlite3.connect(path) as db:
                if foreign:
                    db.execute('CREATE TABLE unrelated (value TEXT)')
            before = path.read_bytes()
            with self.assertRaises((ValueError, sqlite3.Error)):
                BudgetLedger(path, LIMITS)
            self.assertEqual(path.read_bytes(), before)

    def test_explicit_init_refuses_existing_and_symlink_ancestors(self):
        self.assertTrue(hasattr(BudgetLedger, 'initialize'), 'Explicit initialization is required')
        with self.assertRaises((ValueError, OSError)):
            BudgetLedger.initialize(self.path, LIMITS)
        link = Path(self.tmp.name)/'linked'
        link.symlink_to(self.path.parent, target_is_directory=True)
        with self.assertRaises((ValueError, OSError)):
            BudgetLedger.initialize(link/'nested'/'new.sqlite3', LIMITS)
        self.assertFalse((self.path.parent/'nested').exists())

    def test_explicit_init_never_chmods_existing_parent(self):
        parent = Path(self.tmp.name)/'public'
        parent.mkdir(mode=0o755)
        with self.assertRaises((ValueError, OSError)):
            BudgetLedger.initialize(parent/'new.sqlite3', LIMITS)
        self.assertEqual(parent.stat().st_mode & 0o777, 0o755)
        self.assertFalse((parent/'new.sqlite3').exists())
