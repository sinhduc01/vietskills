"""Tests for payroll.py — run with:  python test_payroll.py

Expected values cross-checked against public 2026 sources cited in SKILL.md
(Progressive 5-bracket table, 15.5M/6.2M deductions, 10.5%/21.5% insurance,
caps 46.8M / 50.6M).
"""

import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import payroll as pr  # noqa: E402


class TestProgressiveTable(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(pr.progressive_annual(Decimal(0)), Decimal(0))

    def test_first_bracket(self):
        self.assertEqual(pr.progressive_annual(Decimal("120000000")), Decimal("6000000"))

    def test_second_bracket(self):
        # 120M @5% + 240M @10% = 6M + 24M
        self.assertEqual(pr.progressive_annual(Decimal("360000000")), Decimal("30000000"))

    def test_third_bracket(self):
        # + 360M @20% = 72M
        self.assertEqual(pr.progressive_annual(Decimal("720000000")), Decimal("102000000"))

    def test_fifth_bracket(self):
        # + 480M @30% = 144M; remainder (2B - 1.2B) @35% = 280M
        total = pr.progressive_annual(Decimal("2000000000"))
        self.assertEqual(total, Decimal("526000000"))


class TestMonthlyPit(unittest.TestCase):
    def test_stable_low(self):
        # 10M/month -> annual 120M -> 6M/year -> 500k/month
        self.assertEqual(pr.pit_month_stable(Decimal("10000000")), 500_000)

    def test_stable_rounding(self):
        # 30M/month -> annual 360M -> 30M/12 = 2,500,000
        self.assertEqual(pr.pit_month_stable(Decimal("30000000")), 2_500_000)

    def test_zero(self):
        self.assertEqual(pr.pit_month_stable(Decimal("0")), 0)

    def test_cumulative_varying(self):
        # Month 1: 5M -> 250k. Month 2: running 45M -> 2.25M total, so +2.0M.
        result = pr.pit_month_cumulative([Decimal("5000000"), Decimal("40000000")])
        self.assertEqual(result, [250_000, 2_000_000])


class TestInsuranceCap(unittest.TestCase):
    def test_2025(self):
        self.assertEqual(pr.insurance_cap("2025-06"), Decimal("46800000"))

    def test_2026_h1(self):
        self.assertEqual(pr.insurance_cap("2026-01"), Decimal("46800000"))
        self.assertEqual(pr.insurance_cap("2026-06"), Decimal("46800000"))

    def test_2026_h2(self):
        self.assertEqual(pr.insurance_cap("2026-07"), Decimal("50600000"))

    def test_unknown_year_raises(self):
        with self.assertRaises(ValueError):
            pr.insurance_cap("2027-01")

    def test_explicit_base_ref(self):
        self.assertEqual(pr.insurance_cap("2024-06", Decimal("1800000")), Decimal("36000000"))


class TestPayStub(unittest.TestCase):
    def test_lacviet_example(self):
        """Public example (lacviet.vn, Oct 2026): gross 25M, 1 dependent,
        2026 -> insurance 2,625,000; taxable 675,000; PIT 33,750."""
        s = pr.PayStub(gross=25_000_000, month="2026-08", dependents=1)
        self.assertEqual(pr._vnd(s.employee_insurance()), 2_625_000)
        self.assertEqual(pr._vnd(s.taxable()), 675_000)
        self.assertEqual(s.pit(), 33_750)
        self.assertEqual(s.take_home(), 22_341_250)

    def test_cap_applied_h2_2026(self):
        s = pr.PayStub(gross=100_000_000, month="2026-08", dependents=0)
        self.assertEqual(s.insurance_base(), Decimal("50600000"))
        self.assertEqual(pr._vnd(s.employee_insurance()), 5_313_000)
        # taxable = 100M - 5.313M - 15.5M = 79.187M -> annual 950.244M
        # tax = 6M + 24M + 72M + 230.244M*30% = 171.0732M -> /12 = 14.2561M
        self.assertEqual(s.pit(), 14_256_100)
        self.assertEqual(s.take_home(), 80_430_900)

    def test_cap_applied_h1_2026(self):
        s = pr.PayStub(gross=100_000_000, month="2026-05", dependents=0)
        self.assertEqual(s.insurance_base(), Decimal("46800000"))
        self.assertEqual(pr._vnd(s.employee_insurance()), 4_914_000)

    def test_no_tax_below_threshold(self):
        s = pr.PayStub(gross=15_000_000, month="2026-08", dependents=0)
        self.assertEqual(s.pit(), 0)
        self.assertEqual(s.take_home(), 15_000_000 - 1_575_000)

    def test_employer_insurance(self):
        s = pr.PayStub(gross=20_000_000, month="2026-08")
        self.assertEqual(pr._vnd(s.employer_insurance()), 4_300_000)

    def test_dependent_deduction(self):
        s = pr.PayStub(gross=30_000_000, month="2026-08", dependents=2)
        # taxable = 30M - 3.15M - 15.5M - 12.4M = -1.05M -> 0
        self.assertEqual(pr._vnd(s.taxable()), 0)
        self.assertEqual(s.pit(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
