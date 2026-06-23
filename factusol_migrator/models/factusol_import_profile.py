# -*- coding: utf-8 -*-
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import schema

# Composición de los presets de fábrica (qué entidades activa cada uno).
_DIM_BASIC = ["warehouse", "section", "family", "customer", "supplier", "product", "variant"]
_PRESETS = {
    "Mínimo": _DIM_BASIC + ["stock"],
    "Comercial": _DIM_BASIC + ["pricelist", "stock",
                               "quotation", "sale_order", "delivery", "customer_invoice",
                               "purchase_order", "receipt", "vendor_bill"],
    "Contable completo": [e["code"] for e in schema.all_entities()],
    "Personalizado": [],
}


class FactusolImportProfile(models.Model):
    """Selección + opciones guardadas y reutilizables (selectividad total)."""

    _name = "factusol.import.profile"
    _description = "Perfil de importación FactuSol"
    _order = "is_preset desc, name"

    name = fields.Char(required=True, translate=True)
    description = fields.Text()
    is_preset = fields.Boolean(string="Preset de fábrica", readonly=True)
    line_ids = fields.One2many(
        "factusol.import.profile.line", "profile_id", string="Entidades", copy=True
    )

    def action_clone(self):
        """Clona el perfil (los presets no se editan; se clonan)."""
        self.ensure_one()
        copy = self.copy({"name": _("%s (copia)") % self.name, "is_preset": False})
        return {
            "type": "ir.actions.act_window",
            "res_model": "factusol.import.profile",
            "res_id": copy.id,
            "view_mode": "form",
            "target": "current",
        }

    def write(self, vals):
        for profile in self:
            if profile.is_preset and not self.env.context.get("allow_preset_write"):
                raise UserError(
                    _("Los presets de fábrica no se editan: clónelos primero.")
                )
        return super().write(vals)

    # -- Export / import (compartir criterios entre instalaciones) -----------
    def export_profile(self):
        self.ensure_one()
        return json.dumps({
            "name": self.name,
            "description": self.description or "",
            "lines": [{
                "entity": ln.entity,
                "enabled": ln.enabled,
                "field_whitelist": ln.field_whitelist or "",
                "options": ln.options or {},
            } for ln in self.line_ids],
        }, ensure_ascii=False, indent=2)

    @api.model
    def import_profile(self, data):
        payload = json.loads(data) if isinstance(data, str) else data
        profile = self.create({
            "name": payload.get("name") or _("Perfil importado"),
            "description": payload.get("description"),
        })
        for ln in payload.get("lines", []):
            self.env["factusol.import.profile.line"].create({
                "profile_id": profile.id,
                "entity": ln["entity"],
                "enabled": ln.get("enabled", True),
                "field_whitelist": ln.get("field_whitelist"),
                "options": ln.get("options") or {},
            })
        return profile

    # -- Presets de fábrica (post_init_hook) ---------------------------------
    @api.model
    def _seed_presets(self):
        Line = self.env["factusol.import.profile.line"]
        all_codes = [e["code"] for e in schema.all_entities()]
        for name, enabled_codes in _PRESETS.items():
            profile = self.search([("name", "=", name), ("is_preset", "=", True)], limit=1)
            if not profile:
                profile = self.create({"name": name, "is_preset": True})
            existing = {ln.entity: ln for ln in profile.line_ids}
            for code in all_codes:
                enabled = code in enabled_codes
                if code in existing:
                    existing[code].with_context(allow_preset_line=True).write(
                        {"enabled": enabled}
                    )
                else:
                    Line.create({
                        "profile_id": profile.id, "entity": code, "enabled": enabled,
                    })
        return True


class FactusolImportProfileLine(models.Model):
    _name = "factusol.import.profile.line"
    _description = "Entidad seleccionada en un perfil FactuSol"
    _order = "entity"

    profile_id = fields.Many2one(
        "factusol.import.profile", required=True, ondelete="cascade"
    )
    entity = fields.Char(string="Entidad", required=True)
    entity_label = fields.Char(string="Nombre", compute="_compute_entity_label")
    plane = fields.Char(string="Plano", compute="_compute_entity_label")
    enabled = fields.Boolean(string="Migrar", default=True)
    field_whitelist = fields.Char(
        string="Campos (lista)",
        help="Lista de campos origen separados por coma. Vacío = mínimos del catálogo.",
    )
    options = fields.Json(string="Opciones")

    @api.depends("entity")
    def _compute_entity_label(self):
        catalog = {e["code"]: e for e in schema.all_entities()}
        planes = dict(schema.PLANES)
        for line in self:
            ent = catalog.get(line.entity)
            line.entity_label = ent["label"] if ent else line.entity
            line.plane = planes.get(ent["plane"]) if ent else ""
