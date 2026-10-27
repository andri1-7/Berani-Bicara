"""Atomic persistent evaluation accounting. No networking or automatic resets."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import uuid
from .money import reserve_micro, actual_micro


DEFAULT_STAGE_LIMITS = {'smoke': '0.25', 'grammar': '0.75', 'transcription': '0.75',
                        'tts': '0.75', 'conversation': '1.00'}


class BudgetExceeded(ValueError):
    """Reservation refused without changing exposure."""


class BudgetLedger:
    def __init__(self, path, stage_limits, total_limit='5.00', stop_line='4.50'):
        self.path = Path(path)
        self.limits = {stage: reserve_micro(value) for stage, value in stage_limits.items()}
        self.total_limit = reserve_micro(total_limit)
        self.stop_line = reserve_micro(stop_line)
        if not self.limits or any(not isinstance(stage, str) or not stage.isidentifier() or stage == 'contingency' or value <= 0 for stage, value in self.limits.items()):
            raise ValueError('Invalid stage limits')
        if not 0 < self.stop_line <= min(self.total_limit, 4500000) or self.total_limit > 5000000:
            raise ValueError('Invalid total limits')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        os.chmod(self.path, 0o600)
        with self._transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            policy = json.dumps({'version': 1, 'stage_limits': self.limits, 'total_limit': self.total_limit, 'stop_line': self.stop_line}, sort_keys=True)
            existing = db.execute("SELECT value FROM metadata WHERE key='policy'").fetchone()
            if existing is None:
                db.execute("INSERT INTO metadata VALUES ('policy', ?)", (policy,))
            elif existing[0] != policy:
                raise ValueError('Ledger policy is immutable')
            db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, stage TEXT NOT NULL, reserved_micro INTEGER NOT NULL, actual_micro INTEGER, status TEXT NOT NULL, generation_id TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def reserve(self, stage, upper_usd):
        amount = reserve_micro(upper_usd)
        if amount <= 0:
            raise ValueError('Reservation must be positive')
        if stage not in self.limits:
            raise BudgetExceeded('Unknown or locked stage')
        with self._transaction() as db:
            if db.execute("SELECT 1 FROM metadata WHERE key='halted'").fetchone():
                raise BudgetExceeded('Account halted after cost overrun')
            if db.execute("SELECT 1 FROM requests WHERE actual_micro IS NULL LIMIT 1").fetchone():
                raise BudgetExceeded('Outstanding request blocks dispatch')
            total = db.execute('SELECT COALESCE(SUM(COALESCE(actual_micro, reserved_micro)), 0) FROM requests').fetchone()[0]
            if total + amount > min(self.total_limit, self.stop_line):
                raise BudgetExceeded('Operational or total budget exceeded')
            used = db.execute('SELECT COALESCE(SUM(COALESCE(actual_micro, reserved_micro)), 0) FROM requests WHERE stage=?', (stage,)).fetchone()[0]
            if used + amount > self.limits.get(stage, 0):
                raise BudgetExceeded('Stage budget exceeded')
            request_id = uuid.uuid4().hex
            db.execute("INSERT INTO requests (id, stage, reserved_micro, status) VALUES (?, ?, ?, 'reserved')", (request_id, stage, amount))
            return request_id

    def mark_unknown(self, request_id):
        with self._transaction() as db:
            changed = db.execute("UPDATE requests SET status='unknown' WHERE id=? AND status='reserved' AND actual_micro IS NULL", (request_id,)).rowcount
            if changed != 1:
                raise ValueError('Request is missing or already reconciled/unknown')

    def summary(self):
        with self._transaction() as db:
            rows = db.execute('SELECT stage, reserved_micro, actual_micro, status FROM requests').fetchall()
            confirmed = sum(row['actual_micro'] for row in rows if row['actual_micro'] is not None)
            reserved = sum(row['reserved_micro'] for row in rows if row['actual_micro'] is None)
            remaining = max(0, min(self.total_limit, self.stop_line) - confirmed - reserved)
            halted = db.execute("SELECT 1 FROM metadata WHERE key='halted'").fetchone() is not None
            available = {stage: max(0, min(remaining, cap - sum(row['actual_micro'] if row['actual_micro'] is not None else row['reserved_micro'] for row in rows if row['stage'] == stage))) for stage, cap in self.limits.items()}
            return {'remaining_micro': remaining, 'available_by_stage_micro': available,
                    'total_limit_micro': self.total_limit, 'stop_line_micro': self.stop_line,
                    'outstanding': sum(row['actual_micro'] is None for row in rows),
                    'dispatch_allowed': not halted and not any(row['actual_micro'] is None for row in rows) and any(available.values()),
                    'confirmed_micro': confirmed, 'reserved_micro': reserved,
                    'unresolved': sum(row['status'] == 'unknown' for row in rows),
                    'halted': db.execute("SELECT 1 FROM metadata WHERE key='halted'").fetchone() is not None}

    def settle(self, request_id, actual_usd):
        amount = actual_micro(actual_usd)
        with self._transaction() as db:
            original = db.execute('SELECT reserved_micro FROM requests WHERE id=?', (request_id,)).fetchone()
            if original is not None and amount > original[0]:
                db.execute("INSERT OR IGNORE INTO metadata VALUES ('halted', 'overrun')")
            changed = db.execute("UPDATE requests SET actual_micro=?, status='settled' WHERE id=? AND actual_micro IS NULL AND status IN ('reserved', 'unknown')", (amount, request_id)).rowcount
            if changed != 1:
                raise ValueError('Request is missing or already settled')
