# -*- coding: utf-8 -*-
"""Datasets sintéticos en memoria (no datos reales de cliente). Dos ejercicios
(2025 y 2026) para probar multi-año. Se cargan vía ``AccessReader.from_dict``."""

from ..tools import AccessReader


def _dataset(year, customer_name):
    return {
        "F_SEC": [{"CODSEC": "01"}],
        "F_FAM": [{"CODFAM": "001", "DESFAM": "Familia A", "SECFAM": "01"}],
        "F_CLI": [
            {"CODCLI": "000001", "NOFCLI": customer_name, "NIFCLI": "20111111119",
             "DOMCLI": "Calle 1", "POBCLI": "Córdoba", "CPOCLI": "5000", "PROCLI": "Córdoba"},
            {"CODCLI": "000002", "NOFCLI": "Cliente Dos", "NIFCLI": "",
             "DOMCLI": "Calle 2", "POBCLI": "Rosario", "CPOCLI": "2000", "PROCLI": "Santa Fe"},
        ],
        "F_ART": [
            {"CODART": "A", "DESART": "Articulo A", "PCOART": "100,50",
             "FAMART": "001", "EANART": "7790000000017"},
            {"CODART": "B", "DESART": "Articulo B", "PCOART": "200",
             "FAMART": "001", "EANART": ""},
        ],
        # Presupuesto 1-000001 con dos líneas en orden POS invertido (2, 1).
        "F_PRE": [{"TIPPRE": "1", "CODPRE": 1, "CLIPRE": "000001",
                   "FECPRE": "%s-03-15" % year, "TOTPRE": "1.234,56"}],
        "F_LPS": [
            {"TIPLPS": "1", "CODLPS": 1, "POSLPS": 2, "ARTLPS": "B", "CANLPS": "2",
             "PRELPS": "200", "DT1LPS": "10", "DT2LPS": "0", "DT3LPS": "0",
             "IVALPS": "0", "CE1LPS": "", "CE2LPS": ""},
            {"TIPLPS": "1", "CODLPS": 1, "POSLPS": 1, "ARTLPS": "A", "CANLPS": "3",
             "PRELPS": "100", "DT1LPS": "10", "DT2LPS": "10", "DT3LPS": "0",
             "IVALPS": "0", "CE1LPS": "", "CE2LPS": ""},
        ],
    }


def reader_2026():
    return AccessReader.from_dict(_dataset(2026, "Cliente Uno"))


def reader_2025():
    return AccessReader.from_dict(_dataset(2025, "Cliente Uno (viejo)"))
