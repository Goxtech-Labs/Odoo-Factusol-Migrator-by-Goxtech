# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .factusol_mixins import IVA_REGIME_SELECTION  # noqa: F401  (kept for reference)

SELECTOR_SELECTION = [
    ("0", "IVA 1"),
    ("1", "IVA 2"),
    ("2", "IVA 3"),
    ("3", "Exento"),
]


class FactusolTaxMap(models.Model):
    """Configurable translation table: FactuSol per-line IVA selector
    (0=IVA1, 1=IVA2, 2=IVA3, 3=Exento) -> Odoo ``account.tax``.

    The percentages live in the FactuSol config (F_CFG); this table binds each
    origin selector to a real tax of the destination localization (l10n_ar /
    l10n_es), per company and per usage (sale / purchase). Reuses the native
    taxes; it does not create duplicates.
    """

    _name = "factusol.tax.map"
    _description = "FactuSol IVA selector → impuesto Odoo"
    _order = "company_id, tax_type, factusol_selector"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        ondelete="cascade",
    )
    factusol_selector = fields.Selection(
        SELECTOR_SELECTION, string="Selector IVA (FactuSol)", required=True
    )
    tax_type = fields.Selection(
        [("sale", "Venta"), ("purchase", "Compra")],
        string="Uso",
        required=True,
        default="sale",
    )
    origin_percent = fields.Float(string="% IVA origen (F_CFG)", digits="Discount")
    tax_id = fields.Many2one(
        "account.tax",
        string="Impuesto Odoo",
        required=True,
        ondelete="cascade",
        domain="[('type_tax_use', '=', tax_type), ('company_id', '=', company_id)]",
    )

    _sql_constraints = [
        (
            "uniq_selector_per_company_use",
            "unique(company_id, factusol_selector, tax_type)",
            "Ya existe un mapeo para ese selector de IVA en esta compañía y uso.",
        ),
    ]

    @api.depends("factusol_selector", "tax_type", "tax_id")
    def _compute_name(self):
        labels = dict(SELECTOR_SELECTION)
        uses = {"sale": "Venta", "purchase": "Compra"}
        for rec in self:
            sel = labels.get(rec.factusol_selector, rec.factusol_selector or "")
            use = uses.get(rec.tax_type, rec.tax_type or "")
            rec.name = "%s (%s) → %s" % (sel, use, rec.tax_id.display_name or "—")

    @api.model
    def resolve_tax(self, selector, tax_type="sale", company=None):
        """Return the ``account.tax`` configured for a FactuSol IVA selector.

        ``selector`` accepts ``0/1/2/3`` (int or str). Returns an empty recordset
        if no mapping exists (the caller decides the fallback / warning).
        """
        company = company or self.env.company
        rec = self.search(
            [
                ("company_id", "=", company.id),
                ("factusol_selector", "=", str(selector)),
                ("tax_type", "=", tax_type),
            ],
            limit=1,
        )
        return rec.tax_id
