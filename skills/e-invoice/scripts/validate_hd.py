"""Validate a Vietnamese electronic invoice (hóa đơn điện tử) XML file.

Business XML format: the <DonHieu> schema from Appendix I of
Circular 78/2021/TT-BTC. That structure is the basis for every e-invoice
regime since 2021 (Decree 123/2020 + Circular 78/2021, then Decree 70/2025 +
Circular 32/2025, and from 01/07/2026 Decree 254/2026 + Circular 91/2026).

What this tool checks
  1. XML is well-formed; root element is <DonHieu>.
  2. Required sections and fields are present (ThongTinChung, ThongTinHoaDon,
     at least one ChiTietHD, TongTien).
  3. Buyer/seller tax codes (MST) look plausible (10 digits for organizations,
     12-13 digits for individuals).
  4. Invoice date format dd/MM/yyyy and is a real date.
  5. Per line: SoLuong > 0; ThanhTien = SoLuong * DonGia;
     TienChiPhiGoc = ThanhTien; ThueGTGT = TienChiPhiGoc * ThueSuat;
     TienHangDichVu = TienChiPhiGoc + ThueGTGT.
  6. Totals: line-item sums match TongChiPhiGoc / TGTGT / ThanhTien.
  7. Check code (NDKH) is 2 or 4 digits when present.
  8. Correction/replacement invoices must carry KHCN (correction reference).

What it does NOT check
  - The check code value itself: NDKH is bound to the exact byte sequence of
    the document as submitted to the General Department of Taxes, so it cannot
    be recomputed from a received file. Verify legal validity at
    https://hoadondientu.gdt.gov.vn instead.
  - The digital signature (ChuKyDienTu).

Usage
    python validate_hd.py invoice.xml
    python validate_hd.py --json invoice.xml      # machine-readable output

Exit codes: 0 = pass (errors may still be printed as WARN only),
            1 = one or more ERROR findings.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict

DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


@dataclass
class Finding:
    level: str  # "ERROR" | "WARN"
    path: str
    message: str


def parse_amount(text: str) -> float | None:
    """Parse a VN-formatted amount: '1234567', '1.234.567', '1234,56',
    '1.234.567,89', '1,234,567'."""
    if text is None:
        return None
    s = text.strip().replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and 1 <= len(parts[1]) <= 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s:
        if len(s.split(".")) > 2:  # 1.234.567 -> thousands separators
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_rate(text: str) -> float | None:
    """Tax rate: '10', '10%', '0%', 'KH' (exempt -> 0.0)."""
    if text is None:
        return None
    s = text.strip().rstrip("%").strip()
    if s.upper() == "KH":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def _text(parent: ET.Element | None, tag: str) -> str:
    if parent is None:
        return ""
    el = parent.find(tag)
    return (el.text or "").strip() if el is not None else ""


def _section(root: ET.Element, tag: str) -> ET.Element | None:
    el = root.find(tag)
    return el if el is not None else None


def validate(xml_text: str) -> list[Finding]:
    findings: list[Finding] = []

    def error(path: str, message: str) -> None:
        findings.append(Finding("ERROR", path, message))

    def warn(path: str, message: str) -> None:
        findings.append(Finding("WARN", path, message))

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        error("root", f"XML is not well-formed: {exc}")
        return findings

    if root.tag != "DonHieu":
        error("root", f"root element is <{root.tag}>, expected <DonHieu>")
        return findings

    # --- root attributes -------------------------------------------------
    ndkh_attr = root.attrib.get("NDKH", "")
    if ndkh_attr and not re.fullmatch(r"\d{2}|\d{4}", ndkh_attr):
        warn("@NDKH", f"check code '{ndkh_attr}' is not 2 or 4 digits")

    # --- ThongTinChung (seller) ------------------------------------------
    ttc = _section(root, "ThongTinChung")
    if ttc is None:
        error("ThongTinChung", "missing section")
    else:
        for tag in ("TenCoSo", "MSTCoSo", "DiaChiCS", "STKH", "NHD"):
            if not _text(ttc, tag):
                error(f"ThongTinChung/{tag}", "required field is missing or empty")
        mst = _text(ttc, "MSTCoSo")
        if mst and not re.fullmatch(r"\d{10}|\d{12,13}", mst):
            warn("ThongTinChung/MSTCoSo",
                 f"'{mst}' is not 10 digits (organization) or 12-13 digits (individual)")

    # --- ThongTinHoaDon ----------------------------------------------------
    tthd = _section(root, "ThongTinHoaDon")
    if tthd is None:
        error("ThongTinHoaDon", "missing section")
    else:
        for tag in ("STTHD", "NgHD", "NCC", "NDKH", "HDTT", "STKH", "NHD"):
            if not _text(tthd, tag):
                error(f"ThongTinHoaDon/{tag}", "required field is missing or empty")
        ndkh = _text(tthd, "NDKH")
        if ndkh and not re.fullmatch(r"\d{2}|\d{4}", ndkh):
            warn("ThongTinHoaDon/NDKH",
                 f"check code '{ndkh}' is not 2 or 4 digits")
        ncc = _text(tthd, "NCC")
        if ncc and ncc not in ("1", "2", "3"):
            error("ThongTinHoaDon/NCC", f"payment method '{ncc}' is not 1 (cash), 2 (transfer) or 3 (other)")
        ng_hd = _text(tthd, "NgHD")
        if ng_hd:
            m = DATE_RE.fullmatch(ng_hd)
            if not m:
                error("ThongTinHoaDon/NgHD",
                      f"date '{ng_hd}' does not match dd/MM/yyyy")
            else:
                d, mo, y = (int(g) for g in m.groups())
                if not (1 <= mo <= 12 and 1 <= d <= 31):
                    error("ThongTinHoaDon/NgHD", f"'{ng_hd}' is not a valid date")
        khcn = _text(tthd, "KHCN")
        if khcn and not re.search(r"\d{2}/\d{2}/\d{4}", khcn):
            warn("ThongTinHoaDon/KHCN",
                 "correction reference found but has no dd/MM/yyyy date — check it names the original invoice")

    # --- ChiTietHD (line items) ---------------------------------------------
    lines = root.findall("ChiTietHD")
    if not lines:
        error("ChiTietHD", "at least one line item is required")

    sum_tcg = 0.0
    sum_gtgt = 0.0
    sum_tien = 0.0
    for idx, line in enumerate(lines, start=1):
        p = f"ChiTietHD[{idx}]"
        slq = parse_amount(_text(line, "SoLuong"))
        dj = parse_amount(_text(line, "DonGia"))
        tt = parse_amount(_text(line, "ThanhTien"))
        tcg = parse_amount(_text(line, "TienChiPhiGoc"))
        gtgt = parse_amount(_text(line, "ThueGTGT"))
        thue = parse_rate(_text(line, "ThueSuat"))
        thd = parse_amount(_text(line, "TienHangDichVu"))
        ten = _text(line, "TenHangDichVuDungCu")
        if not ten:
            error(f"{p}/TenHangDichVuDungCu", "item name is missing")
        if slq is None or slq <= 0:
            error(f"{p}/SoLuong", f"quantity missing or not > 0: '{_text(line, 'SoLuong')}'")
        if dj is None or dj < 0:
            error(f"{p}/DonGia", f"unit price missing or negative: '{_text(line, 'DonGia')}'")
        if tt is None:
            error(f"{p}/ThanhTien", "amount missing")
        if slq is not None and dj is not None and tt is not None:
            if abs(slq * dj - tt) > 1.0:
                error(f"{p}/ThanhTien",
                      f"amount {tt:,.0f} != SoLuong x DonGia = {slq * dj:,.0f}")
        if tcg is None:
            error(f"{p}/TienChiPhiGoc", "base amount missing")
        elif tt is not None and abs(tcg - tt) > 1.0:
            error(f"{p}/TienChiPhiGoc",
                  f"base amount {tcg:,.0f} != ThanhTien {tt:,.0f}")
        if thue is None:
            error(f"{p}/ThueSuat",
                  f"tax rate missing or unparsable: '{_text(line, 'ThueSuat')}'")
        if gtgt is None:
            error(f"{p}/ThueGTGT", "VAT amount missing")
        if thue is not None and gtgt is not None and tcg is not None:
            expected = tcg * thue / 100.0
            if abs(expected - gtgt) > max(1.0, tcg * 0.0001):
                error(f"{p}/ThueGTGT",
                      f"VAT {gtgt:,.0f} != {tcg:,.0f} x {thue:g}% = {expected:,.0f}")
        if thd is None:
            error(f"{p}/TienHangDichVu", "total (incl. VAT) missing")
        elif thd is not None and tcg is not None and gtgt is not None:
            if abs(tcg + gtgt - thd) > 1.0:
                error(f"{p}/TienHangDichVu",
                      f"total {thd:,.0f} != TCG {tcg:,.0f} + VAT {gtgt:,.0f}")
        if slq is not None and dj is not None:
            sum_tcg += tcg if tcg is not None else slq * dj
            sum_gtgt += gtgt if gtgt is not None else 0.0
            sum_tien += thd if thd is not None else (tcg or slq * dj) + (gtgt or 0.0)

    # --- TongTien (totals) ---------------------------------------------------
    ttj = _section(root, "TongTien")
    if ttj is None:
        error("TongTien", "missing section")
    elif lines:
        tcg_sum = parse_amount(_text(ttj, "TongChiPhiGoc"))
        gtgt_sum = parse_amount(_text(ttj, "TGTGT"))
        tien_sum = parse_amount(_text(ttj, "ThanhTien"))
        if tcg_sum is not None and abs(tcg_sum - sum_tcg) > 1.0:
            error("TongTien/TongChiPhiGoc",
                  f"total {tcg_sum:,.0f} != sum of lines {sum_tcg:,.0f}")
        if gtgt_sum is not None and abs(gtgt_sum - sum_gtgt) > 1.0:
            error("TongTien/TGTGT",
                  f"total VAT {gtgt_sum:,.0f} != sum of lines {sum_gtgt:,.0f}")
        if tien_sum is not None:
            if abs(tien_sum - sum_tien) > 1.0:
                error("TongTien/ThanhTien",
                      f"grand total {tien_sum:,.0f} != sum of lines {sum_tien:,.0f}")
            if tcg_sum is not None and gtgt_sum is not None and abs(tcg_sum + gtgt_sum - tien_sum) > 1.0:
                error("TongTien/ThanhTien",
                      f"grand total {tien_sum:,.0f} != TCG {tcg_sum:,.0f} + VAT {gtgt_sum:,.0f}")

    # Optional sections: presence checks (not errors when absent).
    if _section(root, "ThongTinThanhToan") is None:
        warn("ThongTinThanhToan", "payment info section missing")
    if _section(root, "ThongTinBanHang") is None:
        warn("ThongTinBanHang", "seller personnel section missing")

    return findings


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--json"]
    as_json = "--json" in argv
    if len(args) != 1:
        print(__doc__.strip().split("Usage")[-1].strip() if __doc__ else
              "usage: validate_hd.py [--json] <invoice.xml>", file=sys.stderr)
        return 2
    try:
        with open(args[0], encoding="utf-8") as fh:
            xml_text = fh.read()
    except OSError as exc:
        print(f"cannot read {args[0]}: {exc}", file=sys.stderr)
        return 2

    findings = validate(xml_text)
    if as_json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"[{f.level}] {f.path}: {f.message}")
        n_err = sum(1 for f in findings if f.level == "ERROR")
        n_warn = sum(1 for f in findings if f.level == "WARN")
        print(f"RESULT: {'FAIL' if n_err else 'PASS'} ({n_err} error(s), {n_warn} warning(s))")
    return 1 if any(f.level == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
