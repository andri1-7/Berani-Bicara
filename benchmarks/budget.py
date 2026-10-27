"""Atomic persistent evaluation accounting. No networking or automatic resets."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import uuid
from .money import reserve_micro, actual_micro
from decimal import Decimal, localcontext
from types import MappingProxyType


DEFAULT_STAGE_LIMITS = MappingProxyType({'smoke': '0.25', 'grammar': '0.75', 'transcription': '0.75',
                        'tts': '0.75', 'conversation': '1.00'})


class BudgetExceeded(ValueError):
    """Reservation refused without changing exposure."""


class BudgetLedger:
    def __init__(self, path, stage_limits, total_limit='5.00', stop_line='4.50'):
        for value in [*stage_limits.values(), total_limit, stop_line]:
            rounded = reserve_micro(value)
            with localcontext() as ctx:
                ctx.prec = 250
                if Decimal(value) * 1000000 != rounded:
                    raise ValueError('Limits must be exact microUSD')
        self.path = Path(path)
        self.limits = {stage: reserve_micro(value) for stage, value in stage_limits.items()}
        self.total_limit = reserve_micro(total_limit)
        self.stop_line = reserve_micro(stop_line)
        if not self.limits or any(not isinstance(stage, str) or not stage.isidentifier() or stage not in DEFAULT_STAGE_LIMITS or value <= 0 or value > reserve_micro(DEFAULT_STAGE_LIMITS[stage]) for stage, value in self.limits.items()):
            raise ValueError('Invalid stage limits')
        if not 0 < self.stop_line <= min(self.total_limit, 4500000) or self.total_limit > 5000000:
            raise ValueError('Invalid total limits')
        with self._connection(readonly=True) as db:
            self._validate_schema(db)

    @classmethod
    def initialize(cls, path, stage_limits, total_limit='5.00', stop_line='4.50'):
        # Validate policy before creating anything; normal construction only opens.
        ledger = cls.__new__(cls)
        ledger.path = Path(path)
        ledger.limits = {stage: reserve_micro(value) for stage, value in stage_limits.items()}
        ledger.total_limit = reserve_micro(total_limit)
        ledger.stop_line = reserve_micro(stop_line)
        from .config import limit
        limit(total_limit, '5')
        limit(stop_line, '4.50')
        if ledger.stop_line > ledger.total_limit or not ledger.limits:
            raise ValueError('Invalid total limits')
        for stage, value in stage_limits.items():
            if stage not in DEFAULT_STAGE_LIMITS:
                raise ValueError('Invalid stage limits')
            limit(value, DEFAULT_STAGE_LIMITS[stage])
        with ledger._parent(create=True) as parent:
            fd = os.open(ledger.path.name, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            os.close(fd)
            with ledger._transaction() as db:
                db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
                db.execute("INSERT INTO metadata VALUES ('policy', ?)", (ledger._policy(),))
                db.execute('CREATE TABLE requests (id TEXT PRIMARY KEY, stage TEXT NOT NULL, reserved_micro INTEGER NOT NULL, actual_micro INTEGER, status TEXT NOT NULL, generation_id TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        return cls(path, stage_limits, total_limit, stop_line)

    def _policy(self):
        return json.dumps({'version': 1, 'stage_limits': self.limits, 'total_limit': self.total_limit, 'stop_line': self.stop_line}, sort_keys=True)

    def _validate_schema(self, db):
        expected = {'metadata': ['key', 'value'], 'requests': ['id', 'stage', 'reserved_micro', 'actual_micro', 'status', 'generation_id', 'created_at']}
        for table, columns in expected.items():
            if [row[1] for row in db.execute('PRAGMA table_info(' + table + ')')] != columns:
                raise ValueError('Ledger schema missing or incompatible')
        policy = db.execute("SELECT value FROM metadata WHERE key='policy'").fetchone()
        if policy is None or policy[0] != self._policy():
            raise ValueError('Ledger policy is missing or immutable')

    @contextmanager
    def _parent(self, create=False):
        # Traverse using directory descriptors: no symlink ancestor or chmod side effects.
        parts = self.path.absolute().parts
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in parts[1:-1]:
                if part in ('.', '..'):
                    raise ValueError('Unsafe ledger path')
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
            if create and os.fstat(fd).st_mode & 0o077:
                raise ValueError('Ledger parent must already be private')
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def _connection(self, readonly=False):
        with self._parent() as parent:
            fd = os.open(self.path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                import stat
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise ValueError('Ledger must be a regular file')
                from urllib.parse import quote
                uri = 'file:' + quote('/proc/self/fd/' + str(parent) + '/' + self.path.name) + '?mode=' + ('ro' if readonly else 'rw')
                db = sqlite3.connect(uri, uri=True, timeout=10)
                db.row_factory = sqlite3.Row
                try:
                    if readonly:
                        db.execute('PRAGMA query_only=ON')
                    yield db
                finally:
                    db.close()
            finally:
                os.close(fd)

    @contextmanager
    def _transaction(self):
        with self._connection() as db:
            try:
                db.execute('PRAGMA synchronous=FULL')
                db.execute('BEGIN IMMEDIATE')
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise

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
        with self._connection(readonly=True) as db:
            db.execute('BEGIN')
            self._validate_schema(db)
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
