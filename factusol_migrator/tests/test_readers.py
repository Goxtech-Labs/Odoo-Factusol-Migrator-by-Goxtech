# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from ..tools import AccessReader, parse_company_year


class TestReaders(TransactionCase):

    def test_dict_backend_interface(self):
        reader = AccessReader.from_dict({
            "F_CLI": [{"CODCLI": "1", "NOFCLI": "A"}, {"CODCLI": "2", "NOFCLI": "B"}],
        })
        self.assertEqual(reader.list_tables(), ["F_CLI"])
        self.assertTrue(reader.has_table("F_CLI"))
        self.assertFalse(reader.has_table("F_NOPE"))
        self.assertEqual(set(reader.field_names("F_CLI")), {"CODCLI", "NOFCLI"})
        rows = reader.read_all("F_CLI")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["NOFCLI"], "A")
        self.assertEqual(reader.count("F_CLI"), 2)
        # columnas filtradas
        only = reader.read_all("F_CLI", columns=["CODCLI"])
        self.assertEqual(only[0], {"CODCLI": "1"})

    def test_parse_company_year(self):
        self.assertEqual(parse_company_year("0022026.accdb"), ("002", 2026))
        self.assertEqual(parse_company_year("0012024.accdb"), ("001", 2024))
        # sin patrón EEEAAAA: extrae el año si está.
        company, year = parse_company_year("empresa_2023.accdb")
        self.assertEqual(year, 2023)

    def test_available_backends_is_list(self):
        self.assertIsInstance(AccessReader.available_backends(), list)
