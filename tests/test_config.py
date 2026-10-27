import unittest
from benchmarks import config

class TestConfig(unittest.TestCase):
    def test_direct_construction_enforces_invariants(self):
        cases = [dict(paid_tests_enabled=value) for value in ('false', 0, 1, None)]
        cases += [dict(api_key=value) for value in (None, 1, True, b'key')]
        cases += [dict(total_limit='500'), dict(stop_line='4.500001'),
                  dict(total_limit='1', stop_line='2'), dict(total_limit='0'),
                  dict(total_limit='1.0000000000000000000000000001', stop_line='1')]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                config.Config(**kwargs)

    def test_long_fractional_micro_setting_rejected(self):
        with self.assertRaises(ValueError):
            config.load_config(environ={'EVALUATION_BUDGET_USD': '1.0000000000000000000000000001'})

    def test_direct_constructor_enforces_invariants(self):
        for kwargs in ({'paid_tests_enabled': 'false'}, {'paid_tests_enabled': 1},
                       {'total_limit': '500'}, {'stop_line': '4.51'},
                       {'total_limit': '1', 'stop_line': '2'}, {'api_key': True},
                       {'total_limit': 'NaN'}, {'total_limit': '0'},
                       {'total_limit': '1.0000001'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                config.Config(**kwargs)

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
