import unittest
from benchmarks import config

class TestConfig(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIs(config.load_config(environ={}).paid_tests_enabled, False)

    def test_rejects_nonpositive_budget(self):
        for value in ('0', '-1', 'NaN', 'Infinity', '6', '1.0000001'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                config.load_config(environ={'EVALUATION_BUDGET_USD': value})
