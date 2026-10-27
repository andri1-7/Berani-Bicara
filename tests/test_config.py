import unittest
from benchmarks import config

class TestConfig(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIs(config.load_config(environ={}).paid_tests_enabled, False)
