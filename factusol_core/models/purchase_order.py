# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "factusol.document.mixin"]


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _inherit = ["purchase.order.line", "factusol.line.mixin"]
