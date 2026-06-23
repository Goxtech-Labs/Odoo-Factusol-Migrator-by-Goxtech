# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestFactusolCompat(TransactionCase):
    """Model-level behaviour of the compatibility layer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # En una DB sin plan de cuentas, account.tax exige tax_group_id y
        # country_id (ambos NOT NULL) sin defaults: los proveemos en el test.
        cls.country = cls.env.ref("base.ar")
        cls.tax_group = cls.env["account.tax.group"].create(
            {"name": "Test FactuSol", "country_id": cls.country.id}
        )
        cls.tax_sale = cls.env["account.tax"].create(
            {
                "name": "IVA 21 (test)",
                "amount": 21.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
                "tax_group_id": cls.tax_group.id,
                "country_id": cls.country.id,
            }
        )

    # -- Helper mixin disponible para el migrador -----------------------------
    def test_helper_mixin_methods(self):
        helper = self.env["factusol.helper.mixin"]
        self.assertEqual(helper.fs_format_doc_ref("FAC", "1", 1), "FAC-1-000001")
        self.assertAlmostEqual(helper.fs_combine_discounts(10, 10, 10), 27.1)
        self.assertAlmostEqual(helper.fs_price_from_margin(100, 25), 125.0)
        self.assertEqual(helper.fs_dimension_xmlid("cli", "5"), "cli_5")

    # -- Traducción de IVA selector -> account.tax (tabla configurable) -------
    def test_tax_map_resolution(self):
        TaxMap = self.env["factusol.tax.map"]
        TaxMap.create(
            {
                "company_id": self.company.id,
                "factusol_selector": "0",
                "tax_type": "sale",
                "origin_percent": 21.0,
                "tax_id": self.tax_sale.id,
            }
        )
        # Resuelve por selector (acepta int o str)
        self.assertEqual(TaxMap.resolve_tax("0", "sale", self.company), self.tax_sale)
        self.assertEqual(TaxMap.resolve_tax(0, "sale", self.company), self.tax_sale)
        # Selector sin mapeo -> recordset vacío (el migrador decide el aviso)
        self.assertFalse(TaxMap.resolve_tax("3", "sale", self.company))

    def test_tax_map_unique_per_company_and_use(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger

        TaxMap = self.env["factusol.tax.map"]
        TaxMap.create(
            {
                "company_id": self.company.id,
                "factusol_selector": "1",
                "tax_type": "sale",
                "tax_id": self.tax_sale.id,
            }
        )
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            TaxMap.create(
                {
                    "company_id": self.company.id,
                    "factusol_selector": "1",
                    "tax_type": "sale",
                    "tax_id": self.tax_sale.id,
                }
            )
            self.env.flush_all()

    # -- Triple descuento volcado al discount nativo (onchange) ---------------
    def test_line_discount_onchange(self):
        line = self.env["sale.order.line"].new(
            {"x_disc1": 10.0, "x_disc2": 10.0, "x_disc3": 0.0}
        )
        line._onchange_factusol_discounts()
        self.assertAlmostEqual(line.discount, 19.0)

        single = self.env["account.move.line"].new({"x_disc1": 15.0})
        single._onchange_factusol_discounts()
        self.assertAlmostEqual(single.discount, 15.0)

    # -- Campos puente presentes en documentos y comisión simple --------------
    def test_document_bridge_fields(self):
        partner = self.env["res.partner"].create(
            {"name": "Cliente FactuSol", "x_factusol_code": "000123"}
        )
        self.assertEqual(partner.x_factusol_code, "000123")

        move = self.env["account.move"].new(
            {
                "move_type": "out_invoice",
                "x_factusol_ref": "FAC-1-000001",
                "x_factusol_serie": "1",
                "x_factusol_code": "000001",
                "x_factusol_year": 2026,
                "x_factusol_iva_regime": "0",
            }
        )
        self.assertEqual(move.x_factusol_ref, "FAC-1-000001")
        self.assertEqual(move.x_factusol_year, 2026)
        # La comisión no rompe el cálculo (sin líneas -> 0).
        self.assertEqual(move.x_factusol_commission_amount, 0.0)
