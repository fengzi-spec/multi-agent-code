import unittest

from calculator import calculate_discount


class CalculateDiscountTests(unittest.TestCase):
    def test_applies_discount(self):
        self.assertEqual(calculate_discount(100, 20), 80)

    def test_allows_zero_discount(self):
        self.assertEqual(calculate_discount(25, 0), 25)


if __name__ == "__main__":
    unittest.main()
