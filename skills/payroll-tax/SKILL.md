---
name: payroll-tax
description: Compute Vietnamese payroll deductions — mandatory social/health/unemployment insurance and personal income tax (TNCN) — under the 2026 rules (PIT Law 109/2025/QH15 + Resolution 110/2025). Use when the user asks to tính lương, tính thuế TNCN, BHXH/BHYT/BHTN, or build a payroll module.
---

# Payroll & Personal Income Tax (Vietnam, 2026)

Compute one employee's monthly deductions correctly, then explain the
breakdown in Vietnamese.

## When to use
- "Tính lương sau thuế cho nhân viên lương 25 triệu, 1 người phụ thuộc"
- "Thuế TNCN tháng này bao nhiêu?"
- Building a payroll module: use the Python API (`from payroll import PayStub`)
  instead of re-implementing the brackets.

## Workflow
1. Gather: gross monthly wage (VND), month (YYYY-MM), number of **registered**
   dependents (người phụ thuộc — only those declared to the tax office), and
   whether the wage is stable all year or varies.
2. Run the script:
   ```bash
   python scripts/payroll.py --gross 25000000 --month 2026-08 --dependents 1
   ```
   or the Python API:
   ```python
   from payroll import PayStub
   s = PayStub(gross=25_000_000, month="2026-08", dependents=1)
   s.take_home()   # 22_341_250
   ```
   For a month with **varying** income, use
   `pr.pit_month_cumulative([...monthly taxable incomes...])` instead of
   `s.pit()`.
3. Present the breakdown table (gross → insurance base → insurance →
   deductions → taxable income → PIT → take-home) in VND.
4. State the caveats (below) in one or two lines.

## Rules encoded (2026, verified)

**Mandatory insurance** (BHXH Law 2024, in force for 2026)
| | Employee | Employer |
|---|---|---|
| BHXH | 8% | 17.5% |
| BHYT | 1.5% | 3% |
| BHTN | 1% | 1% |
| **Total** | **10.5%** | **21.5%** |

Contribution base = wage, capped at **20 × reference salary**:
- 46,800,000/month (ref 2,340,000) until 30/06/2026
- 50,600,000/month (ref 2,530,000) from 01/07/2026

**PIT** (Law 109/2025/QH15, residents, wage income, tax year 2026+)
- Taxable income = gross − tax-exempt parts − mandatory insurance −
  deductions:
  - for self: **15,500,000/month**
  - per registered dependent: **6,200,000/month**
  (Resolution 110/2025/UBTVQH15)
- Progressive partial table on **annual** taxable income:
  | Annual taxable (VND) | Rate |
  |---|---|
  | ≤ 120,000,000 | 5% |
  | 120M – 360M | 10% |
  | 360M – 720M | 20% |
  | 720M – 1.2B | 30% |
  | > 1.2B | 35% |
- Monthly withholding for stable income = progressive(annual) / 12;
  varying income = progressive on the cumulative annual total, minus tax
  already withheld (the script does both).

## Caveats — always state
- Only **registered** dependents (declared with form 06/ĐK-TCT) count; the
  script does not check dependency eligibility.
- Some income may be tax-exempt (bonuses ≤ 3 months' wage under the 2025 PIT
  Law, in-kind allowances within limits) — if any applies, subtract it from
  gross before running the script.
- This computes **withholding** (thanh toán tạm tính) for one year. If the
  employee has taxable income in multiple years or the withholding deviates,
  the annual settlement (kê khai quyết toán) may differ.
- For months outside 2025–2026 pass `--base-ref` (reference salary for that
  month); 2027+ figures are not yet known to the script.

## Tests
```bash
python test_payroll.py
```
Expected values are cross-checked against the public lacviet.vn 2026 worked
example (25M, 1 dependent → PIT 33,750) and the 5-bracket table.
