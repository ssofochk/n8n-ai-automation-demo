import unittest

from src.calculator import add, subtract, multiply, divide, average


class CalculatorTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(8, 2), 10)

    def test_subtract(self):
        self.assertEqual(subtract(8, 2), 6)

    def test_multiply(self):
        self.assertEqual(multiply(8, 2), 16)

    def test_divide(self):
        self.assertEqual(divide(8, 2), 4)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(8, 0)

    def test_average(self):
        self.assertEqual(average([2, 4, 6]), 4)

    def test_average_empty(self):
        with self.assertRaises(ValueError):
            average([])
