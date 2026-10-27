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
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path.parent, 0o700)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        os.chmod(self.path, 0o600)
        with self._transaction() as db:
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
        with self._transaction() as db:
            used = db.execute('SELECT COALESCE(SUM(COALESCE(actual_micro, reserved_micro)), 0) FROM requests WHERE stage=?', (stage,)).fetchone()[0]
            if used + amount > self.limits.get(stage, 0):
                raise BudgetExceeded('Stage budget exceeded')
            request_id = uuid.uuid4().hex
            db.execute("INSERT INTO requests (id, stage, reserved_micro, status) VALUES (?, ?, ?, 'reserved')", (request_id, stage, amount))
            return request_id
