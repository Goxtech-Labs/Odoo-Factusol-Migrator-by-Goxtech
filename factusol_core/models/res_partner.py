# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    x_factusol_code = fields.Char(
        string="Código FactuSol",
        index=True,
        copy=False,
        help="Código origen del tercero en FactuSol (CODCLI / CODPRO). "
             "Permite conciliar y re-migrar de forma idempotente.",
    )
    x_factusol_agent_code = fields.Char(string="Agente / Comercial (FactuSol)", copy=False)
