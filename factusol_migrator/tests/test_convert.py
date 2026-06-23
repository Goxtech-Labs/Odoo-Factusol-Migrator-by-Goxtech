# -*- coding: utf-8 -*-
import datetime

from odoo.tests.common import TransactionCase

from ..tools import convert


class TestConvert(TransactionCase):

    def test_decimals_spanish(self):
        self.assertAlmostEqual(convert.to_float("1.234,56"), 1234.56)
        self.assertAlmostEqual(convert.to_float("100,50"), 100.5)
        self.assertAlmostEqual(convert.to_float("200"), 200.0)
        self.assertAlmostEqual(convert.to_float(""), 0.0)
        self.assertAlmostEqual(convert.to_float(None), 0.0)

    def test_dates(self):
        self.assertEqual(convert.to_date("2026-03-15"), datetime.date(2026, 3, 15))
        self.assertEqual(convert.to_date("15/03/2026"), datetime.date(2026, 3, 15))
        self.assertFalse(convert.to_date("00/00/0000"))
        self.assertFalse(convert.to_date("01/01/1900"))
        self.assertFalse(convert.to_date(None))

    def test_vat_and_strings(self):
        self.assertEqual(convert.norm_vat("  20-111.111 "), "20111111")
        self.assertFalse(convert.norm_vat("   "))
        self.assertEqual(convert.clean_str("  hola  "), "hola")

    def test_selector(self):
        self.assertEqual(convert.to_selector("0"), 0)
        self.assertEqual(convert.to_selector("3"), 3)
        self.assertEqual(convert.to_selector(None), 0)
