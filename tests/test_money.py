import unittest
from benchmarks import money

class TestMoney(unittest.TestCase):
    def test_decimal_rounds_reservation_up(self):
        self.assertEqual(money.reserve_micro('0.0000001'), 1)
        self.assertEqual(money.reserve_micro('0.20'), 200000)
        self.assertEqual(money.reserve_micro('0'), 0)
        for value in ('-1', 'NaN', 'Infinity', 0.2):
            with self.subTest(value=value), self.assertRaises(ValueError):
                money.reserve_micro(value)
