# -*- coding: utf-8 -*-
"""Plano 0 — Configuración fiscal (F6) y Plano 2b — Tesorería (F7).

Reutiliza la localización destino (l10n_*): busca el impuesto/diario que ya
existe y solo crea lo que falte. Cobros/pagos se importan **sueltos** por
defecto; la conciliación es opcional (perfil → options.reconcile)."""
from .base import _stats

# CODCFG → selector de IVA de línea (0=IVA1,1=IVA2,2=IVA3,3=Exento).
_CFG_SELECTOR = {"IVA1": "0", "IVA2": "1", "IVA3": "2"}


class ConfigMixin:
    """F6 — Configuración fiscal."""

    def do_company(self, source, reader, entity, line):
        if not reader.has_table("F_EMP"):
            return _stats()
        rows = reader.read_all("F_EMP")
        if not rows:
            return _stats()
        if self.dry_run:
            return _stats(1, 1, 0)
        r = rows[0]
        company = self.company
        vals = {}
        if not company.street and self.s(r, "DOMEMP"):
            vals["street"] = self.s(r, "DOMEMP")
        if not company.city and self.s(r, "POBEMP"):
            vals["city"] = self.s(r, "POBEMP")
        if not company.zip and self.s(r, "CPOEMP"):
            vals["zip"] = self.s(r, "CPOEMP")
        if vals:
            company.write(vals)
        return _stats(1, 1, 0)

    def do_taxes(self, source, reader, entity, line):
        if not reader.has_table("F_CFG"):
            return _stats()
        TaxMap = self.env["factusol.tax.map"]
        n = ok = 0
        for row in reader.iter_rows("F_CFG"):
            code = self.s(row, "CODCFG").upper()
            sel = _CFG_SELECTOR.get(code)
            if sel is None:
                continue
            n += 1
            pct = self.fl(row, "NUMCFG")
            if self.dry_run:
                ok += 1
                continue
            for tax_type in ("sale", "purchase"):
                tax = self.env["account.tax"].search([
                    ("company_id", "=", self.company.id),
                    ("type_tax_use", "=", tax_type),
                    ("amount_type", "=", "percent"),
                    ("amount", "=", pct),
                ], limit=1)
                if not tax:
                    tax = self.upsert("account.tax",
                                      self.dim_xmlid("cfgtax", "%s_%s" % (tax_type, sel)),
                                      {"name": "IVA %s%% (%s)" % (pct, tax_type),
                                       "amount": pct, "amount_type": "percent",
                                       "type_tax_use": tax_type, "company_id": self.company.id})
                existing = TaxMap.search([
                    ("company_id", "=", self.company.id),
                    ("factusol_selector", "=", sel), ("tax_type", "=", tax_type)], limit=1)
                tm_vals = {"company_id": self.company.id, "factusol_selector": sel,
                           "tax_type": tax_type, "origin_percent": pct, "tax_id": tax.id}
                if existing:
                    existing.write(tm_vals)
                else:
                    TaxMap.create(tm_vals)
            ok += 1
        return _stats(n, ok, 0)

    def do_payment_terms(self, source, reader, entity, line):
        if not reader.has_table("F_FPA"):
            return _stats()
        n = ok = fail = 0
        for row in reader.iter_rows("F_FPA"):
            code = self.s(row, "CODFPA")
            if not code:
                continue
            n += 1
            if self.dry_run:
                ok += 1
                continue
            try:
                self.upsert("account.payment.term", self.dim_xmlid("fpa", code), {
                    "name": "FactuSol FPA %s" % code,
                    "line_ids": [(0, 0, {"value": "percent", "value_amount": 100.0,
                                         "nb_days": 0})],
                })
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("warning", "payment_terms", code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)

    def do_banks(self, source, reader, entity, line):
        if not reader.has_table("F_BAN"):
            return _stats()
        n = ok = fail = 0
        for row in reader.iter_rows("F_BAN"):
            code = self.s(row, "CODBAN")
            if not code:
                continue
            n += 1
            if self.dry_run:
                ok += 1
                continue
            try:
                self.upsert("account.journal", self.dim_xmlid("ban", code), {
                    "name": self.s(row, "NOMBAN") or ("Banco %s" % code),
                    "type": "bank", "code": ("B%s" % code)[:5],
                    "company_id": self.company.id,
                })
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("warning", "banks", code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)


class TreasuryMixin:
    """F7 — Tesorería (cobros, pagos, anticipos)."""

    def _payment_journal(self):
        if not hasattr(self, "_pj"):
            self._pj = self.env["account.journal"].search(
                [("type", "in", ("bank", "cash")), ("company_id", "=", self.company.id)],
                limit=1)
        return self._pj

    def _make_payment(self, xmlid, ptype, partner_type, partner, amount, date, journal, memo):
        vals = {
            "payment_type": ptype, "partner_type": partner_type,
            "partner_id": partner.id, "amount": abs(amount),
            "date": date or False, "journal_id": journal.id,
            "memo": memo, "company_id": self.company.id,
        }
        pay = self.upsert("account.payment", xmlid, vals, only_if_absent=True)
        try:
            if pay and pay.state == "draft":
                pay.action_post()
        except Exception:  # noqa: BLE001
            pass
        return pay

    def _reconcile(self, payment, invoice):
        try:
            lines = (payment.move_id.line_ids + invoice.line_ids).filtered(
                lambda l: l.account_id.reconcile and not l.reconciled)
            lines.filtered(lambda l: l.account_id.account_type in
                           ("asset_receivable", "liability_payable")).reconcile()
        except Exception:  # noqa: BLE001
            pass

    def do_collection(self, source, reader, entity, line):
        journal = self._payment_journal()
        if not journal:
            self.log("warning", "collection", "", "Sin diario de banco/caja: cobros omitidos",
                     year=source.fiscal_year)
            return _stats()
        if not reader.has_table("F_LCO"):
            return _stats()
        opts = (line.options if line else None) or {}
        reconcile = bool(opts.get("reconcile"))
        year = source.fiscal_year
        n = ok = fail = skip = 0
        for row in reader.iter_rows("F_LCO"):
            n += 1
            tfa, cfa = self.s(row, "TFALCO"), self.it(row, "CFALCO")
            lin, amount = self.it(row, "LINLCO"), self.fl(row, "IMPLCO")
            if not cfa or not amount:
                skip += 1
                continue
            inv = self.ref(self.fact_xmlid("fac", year, tfa, cfa))
            if not inv:
                self.log("warning", "collection", "%s-%s" % (tfa, cfa),
                         "Factura no migrada; cobro omitido", year=year)
                skip += 1
                continue
            if self.dry_run:
                ok += 1
                continue
            try:
                pay = self._make_payment(
                    self.dim_xmlid("cob", "%s_%s_%s_%s" % (year, tfa, cfa, lin)),
                    "inbound", "customer", inv.partner_id, amount,
                    self.dt(row, "FECLCO"), journal, "LCO:%s-%s-%s" % (tfa, cfa, lin))
                if reconcile and pay and inv.state == "posted":
                    self._reconcile(pay, inv)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "collection", "%s-%s" % (tfa, cfa), str(exc), year=year)
                fail += 1
        return _stats(n, ok, fail, skip)

    def do_payment(self, source, reader, entity, line):
        journal = self._payment_journal()
        if not journal or not reader.has_table("F_PAG"):
            if not journal:
                self.log("warning", "payment", "", "Sin diario de banco/caja: pagos omitidos",
                         year=source.fiscal_year)
            return _stats()
        year = source.fiscal_year
        n = ok = fail = 0
        for row in reader.iter_rows("F_PAG"):
            n += 1
            code = self.s(row, "CODPAG")
            partner = self.partner_ref("supplier", self.s(row, "PROPAG"))
            amount = self.fl(row, "IMPPAG")
            if not partner or not amount:
                self.log("warning", "payment", code, "Falta proveedor o importe", year=year)
                fail += 1
                continue
            if self.dry_run:
                ok += 1
                continue
            try:
                self._make_payment(self.dim_xmlid("pag", "%s_%s" % (year, code)),
                                   "outbound", "supplier", partner, amount,
                                   self.dt(row, "FEMPAG"), journal, "PAG:%s" % code)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "payment", code, str(exc), year=year)
                fail += 1
        return _stats(n, ok, fail)

    def _do_advance(self, source, reader, table, code_field, partner_field, amount_field,
                    date_field, ptype, partner_type, partner_kind, prefix):
        journal = self._payment_journal()
        if not journal or not reader.has_table(table):
            return _stats()
        year = source.fiscal_year
        n = ok = fail = 0
        for row in reader.iter_rows(table):
            n += 1
            code = self.s(row, code_field)
            partner = self.partner_ref(partner_kind, self.s(row, partner_field))
            amount = self.fl(row, amount_field)
            if not partner or not amount:
                self.log("warning", prefix, code, "Falta tercero o importe", year=year)
                fail += 1
                continue
            if self.dry_run:
                ok += 1
                continue
            try:
                self._make_payment(self.dim_xmlid(prefix, "%s_%s" % (year, code)),
                                   ptype, partner_type, partner, amount,
                                   self.dt(row, date_field) if date_field else False,
                                   journal, "%s:%s" % (prefix.upper(), code))
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", prefix, code, str(exc), year=year)
                fail += 1
        return _stats(n, ok, fail)

    def do_customer_advance(self, source, reader, entity, line):
        return self._do_advance(source, reader, "F_ANT", "CODANT", "CLIANT", "IMPANT",
                                "FECANT", "inbound", "customer", "customer", "ant")

    def do_supplier_advance(self, source, reader, entity, line):
        return self._do_advance(source, reader, "F_ANP", "CODANP", "PROANP", "IMPANP",
                                None, "outbound", "supplier", "supplier", "anp")
