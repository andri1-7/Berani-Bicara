import subprocess
import unittest

class TestRepositoryHygiene(unittest.TestCase):
    def test_private_paths_are_ignored(self):
        for path in ('.env', 'private/ledger.sqlite3', 'recordings/sample.wav',
                     'benchmark-results/session.json', '.venv/', '.hermes/plans/private.md'):
            with self.subTest(path=path):
                self.assertEqual(subprocess.run(['git', 'check-ignore', '--quiet', path]).returncode, 0)
