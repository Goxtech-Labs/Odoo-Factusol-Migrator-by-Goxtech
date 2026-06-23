# -*- coding: utf-8 -*-
"""Plano 2 — Hechos comerciales. Un solo transformador genérico para los 7
documentos (FAC/FRE/ALB/ENT/PPR/PCL/PRE): unión cabecera↔línea por ``(TIP,COD)``,
orden por ``POS``, número ``TIPO-TIP-COD`` e idempotencia con clave por año."""
import logging

from .base import _stats

_logger = logging.getLogger(__name__)


class DocumentMixin:

    def do_document(self, source, reader, entity, line):
        """Transformador genérico parametrizado por el catálogo del documento."""
        H, L = entity["header"], entity["line"]
        year = source.fiscal_year
        if not reader.has_table(entity["table"]):
            return _stats()

        # Líneas agrupadas por (TIP, COD) y ordenadas por POS.
        grouped = {}
        if reader.has_table(entity["line_table"]):
            for lr in reader.iter_rows(entity["line_table"]):
                k = (self.s(lr, L["tip"]), self.it(lr, L["cod"]))
                grouped.setdefault(k, []).append(lr)
        for k in grouped:
            grouped[k].sort(key=lambda r: self.it(r, L["pos"]))

        tax_type = "sale" if entity["partner_kind"] == "customer" else "purchase"
        track_amount = entity["kind"] in ("move", "sale_order", "purchase_order")
        n = ok = fail = skip = 0
        amount_src = amount_odoo = 0.0

        for row in reader.iter_rows(entity["table"]):
            n += 1
            tip = self.s(row, H["tip"])
            cod = self.it(row, H["cod"])
            key = "%s-%s" % (tip, cod)
            ref_legible = self.format_doc_ref(entity["prefix"], tip, cod)
            xmlid = self.fact_xmlid(entity["xmlid_prefix"], year, tip, cod)
            total = self.fl(row, H["tot"])
            amount_src += total

            partner = self.partner_ref(entity["partner_kind"], self.s(row, entity["partner_field"]))
            if not partner:
                self.log("error", entity["code"], key,
                         "No se migró %s: falta su %s en FactuSol." % (
                             ref_legible, "cliente" if tax_type == "sale" else "proveedor"),
                         year=year)
                fail += 1
                continue

            # Idempotencia: si ya existe, no se reescribe (no re-postea facturas).
            existing = self.ref(xmlid)
            if existing:
                skip += 1
                if track_amount and hasattr(existing, "amount_total"):
                    amount_odoo += existing.amount_total
                continue

            specs, missing = self._line_specs(grouped.get((tip, cod), []), L, tax_type)
            for m in missing:
                self.log("warning", entity["code"], key,
                         "Línea sin artículo en Odoo (%s)" % m, year=year)

            if self.dry_run:
                ok += 1
                continue

            try:
                rec = self._create_document(entity, row, partner, ref_legible, xmlid,
                                            year, tip, cod, specs)
                ok += 1
                if track_amount and rec and hasattr(rec, "amount_total"):
                    amount_odoo += rec.amount_total
            except Exception as exc:  # noqa: BLE001
                _logger.exception("FactuSol document %s %s failed", entity["code"], key)
                self.log("error", entity["code"], key, str(exc), year=year,
                         payload={"ref": ref_legible})
                fail += 1

        return _stats(n, ok, fail, skip,
                      amount_src if track_amount else None,
                      amount_odoo if track_amount else None)

    # -- Resolución de líneas ------------------------------------------------
    def _line_specs(self, line_rows, L, tax_type):
        specs, missing = [], []
        for lr in line_rows:
            art = self.s(lr, L["art"])
            ce1, ce2 = self.s(lr, L["ce1"]), self.s(lr, L["ce2"])
            if ce1 or ce2:
                product = self.variant_ref(art, ce1, ce2)
            else:
                tmpl = self.product_tmpl_ref(art)
                product = tmpl.product_variant_id if tmpl else None
            if not product:
                missing.append(art or "?")
                continue
            d1, d2, d3 = self.fl(lr, L["d1"]), self.fl(lr, L["d2"]), self.fl(lr, L["d3"])
            sel = self.cv(lr.get(L["iva"]), "selector")
            specs.append({
                "product": product,
                "pos": self.it(lr, L["pos"]),
                "qty": self.fl(lr, L["qty"]),
                "price": self.fl(lr, L["price"]),
                "discount": self.combine_discounts(d1, d2, d3),
                "d1": d1, "d2": d2, "d3": d3,
                "tax": self.resolve_tax(sel, tax_type),
            })
        return specs, missing

    # -- Creación por tipo de destino ----------------------------------------
    def _create_document(self, entity, row, partner, ref_legible, xmlid, year, tip, cod, specs):
        kind = entity["kind"]
        if kind == "move":
            return self._create_move(entity, row, partner, ref_legible, xmlid, year, tip, cod, specs)
        if kind in ("sale_order", "purchase_order"):
            return self._create_order(entity, row, partner, ref_legible, xmlid, year, tip, cod, specs)
        if kind == "picking":
            return self._create_picking(entity, row, partner, ref_legible, xmlid, specs)
        return None

    def _factusol_bridge(self, ref_legible, tip, cod, year, row, entity):
        return {
            "x_factusol_ref": ref_legible,
            "x_factusol_serie": tip,
            "x_factusol_code": str(cod),
            "x_factusol_year": year,
        }

    def _create_move(self, entity, row, partner, ref_legible, xmlid, year, tip, cod, specs):
        H = entity["header"]
        line_cmds = [(0, 0, {
            "product_id": sp["product"].id,
            "name": sp["product"].display_name,
            "sequence": sp["pos"],
            "quantity": sp["qty"],
            "price_unit": sp["price"],
            "discount": sp["discount"],
            "x_disc1": sp["d1"], "x_disc2": sp["d2"], "x_disc3": sp["d3"],
            "tax_ids": [(6, 0, sp["tax"].ids)] if sp["tax"] else False,
        }) for sp in specs]
        vals = {
            "move_type": entity["move_type"],
            "partner_id": partner.id,
            "invoice_date": self.dt(row, H["fec"]) or False,
            "date": self.dt(row, H["fec"]) or False,
            "ref": ref_legible,
            "company_id": self.company.id,
            "invoice_line_ids": line_cmds,
        }
        vals.update(self._factusol_bridge(ref_legible, tip, cod, year, row, entity))
        move = self.upsert("account.move", xmlid, vals, only_if_absent=True)
        # Intento de dejarlo en estado final (posteado); si falla, queda borrador.
        try:
            if move and move.state == "draft" and move.invoice_line_ids:
                move.action_post()
        except Exception as exc:  # noqa: BLE001
            self.log("warning", entity["code"], "%s-%s" % (tip, cod),
                     "Factura importada en borrador (no se pudo postear): %s" % exc,
                     year=year)
        return move

    def _create_order(self, entity, row, partner, ref_legible, xmlid, year, tip, cod, specs):
        H = entity["header"]
        is_sale = entity["kind"] == "sale_order"
        model = "sale.order" if is_sale else "purchase.order"
        if is_sale:
            line_cmds = [(0, 0, {
                "product_id": sp["product"].id,
                "name": sp["product"].display_name,
                "sequence": sp["pos"],
                "product_uom_qty": sp["qty"],
                "price_unit": sp["price"],
                "discount": sp["discount"],
                "x_disc1": sp["d1"], "x_disc2": sp["d2"], "x_disc3": sp["d3"],
                "tax_id": [(6, 0, sp["tax"].ids)] if sp["tax"] else False,
            }) for sp in specs]
            vals = {"partner_id": partner.id, "date_order": self.dt(row, H["fec"]) or False,
                    "company_id": self.company.id, "order_line": line_cmds}
        else:
            line_cmds = [(0, 0, {
                "product_id": sp["product"].id,
                "name": sp["product"].display_name,
                "sequence": sp["pos"],
                "product_qty": sp["qty"],
                "price_unit": sp["price"],
                "discount": sp["discount"],
                "x_disc1": sp["d1"], "x_disc2": sp["d2"], "x_disc3": sp["d3"],
                "product_uom": sp["product"].uom_id.id,
                "date_planned": self.dt(row, H["fec"]) or False,
                "taxes_id": [(6, 0, sp["tax"].ids)] if sp["tax"] else False,
            }) for sp in specs]
            vals = {"partner_id": partner.id, "date_order": self.dt(row, H["fec"]) or False,
                    "company_id": self.company.id, "order_line": line_cmds}
        vals.update(self._factusol_bridge(ref_legible, tip, cod, year, row, entity))
        order = self.upsert(model, xmlid, vals, only_if_absent=True)
        # Pedido de cliente confirmado (F_PCL); el presupuesto (F_PRE) queda borrador.
        if order and entity["code"] == "sale_order" and order.state in ("draft", "sent"):
            try:
                order.action_confirm()
            except Exception as exc:  # noqa: BLE001
                self.log("warning", entity["code"], "%s-%s" % (tip, cod),
                         "Pedido importado sin confirmar: %s" % exc, year=year)
        return order

    def _create_picking(self, entity, row, partner, ref_legible, xmlid, specs):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.company.id)], limit=1)
        if not warehouse:
            return None
        ptype = warehouse.out_type_id if entity["picking_type"] == "outgoing" else warehouse.in_type_id
        src = ptype.default_location_src_id
        dest = ptype.default_location_dest_id
        move_cmds = [(0, 0, {
            "name": sp["product"].display_name,
            "product_id": sp["product"].id,
            "product_uom_qty": sp["qty"],
            "product_uom": sp["product"].uom_id.id,
            "location_id": src.id,
            "location_dest_id": dest.id,
        }) for sp in specs]
        vals = {
            "partner_id": partner.id,
            "picking_type_id": ptype.id,
            "location_id": src.id,
            "location_dest_id": dest.id,
            "origin": ref_legible,
            "move_ids": move_cmds,
        }
        # Se deja en borrador (no se valida el stock histórico).
        return self.upsert("stock.picking", xmlid, vals, only_if_absent=True)
