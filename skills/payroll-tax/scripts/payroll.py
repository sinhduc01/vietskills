"""Vietnamese payroll deductions: mandatory insurance + personal income tax (TNCN).

Rules encoded (as of 2026, verified against public sources — see SKILL.md):

Insurance (BHXH Law 2024, in force for 2026):
  - Employee: 8% BHXH + 1.5% BHYT + 1% BHTN = 10.5% of the contribution base.
  - Employer: 17.5% + 3% + 1% = 21.5% of the same base.
  - Base = wage, capped at 20 x reference salary (muc tham chieu = luong co so):
      46,800,000 VND/month until 30/06/2026 (ref 2,340,000)
      50,600,000 VND/month from 01/07/2026 (ref 2,530,000)

PIT (PIT Law 109/2025/QH15, wage income of residents, tax year 2026+):
  - Taxable income = gross - tax-exempt parts - mandatory insurance -
    deductions (15,500,000/month for self + 6,200,000/month per registered
    dependent, per Resolution 110/2025/UBTVQH15).
  - Progressive partial table (annual):  <= 120M: 5%;  120-360M: 10%;
    360-720M: 20%;  720M-1.2B: 30%;  > 1.2B: 35%.
  - Monthly withholding for a stable monthly taxable income:
    progressive(annual) / 12.
  - Varying income: progressive tax on the cumulative annual taxable income,
    minus tax already withheld (per-month difference).

Usage
    python payroll.py --gross 25000000 --month 2026-08 --dependents 1
    python payroll.py --gross 25000000 --month 2026-08 --dependents 1 --json

Python API
    from payroll import PayStub
    s = PayStub(gross=25_000_000, month="2026-08", dependents=1)
    s.pit()           # 33750
    s.take_home()     # 22341250
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

# --- constants (2026) ------------------------------------------------------

INSURANCE_EMPLOYEE_RATE = Decimal("0.105")   # 8 + 1.5 + 1
INSURANCE_EMPLOYER_RATE = Decimal("0.215")   # 17.5 + 3 + 1
DEDUCTION_SELF = Decimal("15500000")         # per month, from 2026
DEDUCTION_DEPENDENT = Decimal("6200000")     # per registered dependent, per month

# Progressive partial table, annual amounts in VND.
BRACKETS_2026 = (
    (Decimal("120000000"), Decimal("0.05")),
    (Decimal("360000000"), Decimal("0.10")),
    (Decimal("720000000"), Decimal("0.20")),
    (Decimal("1200000000"), Decimal("0.30")),
    (None, Decimal("0.35")),
)

# Insurance base caps: (year, month) -> 20 x reference salary.
INS_CAP_2026 = (Decimal("46800000"), Decimal("50600000"))  # before / from 01/07/2026


def _vnd(amount: Decimal) -> int:
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def insurance_cap(month: str, base_ref: Decimal | None = None) -> Decimal:
    """Insurance base cap for a YYYY-MM month. Pass base_ref (reference
    salary) explicitly for years other than 2025-2026."""
    if base_ref is not None:
        return base_ref * 20
    y, m = map(int, month.split("-"))
    if (y, m) < (2025, 1):
        raise ValueError(
            f"month {month}: pre-2025 rules differ (ref salary 1.8M in 2024); "
            "pass base_ref explicitly")
    if (y, m) <= (2026, 6):
        return INS_CAP_2026[0]
    if (y, m) <= (2026, 12):
        return INS_CAP_2026[1]
    raise ValueError(f"month {month}: reference salary after 2026 is unknown — pass base_ref")


def progressive_annual(taxable: Decimal) -> Decimal:
    """PIT for the year on an annual taxable income (progressive partial)."""
    if taxable <= 0:
        return Decimal("0")
    total = Decimal("0")
    prev = Decimal("0")
    for cap, rate in BRACKETS_2026:
        if cap is None:
            total += (taxable - prev) * rate
            break
        if taxable > prev:
            total += (min(taxable, cap) - prev) * rate
            prev = cap
            if taxable <= cap:
                break
    return total


def pit_month_stable(taxable_month: Decimal) -> int:
    """Monthly withholding when the same taxable income continues all year."""
    if taxable_month <= 0:
        return 0
    return _vnd(progressive_annual(taxable_month * 12) / 12)


def pit_month_cumulative(monthly_taxables: list[Decimal]) -> list[int]:
    """Per-month PIT for varying income: progressive on the running annual
    taxable total, taking the difference each month."""
    out: list[int] = []
    running = Decimal("0")
    for t in monthly_taxables:
        prev = running
        running += max(t, Decimal("0"))
        out.append(_vnd(progressive_annual(running)) - _vnd(progressive_annual(prev)))
    return out


@dataclass
class PayStub:
    """One month of payroll for one employee. All money in VND (int or Decimal)."""

    gross: int | Decimal
    month: str = "2026-08"          # YYYY-MM
    dependents: int = 0             # registered dependents
    base_ref: int | Decimal | None = None   # reference salary, for non-2026 months

    def __post_init__(self) -> None:
        self.gross = Decimal(self.gross)

    def insurance_base(self) -> Decimal:
        cap = insurance_cap(self.month,
                            Decimal(self.base_ref) if self.base_ref is not None else None)
        return min(self.gross, cap)

    def employee_insurance(self) -> Decimal:
        return self.insurance_base() * INSURANCE_EMPLOYEE_RATE

    def employer_insurance(self) -> Decimal:
        return self.insurance_base() * INSURANCE_EMPLOYER_RATE

    def taxable(self) -> Decimal:
        t = (self.gross - self.employee_insurance()
             - DEDUCTION_SELF - DEDUCTION_DEPENDENT * self.dependents)
        return max(t, Decimal("0"))

    def pit(self) -> int:
        return pit_month_stable(self.taxable())

    def take_home(self) -> int:
        return _vnd(self.gross - self.employee_insurance() - Decimal(self.pit()))

    def as_dict(self) -> dict:
        return {
            "gross": int(self.gross),
            "month": self.month,
            "dependents": self.dependents,
            "insurance_base": int(self.insurance_base()),
            "employee_insurance": int(_vnd(self.employee_insurance())),
            "employer_insurance": int(_vnd(self.employer_insurance())),
            "deduction_self": int(DEDUCTION_SELF),
            "deduction_dependents": int(DEDUCTION_DEPENDENT * self.dependents),
            "taxable": int(_vnd(self.taxable())),
            "pit": self.pit(),
            "take_home": self.take_home(),
        }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Usage")[0])
    ap.add_argument("--gross", type=int, required=True, help="gross monthly wage, VND")
    ap.add_argument("--month", default="2026-08", help="YYYY-MM (default 2026-08)")
    ap.add_argument("--dependents", type=int, default=0, help="registered dependents")
    ap.add_argument("--base-ref", type=int, default=None,
                    help="reference salary for the month (needed for non-2026 months)")
    ap.add_argument("--json", action="store_true")
    ns = ap.parse_args(argv)

    try:
        s = PayStub(gross=ns.gross, month=ns.month,
                    dependents=ns.dependents, base_ref=ns.base_ref)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    if ns.json:
        print(json.dumps(s.as_dict(), ensure_ascii=False, indent=2))
        return 0

    d = s.as_dict()
    rows = [
        ("Gross (luong truoc thue)", d["gross"]),
        ("Insurance base (can cu do BHXH)", d["insurance_base"]),
        ("Employee insurance 10.5%", -d["employee_insurance"]),
        ("  = employer pays 21.5%", d["employer_insurance"]),
        ("Deduction for self (GTGC ban than)", -d["deduction_self"]),
        ("Deduction dependents (GTGC NPT)", -d["deduction_dependents"]),
        ("Taxable income (TNCT)", d["taxable"]),
        ("PIT (thue TNCN)", -d["pit"]),
        ("Take home (luong sau thue)", d["take_home"]),
    ]
    for label, val in rows:
        sign = "-" if val < 0 else "+"
        print(f"{label:<36} {sign} {abs(val):>15,} VND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
