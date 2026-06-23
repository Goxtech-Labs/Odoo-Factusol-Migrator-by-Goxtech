# -*- coding: utf-8 -*-
from odoo import fields, models

from ..tools import schema

PLANE_SELECTION = list(schema.PLANES)


class FactusolStagingRow(models.Model):
    """Fila cruda (JSON) extraída de FactuSol, por lote (auditoría / preview)."""

    _name = "factusol.staging.row"
    _description = "Fila de staging FactuSol"
    _order = "id"

    run_id = fields.Many2one("factusol.import.run", required=True, ondelete="cascade", index=True)
    entity = fields.Char(string="Entidad", index=True)
    table = fields.Char(string="Tabla")
    plane = fields.Selection(PLANE_SELECTION, string="Plano")
    fiscal_year = fields.Integer(string="Ejercicio")
    key = fields.Char(string="Clave origen", index=True)
    line_no = fields.Integer(string="Línea")
    data = fields.Json(string="Datos (crudo)")
    state = fields.Selection(
        [("pending", "Pendiente"), ("done", "Migrado"),
         ("failed", "Fallido"), ("skipped", "Omitido")],
        default="pending", index=True,
    )


class FactusolImportLog(models.Model):
    """Incidencia por fila: tabla, clave, campo, mensaje y payload para reproceso."""

    _name = "factusol.import.log"
    _description = "Incidencia de importación FactuSol"
    _order = "id desc"

    run_id = fields.Many2one("factusol.import.run", required=True, ondelete="cascade", index=True)
    entity = fields.Char(string="Entidad", index=True)
    table = fields.Char(string="Tabla")
    fiscal_year = fields.Integer(string="Ejercicio")
    key = fields.Char(string="Clave origen")
    field = fields.Char(string="Campo")
    level = fields.Selection(
        [("info", "Info"), ("warning", "Aviso"), ("error", "Error")],
        default="error", index=True,
    )
    message = fields.Text(string="Mensaje")
    payload = fields.Json(string="Payload")
    state = fields.Selection(
        [("open", "Abierto"), ("reprocessed", "Reprocesado"), ("ignored", "Ignorado")],
        default="open", index=True,
    )
