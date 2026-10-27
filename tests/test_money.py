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

    def test_actual_cost_not_rounded_down(self):
        convert = getattr(money, 'actual_micro', lambda value: 0)
        self.assertEqual(convert('0.00000100000000000000001'), 2)
        self.assertEqual(convert('4.50'), 4500000)
        for value in ('-0.01', 'NaN', '1e1000000', '1e-1000000', 0.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                convert(value)
