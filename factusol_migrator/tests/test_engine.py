# -*- coding: utf-8 -*-
import base64

from odoo.tests.common import TransactionCase

from ..models.transformers import MigrationEngine
from ..tools import schema
from . import fixtures


class TestEngine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        dummy = base64.b64encode(b"x")
        cls.src2026 = cls.env["factusol.source"].create({
            "accdb_file": dummy, "file_name": "0022026.accdb",
            "company_code": "002", "fiscal_year": 2026, "state": "ready"})
        cls.src2025 = cls.env["factusol.source"].create({
            "accdb_file": dummy, "file_name": "0022025.accdb",
            "company_code": "002", "fiscal_year": 2025, "state": "ready"})
        cls.imp_run = cls.env["factusol.import.run"].create({
            "company_id": cls.company.id,
            "source_ids": [(6, 0, [cls.src2025.id, cls.src2026.id])]})
        cls.empty_line = cls.env["factusol.import.profile.line"]

    def _engine(self, dry_run=False):
        # OJO: no usar self.run — pisa unittest.TestCase.run().
        return MigrationEngine(self.env, self.imp_run, dry_run=dry_run)

    def _load_dimensions(self, engine, source, reader):
        for code in ("section", "family", "customer", "product"):
            getattr(engine, "do_" + code)(
                source, reader, schema.entity_by_code(code), self.empty_line)

    # -- Dimensiones ---------------------------------------------------------
    def test_dimensions(self):
        engine = self._engine()
        self._load_dimensions(engine, self.src2026, fixtures.reader_2026())
        partner = self.env.ref("__factusol__.cli_000001", raise_if_not_found=False)
        self.assertTrue(partner)
        self.assertEqual(partner.name, "Cliente Uno")
        self.assertEqual(partner.x_factusol_code, "000001")
        self.assertGreaterEqual(partner.customer_rank, 1)
        prod_a = self.env.ref("__factusol__.art_A", raise_if_not_found=False)
        self.assertTrue(prod_a)
        self.assertAlmostEqual(prod_a.standard_price, 100.5, places=2)
        self.assertEqual(prod_a.categ_id, self.env.ref("__factusol__.fam_001"))

    # -- Idempotencia --------------------------------------------------------
    def test_idempotency(self):
        engine = self._engine()
        self._load_dimensions(engine, self.src2026, fixtures.reader_2026())
        n1 = self.env["res.partner"].search_count([("x_factusol_code", "=", "000001")])
        self._load_dimensions(engine, self.src2026, fixtures.reader_2026())
        n2 = self.env["res.partner"].search_count([("x_factusol_code", "=", "000001")])
        self.assertEqual(n1, n2)
        self.assertEqual(n2, 1)

    # -- Fusión multi-año (gana el más reciente) -----------------------------
    def test_multiyear_merge(self):
        engine = self._engine()
        self._load_dimensions(engine, self.src2025, fixtures.reader_2025())
        partner = self.env.ref("__factusol__.cli_000001")
        self.assertEqual(partner.name, "Cliente Uno (viejo)")
        self._load_dimensions(engine, self.src2026, fixtures.reader_2026())
        self.assertEqual(partner.name, "Cliente Uno")

    # -- Documento genérico: unión (TIP,COD), orden POS, triple descuento ----
    def test_document_quotation(self):
        engine = self._engine()
        reader = fixtures.reader_2026()
        self._load_dimensions(engine, self.src2026, reader)
        stats = engine.do_document(
            self.src2026, reader, schema.document_by_code("quotation"), self.empty_line)
        self.assertEqual(stats["source"], 1)
        self.assertEqual(stats["ok"], 1)

        order = self.env.ref("__factusol__.pre_2026_1-000001", raise_if_not_found=False)
        self.assertTrue(order)
        self.assertEqual(order.x_factusol_ref, "PRE-1-000001")
        self.assertEqual(len(order.order_line), 2)

        lines = order.order_line.sorted("sequence")
        prod_a = self.env.ref("__factusol__.art_A")
        self.assertEqual(lines[0].product_id, prod_a.product_variant_id)
        # Triple descuento combinado: 10%+10% = 19% ; 10% = 10%.
        self.assertAlmostEqual(lines[0].discount, 19.0, places=2)
        self.assertAlmostEqual(lines[1].discount, 10.0, places=2)

    # -- Idempotencia de documentos (no se duplican / no se re-postean) ------
    def test_document_idempotent(self):
        engine = self._engine()
        reader = fixtures.reader_2026()
        self._load_dimensions(engine, self.src2026, reader)
        engine.do_document(self.src2026, reader, schema.document_by_code("quotation"), self.empty_line)
        stats2 = engine.do_document(
            self.src2026, reader, schema.document_by_code("quotation"), self.empty_line)
        self.assertEqual(stats2["skipped"], 1)
        self.assertEqual(
            self.env["sale.order"].search_count([("x_factusol_ref", "=", "PRE-1-000001")]), 1)
