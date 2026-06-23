# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "factusol.document.mixin"]

    x_factusol_commission_amount = fields.Monetary(
        string="Comisión (importe)",
        compute="_compute_factusol_commission_amount",
        currency_field="currency_id",
        help="Comisión simple del agente: base imponible × comisión (%).",
    )

    @api.depends("amount_untaxed", "x_factusol_commission_rate")
    def _compute_factusol_commission_amount(self):
        for move in self:
            move.x_factusol_commission_amount = (
                move.amount_untaxed * (move.x_factusol_commission_rate or 0.0) / 100.0
            )


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "factusol.line.mixin"]
