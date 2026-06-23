# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_factusol_code = fields.Char(
        string="Código FactuSol",
        index=True,
        copy=False,
        help="Código origen del artículo en FactuSol (CODART).",
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    x_factusol_code = fields.Char(
        string="Código FactuSol (variante)",
        index=True,
        copy=False,
        help="Código origen de la variante (artículo + talla/color) en FactuSol.",
    )
