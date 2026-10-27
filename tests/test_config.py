import unittest
from benchmarks import config

class TestConfig(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIs(config.load_config(environ={}).paid_tests_enabled, False)

    def test_rejects_nonpositive_budget(self):
        for value in ('0', '-1', 'NaN', 'Infinity', '6', '1.0000001'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                config.load_config(environ={'EVALUATION_BUDGET_USD': value})

    def test_secret_is_not_in_repr(self):
        secret = 'fixture-only-sensitive-token'
        loaded = config.load_config(environ={'OPENROUTER_API_KEY': secret})
        self.assertTrue(getattr(loaded, 'key_present', False))
        self.assertNotIn(secret, repr(loaded))
