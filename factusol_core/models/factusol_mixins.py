# -*- coding: utf-8 -*-
from odoo import api, fields, models

from odoo.addons.factusol_core.tools import (
    combine_discounts,
    dimension_xmlid,
    fact_xmlid,
    format_doc_ref,
    price_from_margin,
)

IVA_REGIME_SELECTION = [
    ("0", "Con IVA"),
    ("1", "Sin IVA"),
    ("2", "Intracomunitario"),
    ("3", "Exportación / Importación"),
]


class FactusolHelperMixin(models.AbstractModel):
    """Exposes the pure helpers as model methods so the migrator (and safe_eval
    transformations) can call them through ``self.env['factusol.helper.mixin']``.
    """

    _name = "factusol.helper.mixin"
    _description = "FactuSol compatibility helpers"

    @api.model
    def fs_format_doc_ref(self, tipo, tip, cod, mask_width=6):
        return format_doc_ref(tipo, tip, cod, mask_width)

    @api.model
    def fs_combine_discounts(self, d1=0.0, d2=0.0, d3=0.0):
        return combine_discounts(d1, d2, d3)

    @api.model
    def fs_price_from_margin(self, cost, margin, basis="cost"):
        return price_from_margin(cost, margin, basis)

    @api.model
    def fs_dimension_xmlid(self, prefix, code):
        return dimension_xmlid(prefix, code)

    @api.model
    def fs_fact_xmlid(self, prefix, year, tip, cod, mask_width=6):
        return fact_xmlid(prefix, year, tip, cod, mask_width)


class FactusolDocumentMixin(models.AbstractModel):
    """Bridge fields shared by every migrated document (account.move, sale.order,
    purchase.order, stock.picking). Keeps the original FactuSol numbering as a
    readable reference while Odoo keeps its own internal sequence.
    """

    _name = "factusol.document.mixin"
    _description = "FactuSol document bridge fields"

    x_factusol_ref = fields.Char(
        string="Ref. FactuSol",
        index=True,
        copy=False,
        help="Referencia legible del documento origen, p. ej. FAC-1-000001.",
    )
    x_factusol_serie = fields.Char(string="Serie FactuSol (TIP)", copy=False)
    x_factusol_code = fields.Char(string="Código FactuSol (COD)", copy=False)
    x_factusol_year = fields.Integer(string="Ejercicio FactuSol", copy=False)
    x_factusol_iva_regime = fields.Selection(
        IVA_REGIME_SELECTION,
        string="Régimen IVA (FactuSol)",
        help="Régimen de IVA del documento en FactuSol; guía la posición fiscal "
             "y la traducción de impuestos.",
    )
    x_factusol_agent_code = fields.Char(string="Agente / Comercial (FactuSol)", copy=False)
    x_factusol_commission_rate = fields.Float(
        string="Comisión (%)", digits="Discount", copy=False,
    )


class FactusolLineMixin(models.AbstractModel):
    """Triple cascade discount + origin code on document lines."""

    _name = "factusol.line.mixin"
    _description = "FactuSol document line bridge fields"

    x_factusol_code = fields.Char(string="Código FactuSol", copy=False)
    x_disc1 = fields.Float(string="Dto. 1 (%)", digits="Discount")
    x_disc2 = fields.Float(string="Dto. 2 (%)", digits="Discount")
    x_disc3 = fields.Float(string="Dto. 3 (%)", digits="Discount")

    @api.onchange("x_disc1", "x_disc2", "x_disc3")
    def _onchange_factusol_discounts(self):
        """Pour the triple discount into the native ``discount`` field so Odoo
        recomputes amounts. Editing the single native discount stays possible."""
        for line in self:
            if line.x_disc1 or line.x_disc2 or line.x_disc3:
                line.discount = combine_discounts(
                    line.x_disc1, line.x_disc2, line.x_disc3
                )
