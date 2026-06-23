# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from ..tools import schema


class TestSchema(TransactionCase):

    def test_header_and_line_derivation(self):
        h = schema.header_field_map("F_FAC")
        self.assertEqual(h["tip"], "TIPFAC")
        self.assertEqual(h["cod"], "CODFAC")
        self.assertEqual(h["tot"], "TOTFAC")
        ln = schema.line_field_map("F_LFA")
        self.assertEqual(ln["pos"], "POSLFA")
        self.assertEqual(ln["art"], "ARTLFA")
        self.assertEqual(ln["d1"], "DT1LFA")
        self.assertEqual(ln["iva"], "IVALFA")

    def test_entities(self):
        self.assertEqual(schema.entity_by_code("customer")["table"], "F_CLI")
        self.assertEqual(schema.document_by_code("customer_invoice")["move_type"], "out_invoice")
        self.assertEqual(schema.document_by_code("vendor_bill")["move_type"], "in_invoice")
        self.assertTrue(schema.entity_by_code("stock").get("last_year_only"))

    def test_seven_documents(self):
        self.assertEqual(len(schema.documents()), 7)
        prefixes = {d["prefix"] for d in schema.documents()}
        self.assertEqual(prefixes, set(schema.DOC_PREFIXES))
