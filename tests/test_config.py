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

    def test_literal_parser_and_explicit_enable(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'fixture.env'
            path.write_text('OPENROUTER_API_KEY="literal-$HOME-$(false)"\nPAID_TESTS_ENABLED=true\n')
            loaded = config.load_config(path=path, environ={})
            self.assertEqual(loaded.api_key, 'literal-$HOME-$(false)')
            self.assertTrue(loaded.paid_tests_enabled)

    def test_malformed_duplicate_or_ambiguous_config_fails_closed(self):
        import tempfile
        from pathlib import Path
        cases = ['OPENROUTER_API_KEY=a\nOPENROUTER_API_KEY=b', 'export PAID_TESTS_ENABLED=true',
                 'PAID_TESTS_ENABLED=yes', 'OPENROUTER_API_KEY="unterminated',
                 'OPENROUTER_API_KEY=foo # ambiguous', 'UNKNOWN=value']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'fixture.env'
            for text in cases:
                with self.subTest(text=text):
                    path.write_text(text)
                    with self.assertRaises(ValueError) as caught:
                        config.load_config(path=path, environ={})
                    self.assertNotIn(text, str(caught.exception))
