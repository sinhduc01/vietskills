"""Tests for validate_hd.py — run with:  python test_validate_hd.py"""

import copy
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_hd as vh  # noqa: E402

VALID_XML = """<?xml version="1.0" encoding="UTF-8"?>
<DonHieu TenDN="CONG TY CO PHAN THUONG MAI ABC" MaTKT="1.0" NDKH="1234">
  <ThongTinChung>
    <TenCoSo>CONG TY CO PHAN THUONG MAI ABC</TenCoSo>
    <MSTCoSo>0101234567</MSTCoSo>
    <DiaChiCS>123 Nguyen Huu Tho, Hai Ba Trung, Hanoi</DiaChiCS>
    <STKH>1C25MA</STKH>
    <NHD>2026</NHD>
  </ThongTinChung>
  <ThongTinHoaDon>
    <STTHD>000123</STTHD>
    <NgHD>05/11/2026</NgHD>
    <NCC>2</NCC>
    <NDKH>1234</NDKH>
    <HDTT>HD GTGT</HDTT>
    <KHCN></KHCN>
    <STKH>1C26MA</STKH>
    <NHD>2026</NHD>
  </ThongTinHoaDon>
  <ChiTietHD>
    <STT>1</STT>
    <TenHangDichVuDungCu>Phien dich vu phat trien phan mem</TenHangDichVuDungCu>
    <MaMatHang>7020</MaMatHang>
    <DonViTinh>Dich vu</DonViTinh>
    <SoLuong>1</SoLuong>
    <DonGia>5000000</DonGia>
    <ThanhTien>5000000</ThanhTien>
    <ThueSuat>10</ThueSuat>
    <TienChiPhiGoc>5000000</TienChiPhiGoc>
    <ThueGTGT>500000</ThueGTGT>
    <TienHangDichVu>5500000</TienHangDichVu>
  </ChiTietHD>
  <ChiTietHD>
    <STT>2</STT>
    <TenHangDichVuDungCu>Thue may chieu</TenHangDichVuDungCu>
    <DonViTinh>Cay</DonViTinh>
    <SoLuong>2</SoLuong>
    <DonGia>1000000</DonGia>
    <ThanhTien>2000000</ThanhTien>
    <ThueSuat>KH</ThueSuat>
    <TienChiPhiGoc>2000000</TienChiPhiGoc>
    <ThueGTGT>0</ThueGTGT>
    <TienHangDichVu>2000000</TienHangDichVu>
  </ChiTietHD>
  <TongTien>
    <TongChiPhiGoc>7000000</TongChiPhiGoc>
    <TGTGT>500000</TGTGT>
    <ThanhTien>7500000</ThanhTien>
    <ThueGTGT>500000</ThueGTGT>
  </TongTien>
  <ThongTinThanhToan>
    <TTT>2</TTT>
  </ThongTinThanhToan>
  <ChuKyDienTu>
    <ChuKy>aW52YWxpZC1zaWduYXR1cmU=</ChuKy>
  </ChuKyDienTu>
  <ThongTinBanHang>
    <TenNhanBanHang>Nguyen Van A</TenNhanBanHang>
    <TenNhanKiemTra>Tran Thi B</TenNhanKiemTra>
    <TenNhanNhap>Le Van C</TenNhanNhap>
  </ThongTinBanHang>
</DonHieu>
"""


def errors(findings):
    return [f for f in findings if f.level == "ERROR"]




class TestAmountParsing(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(vh.parse_amount("1234567"), 1234567.0)

    def test_dot_thousands(self):
        self.assertEqual(vh.parse_amount("1.234.567"), 1234567.0)

    def test_comma_decimal(self):
        self.assertEqual(vh.parse_amount("1234,56"), 1234.56)

    def test_mixed_vn(self):
        self.assertEqual(vh.parse_amount("1.234.567,89"), 1234567.89)

    def test_dot_decimal(self):
        self.assertEqual(vh.parse_amount("1234.56"), 1234.56)

    def test_comma_thousands(self):
        self.assertEqual(vh.parse_amount("1,234,567"), 1234567.0)

    def test_garbage(self):
        self.assertIsNone(vh.parse_amount("abc"))
        self.assertIsNone(vh.parse_amount(""))


class TestRateParsing(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(vh.parse_rate("10"), 10.0)

    def test_percent(self):
        self.assertEqual(vh.parse_rate("8%"), 8.0)

    def test_exempt(self):
        self.assertEqual(vh.parse_rate("KH"), 0.0)

    def test_zero(self):
        self.assertEqual(vh.parse_rate("0%"), 0.0)


class TestValidator(unittest.TestCase):
    def test_valid_invoice_passes(self):
        findings = vh.validate(VALID_XML)
        self.assertEqual(errors(findings), [])

    def test_line_amount_mismatch(self):
        root = ET.fromstring(VALID_XML)
        root.find(".//ChiTietHD[1]/ThanhTien").text = "4000000"
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertTrue(any("ThanhTien" in f.message for f in errors(findings)))

    def test_vat_mismatch(self):
        root = ET.fromstring(VALID_XML)
        root.find(".//ChiTietHD[1]/ThueGTGT").text = "900000"
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertTrue(any("ThueGTGT" in f.path for f in errors(findings)))

    def test_grand_total_mismatch(self):
        root = ET.fromstring(VALID_XML)
        root.find(".//TongTien/ThanhTien").text = "7600000"
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertTrue(any("TongTien" in f.path for f in errors(findings)))

    def test_bad_date_format(self):
        root = ET.fromstring(VALID_XML)
        root.find(".//ThongTinHoaDon/NgHD").text = "2026/11/05"
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertTrue(any("NgHD" in f.path for f in errors(findings)))

    def test_missing_required_section(self):
        root = ET.fromstring(VALID_XML)
        ttj = root.find(".//TongTien")
        root.remove(ttj)
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertTrue(any("TongTien" in f.path for f in errors(findings)))

    def test_bad_mst_warns_not_errors(self):
        root = ET.fromstring(VALID_XML)
        root.find(".//ThongTinChung/MSTCoSo").text = "12345"
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertEqual(errors(findings), [])
        self.assertTrue(any("MSTCoSo" in f.path for f in findings if f.level == "WARN"))

    def test_correction_without_date_warns(self):
        root = ET.fromstring(VALID_XML)
        root.find(".//ThongTinHoaDon/KHCN").text = "Dieu chinh hoa don"
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertEqual(errors(findings), [])
        self.assertTrue(any("KHCN" in f.path for f in findings if f.level == "WARN"))

    def test_malformed_xml(self):
        findings = vh.validate("<DonHieu><ThongTinChung>")
        self.assertTrue(any("well-formed" in f.message for f in errors(findings)))

    def test_wrong_root(self):
        findings = vh.validate("<Invoice><a>1</a></Invoice>")
        self.assertTrue(any("DonHieu" in f.message for f in errors(findings)))

    def test_no_line_items(self):
        root = ET.fromstring(VALID_XML)
        for line in root.findall("ChiTietHD"):
            root.remove(line)
        findings = vh.validate(ET.tostring(root, encoding="unicode"))
        self.assertTrue(any("ChiTietHD" in f.path for f in errors(findings)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
