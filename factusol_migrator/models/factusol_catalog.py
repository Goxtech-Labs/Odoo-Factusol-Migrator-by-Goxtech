# -*- coding: utf-8 -*-
from odoo import api, fields, models

from ..tools import schema

PLANE_SELECTION = list(schema.PLANES)
TRANSFORM_SELECTION = [
    ("str", "Texto"),
    ("float", "Número"),
    ("int", "Entero"),
    ("date", "Fecha"),
    ("vat", "NIF / CIF"),
    ("selector", "Selector de IVA"),
    ("raw", "Sin transformar"),
]


class FactusolTableProfile(models.Model):
    """Catálogo de tablas FactuSol → modelo Odoo (sembrado desde el esquema)."""

    _name = "factusol.table.profile"
    _description = "Perfil de tabla FactuSol"
    _order = "load_order, plane"

    entity_code = fields.Char(string="Entidad", required=True, index=True)
    name = fields.Char(string="Nombre", required=True, translate=True)
    plane = fields.Selection(PLANE_SELECTION, string="Plano", required=True)
    table = fields.Char(string="Tabla FactuSol", required=True)
    line_table = fields.Char(string="Tabla de líneas")
    odoo_model = fields.Char(string="Modelo Odoo")
    xmlid_prefix = fields.Char(string="Prefijo External ID")
    load_order = fields.Integer(string="Orden de carga", default=100)
    active = fields.Boolean(default=True)
    mapping_ids = fields.One2many(
        "factusol.field.mapping", "table_profile_id", string="Campos"
    )

    _sql_constraints = [
        ("uniq_entity_code", "unique(entity_code)", "Entidad duplicada en el catálogo."),
    ]

    @api.model
    def _seed_from_catalog(self):
        """Crea/actualiza el catálogo y los mapeos de campo desde ``tools.schema``
        de forma idempotente (post_init_hook)."""
        Mapping = self.env["factusol.field.mapping"]
        for entity in schema.all_entities():
            vals = {
                "entity_code": entity["code"],
                "name": entity["label"],
                "plane": entity["plane"],
                "table": entity["table"],
                "line_table": entity.get("line_table"),
                "odoo_model": entity.get("model"),
                "xmlid_prefix": entity.get("xmlid_prefix"),
                "load_order": entity.get("load_order", 100),
            }
            profile = self.search([("entity_code", "=", entity["code"])], limit=1)
            if profile:
                profile.write(vals)
            else:
                profile = self.create(vals)
            existing = {m.source_field: m for m in profile.mapping_ids}
            for field_def in entity.get("fields", []):
                mvals = {
                    "table_profile_id": profile.id,
                    "source_field": field_def["src"],
                    "target_field": field_def["target"],
                    "transform": field_def["transform"],
                    "is_key": field_def["key"],
                    "include": field_def["min"],  # mínimos premarcados; resto opt-in
                }
                if field_def["src"] in existing:
                    existing[field_def["src"]].write(mvals)
                else:
                    Mapping.create(mvals)
        return True


class FactusolFieldMapping(models.Model):
    """Mapeo campo origen (FactuSol) → campo destino (Odoo)."""

    _name = "factusol.field.mapping"
    _description = "Mapeo de campo FactuSol"
    _order = "is_key desc, include desc, source_field"

    table_profile_id = fields.Many2one(
        "factusol.table.profile", string="Tabla", required=True, ondelete="cascade"
    )
    source_field = fields.Char(string="Campo origen", required=True)
    target_field = fields.Char(string="Campo destino (Odoo)")
    transform = fields.Selection(TRANSFORM_SELECTION, string="Transformación", default="str")
    is_key = fields.Boolean(string="Clave")
    include = fields.Boolean(
        string="Incluir",
        default=False,
        help="Mínimos premarcados; el resto es opt-in (visible, desmarcado).",
    )
