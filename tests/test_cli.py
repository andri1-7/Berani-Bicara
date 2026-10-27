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
