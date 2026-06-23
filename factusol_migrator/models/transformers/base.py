# -*- coding: utf-8 -*-
"""Infraestructura compartida por los transformadores (upsert idempotente,
conversión, logging, resolución de FK por External ID)."""
import logging

from odoo.addons.factusol_core.tools import (
    combine_discounts,
    dimension_xmlid,
    fact_xmlid,
    format_doc_ref,
    price_from_margin,
)

from ...tools import convert

_logger = logging.getLogger(__name__)


def _stats(source=0, ok=0, failed=0, skipped=0, amount_src=None, amount_odoo=None):
    out = {"source": source, "ok": ok, "failed": failed, "skipped": skipped}
    if amount_src is not None:
        out["amount_src"] = amount_src
        out["amount_odoo"] = amount_odoo or 0.0
    return out


class BaseEngine:
    """Servicios base; los mixins de cada plano aportan los ``do_*``."""

    MODULE = "__factusol__"

    def __init__(self, env, run, dry_run=False):
        self.env = env
        self.run = run
        self.dry_run = dry_run
        self.company = run.company_id
        self._tax_cache = {}

    # -- Conversión ----------------------------------------------------------
    @staticmethod
    def cv(value, transform="str"):
        if transform == "float":
            return convert.to_float(value)
        if transform == "int":
            return convert.to_int(value)
        if transform == "date":
            return convert.to_date(value)
        if transform == "vat":
            return convert.norm_vat(value)
        if transform == "selector":
            return convert.to_selector(value)
        return convert.clean_str(value)

    @staticmethod
    def s(row, field):
        return convert.clean_str(row.get(field))

    @staticmethod
    def fl(row, field):
        return convert.to_float(row.get(field))

    @staticmethod
    def it(row, field):
        return convert.to_int(row.get(field))

    @staticmethod
    def dt(row, field):
        return convert.to_date(row.get(field))

    # -- Helpers de FactuSol (re-exportados de factusol_core) ----------------
    format_doc_ref = staticmethod(format_doc_ref)
    combine_discounts = staticmethod(combine_discounts)
    price_from_margin = staticmethod(price_from_margin)
    dim_xmlid = staticmethod(dimension_xmlid)
    fact_xmlid = staticmethod(fact_xmlid)

    # -- Idempotencia (ir.model.data) ----------------------------------------
    def ref(self, xmlid):
        return self.env.ref("%s.%s" % (self.MODULE, xmlid), raise_if_not_found=False)

    def upsert(self, model, xmlid, vals, only_if_absent=False):
        """Crea/actualiza un registro ligado a un External ID determinista.

        En *dry-run* no escribe: devuelve el registro existente (para resolver
        FK ya migradas) o ``None``.
        """
        rec = self.ref(xmlid)
        if self.dry_run:
            return rec
        if rec:
            if not only_if_absent and vals:
                rec.write(vals)
            return rec
        rec = self.env[model].with_context(
            tracking_disable=True, mail_create_nolog=True, mail_notrack=True,
        ).create(vals)
        self.env["ir.model.data"].create({
            "module": self.MODULE, "name": xmlid, "model": model,
            "res_id": rec.id, "noupdate": True,
        })
        return rec

    # -- Logging -------------------------------------------------------------
    def log(self, level, entity, key, message, field=None, payload=None, year=None):
        self.env["factusol.import.log"].create({
            "run_id": self.run.id, "entity": entity, "key": str(key or ""),
            "field": field, "level": level, "message": message,
            "payload": payload, "fiscal_year": year,
        })

    def stage(self, source, entity, table, key, data, line_no=0, state="pending"):
        """Guarda una muestra cruda en staging (auditoría / preview)."""
        self.env["factusol.staging.row"].create({
            "run_id": self.run.id, "entity": entity, "table": table,
            "plane": None, "fiscal_year": source.fiscal_year, "key": str(key or ""),
            "line_no": line_no, "data": data, "state": state,
        })

    # -- Resolución de impuestos (selector → account.tax) --------------------
    def resolve_tax(self, selector, tax_type="sale"):
        cache_key = (selector, tax_type)
        if cache_key not in self._tax_cache:
            self._tax_cache[cache_key] = self.env["factusol.tax.map"].resolve_tax(
                selector, tax_type, self.company
            )
        return self._tax_cache[cache_key]

    # -- Resolución de dimensiones por código --------------------------------
    def partner_ref(self, kind, code):
        prefix = "cli" if kind == "customer" else "pro"
        return self.ref(self.dim_xmlid(prefix, code))

    def product_tmpl_ref(self, code):
        return self.ref(self.dim_xmlid("art", code))

    def category_ref(self, code):
        return self.ref(self.dim_xmlid("fam", code))

    def warehouse_ref(self, code):
        return self.ref(self.dim_xmlid("alm", code))

    def variant_ref(self, art_code, ce1, ce2):
        """Variante por artículo+talla+color (External ID determinista)."""
        token = "%s_%s_%s" % (art_code, ce1 or "0", ce2 or "0")
        return self.ref(self.dim_xmlid("var", token))
