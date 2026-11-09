---
name: e-invoice
description: Validate Vietnamese electronic invoices (hóa đơn điện tử). Use when the user provides an HD XML file, asks to check invoice validity (hóa đơn hợp lệ / hợp pháp), detect arithmetic or format errors, or decide how to fix an invoice mistake (điều chỉnh / thay thế / thông báo sai sót) under Vietnamese e-invoice rules.
---

# E-Invoice (Hóa đơn điện tử)

Validate Vietnamese e-invoice XML files and guide the correct fix for each
kind of invoice error.

## When to use
- The user hands you an `*.xml` e-invoice and asks "hóa đơn này có hợp lệ không?"
- A user is building an invoicing module and needs the XML structure + consistency rules.
- The user found an error on a received invoice and asks what to do (điều chỉnh? thay thế? thông báo?).

## Workflow
1. Run the validator:
   ```bash
   python scripts/validate_hd.py <file.xml>          # human output
   python scripts/validate_hd.py --json <file.xml>   # machine-readable
   ```
   Exit code 0 = no ERROR findings; 1 = invalid.
2. Interpret findings:
   - `ERROR` = the document fails a structural or arithmetic rule → not a valid
     tax document as-is; tell the user exactly which line/field is wrong.
   - `WARN` = plausible but suspicious (e.g. short MST, missing optional
     section) → ask the user to double-check.
3. Map the error to the fix decision table below.
4. **Always say**: local validation is not a substitute for the legal check.
   When it matters (audit, tax filing, dispute), verify the invoice at the
   General Department of Taxes portal: https://hoadondientu.gdt.gov.vn
   (enter MST + invoice number + date, or upload the XML file).

## Legal framework (as of 2026-11)
| Period | Decree | Circular |
|---|---|---|
| from 01/07/2026 | Decree 254/2026/NĐ-CP | Circular 91/2026/TT-BTC |
| 01/06/2025 – 30/06/2026 | Decree 70/2025/NĐ-CP | Circular 32/2025/TT-BTC |
| 01/07/2022 – 31/05/2025 | Decree 123/2020/NĐ-CP | Circular 78/2021/TT-BTC |

The business XML format (root `<DonHieu>`, sections `ThongTinChung`,
`ThongTinHoaDon`, `ChiTietHD`, `TongTien`, …) is the same across all three
regimes; the validator targets that format. For invoices dated before
01/07/2026, cite the old circular when giving fix advice.

## Fix decision table
Current rule (Art. 10, Circular 91/2026; for pre-2026 invoices: Art. 19,
Circular 78/2021):

| Error found on the invoice | Action |
|---|---|
| Buyer's name or address wrong, **MST correct** | Notify on Form 04/SS-HĐĐT — no adjustment invoice needed |
| Buyer's MST wrong | Adjustment (điều chỉnh) or replacement (thay thế) invoice |
| Amount, tax rate, or VAT amount wrong | Adjustment or replacement invoice |
| Item/goods name wrong | Adjustment or replacement invoice |
| Seller's name, address or MST wrong | Replacement invoice (1-for-1) |
| Wrong invoice symbol (STKH) or year (NHD) | Replacement invoice |
| Wrong sequence number (STTHD) | Replacement invoice |

Adjustment/replacement invoices must reference the original in the `KHCN`
field (type + date + number of the original invoice).

## Rules implemented in `scripts/validate_hd.py`
- Well-formed XML, root `<DonHieu>`.
- Required fields: `ThongTinChung` (TenCoSo, MSTCoSo, DiaChiCS, STKH, NHD),
  `ThongTinHoaDon` (STTHD, NgHD, NCC, NDKH, HDTT, STKH, NHD), ≥1 `ChiTietHD`,
  `TongTien`.
- Per line: `SoLuong > 0`; `ThanhTien = SoLuong × DonGia`;
  `TienChiPhiGoc = ThanhTien`; `ThueGTGT = TienChiPhiGoc × ThueSuat`;
  `TienHangDichVu = TienChiPhiGoc + ThueGTGT` (tolerance 1 VND or 0.01%).
- Totals: line sums match `TongChiPhiGoc`, `TGTGT`, `ThanhTien`.
- `NgHD` must be `dd/MM/yyyy` and a real date.
- `MSTCoSo` should be 10 digits (organization) or 12–13 (individual).
- `NCC` ∈ {1 cash, 2 transfer, 3 other}; `NDKH` check code 2 or 4 digits.

## Gotchas
- Amounts in the XML may use `.` as thousands separator (`1.234.567`),
  `,` as decimal (`1234,56`), or `.` as decimal (`1234.56`). The parser
  handles all; do not "fix" amounts by string replacement.
- `ThueSuat = "KH"` means exempt (0%), not a missing rate.
- The 4-digit check code (`NDKH`) is bound to the exact byte sequence of the
  document submitted to the tax authority — it cannot be recomputed from a
  received file. Never claim it is "wrong" without the GDT portal.
- A received invoice may be the *buyer's* view: seller sections describe the
  issuer. Do not assume the user's company is the seller.
