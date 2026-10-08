import unittest
from decimal import Decimal

from pricing import line_total


class PricingContractTests(unittest.TestCase):
    def test_fractional_cent_rounding(self):
        self.assertEqual(line_total("1.235", 3), Decimal("3.71"))

    def test_half_cent_rounding(self):
        self.assertEqual(line_total("0.335", 3), Decimal("1.01"))

    def test_whole_cent_price(self):
        self.assertEqual(line_total("12.50", 2), Decimal("25.00"))

    def test_zero_quantity(self):
        self.assertEqual(line_total("12.50", 0), Decimal("0.00"))

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            line_total("12.50", -1)


if __name__ == "__main__":
    unittest.main()
