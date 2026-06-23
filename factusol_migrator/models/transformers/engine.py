# -*- coding: utf-8 -*-
"""Motor de migración: combina los mixins de cada plano y despacha por entidad."""
from .base import BaseEngine, _stats
from .config_treasury import ConfigMixin, TreasuryMixin
from .dimensions import DimensionMixin
from .documents import DocumentMixin

_DISPATCH = {
    # Plano 0 — Configuración
    "company": "do_company", "taxes": "do_taxes",
    "payment_terms": "do_payment_terms", "banks": "do_banks",
    # Plano 1 — Dimensiones
    "warehouse": "do_warehouse", "section": "do_section", "family": "do_family",
    "customer": "do_customer", "supplier": "do_supplier", "product": "do_product",
    "variant": "do_variant", "pricelist": "do_pricelist", "stock": "do_stock",
    # Plano 2b — Tesorería
    "collection": "do_collection", "payment": "do_payment",
    "customer_advance": "do_customer_advance", "supplier_advance": "do_supplier_advance",
}


class MigrationEngine(BaseEngine, ConfigMixin, DimensionMixin, DocumentMixin, TreasuryMixin):
    """Punto de entrada usado por ``factusol.import.run``."""

    def run_entity(self, source, reader, entity, line):
        # Todos los hechos comerciales (plano 2) van al transformador genérico.
        if entity["plane"] == "2":
            return self.do_document(source, reader, entity, line)
        method_name = _DISPATCH.get(entity["code"])
        method = getattr(self, method_name, None) if method_name else None
        if not method:
            return _stats()
        return method(source, reader, entity, line)
