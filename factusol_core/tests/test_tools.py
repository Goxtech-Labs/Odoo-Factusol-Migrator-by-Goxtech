# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo.addons.factusol_core.tools import (
    combine_discounts,
    dimension_xmlid,
    fact_xmlid,
    format_doc_ref,
    price_from_margin,
)


class TestFactusolTools(TransactionCase):
    """Pure helper functions (no DB needed, run under the Odoo test runner)."""

    # -- Referencia TIPO-TIP-COD con distintos anchos de máscara --------------
    def test_format_doc_ref_default_width(self):
        self.assertEqual(format_doc_ref("FAC", "1", 1), "FAC-1-000001")
        self.assertEqual(format_doc_ref("fre", "2", 345), "FRE-2-000345")

    def test_format_doc_ref_custom_width(self):
        self.assertEqual(format_doc_ref("ALB", "1", 7, 5), "ALB-1-00007")
        self.assertEqual(format_doc_ref("PRE", "A", 12, 4), "PRE-A-0012")

    # -- Triple descuento: combinación y equivalencia con descuento único -----
    def test_single_discount_is_preserved(self):
        self.assertAlmostEqual(combine_discounts(10, 0, 0), 10.0)
        self.assertAlmostEqual(combine_discounts(0, 0, 0), 0.0)

    def test_triple_discount_cascade(self):
        # 10% + 10% -> 19% ; 10%+10%+10% -> 27.1%
        self.assertAlmostEqual(combine_discounts(10, 10, 0), 19.0)
        self.assertAlmostEqual(combine_discounts(10, 10, 10), 27.1)

    # -- Precio por margen ----------------------------------------------------
    def test_price_from_margin_over_cost(self):
        self.assertAlmostEqual(price_from_margin(100, 25), 125.0)
        self.assertAlmostEqual(price_from_margin(100, 0), 100.0)

    def test_price_from_margin_over_price(self):
        self.assertAlmostEqual(price_from_margin(100, 20, "price"), 125.0)
        self.assertAlmostEqual(price_from_margin(80, 20, "price"), 100.0)

    # -- External IDs (convención multi-año) ----------------------------------
    def test_dimension_xmlid_has_no_year(self):
        self.assertEqual(dimension_xmlid("cli", "000123"), "cli_000123")

    def test_fact_xmlid_has_year(self):
        self.assertEqual(fact_xmlid("fac", 2026, "1", 1), "fac_2026_1-000001")
        self.assertEqual(fact_xmlid("fre", 2025, "1", 1), "fre_2025_1-000001")
