# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "factusol.document.mixin"]


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "factusol.line.mixin"]
