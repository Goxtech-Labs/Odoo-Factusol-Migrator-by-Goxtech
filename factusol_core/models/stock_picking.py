# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "factusol.document.mixin"]
