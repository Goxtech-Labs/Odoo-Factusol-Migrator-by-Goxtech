# -*- coding: utf-8 -*-
import base64
import logging
import os
import tempfile

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import AccessReader, AccessReaderError, parse_company_year

_logger = logging.getLogger(__name__)


class FactusolSource(models.Model):
    """Un fichero ``.accdb`` = una empresa + un ejercicio (un año)."""

    _name = "factusol.source"
    _description = "Base FactuSol (.accdb = empresa + ejercicio)"
    _order = "fiscal_year, company_code"

    name = fields.Char(compute="_compute_name", store=True)
    accdb_file = fields.Binary(string="Fichero .accdb", attachment=True, required=True)
    file_name = fields.Char(string="Nombre del fichero")
    password = fields.Char(string="Contraseña (si está cifrado)")
    company_code = fields.Char(string="Empresa (EEE)", index=True)
    fiscal_year = fields.Integer(string="Ejercicio", index=True)
    backend = fields.Char(string="Backend de lectura", readonly=True)
    table_count = fields.Integer(string="Tablas detectadas", readonly=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("ready", "Listo"), ("error", "Error")],
        default="draft", required=True, index=True,
    )
    note = fields.Text(string="Notas / errores")

    @api.depends("file_name", "company_code", "fiscal_year")
    def _compute_name(self):
        for source in self:
            if source.company_code or source.fiscal_year:
                source.name = "Empresa %s · ejercicio %s" % (
                    source.company_code or "?", source.fiscal_year or "?",
                )
            else:
                source.name = source.file_name or "Base FactuSol"

    # -- Lectura -------------------------------------------------------------
    def _write_temp(self):
        self.ensure_one()
        if not self.accdb_file:
            raise UserError(_("No hay fichero .accdb cargado."))
        data = base64.b64decode(self.accdb_file)
        fd, path = tempfile.mkstemp(suffix=".accdb", prefix="factusol_")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return path

    def get_reader(self):
        """Devuelve un :class:`AccessReader` abierto sobre el fichero."""
        self.ensure_one()
        path = self._write_temp()
        return AccessReader.open(path, password=self.password or None)

    # -- Acciones ------------------------------------------------------------
    def action_scan(self):
        """Detecta backend, empresa y ejercicio; cuenta tablas."""
        for source in self:
            try:
                company, year = parse_company_year(source.file_name or "")
                reader = source.get_reader()
                tables = reader.list_tables()
                if (not company or not year) and "F_EMP" in tables:
                    rows = reader.read_all("F_EMP")
                    if rows:
                        company = company or str(rows[0].get("CODEMP") or "").strip()
                source.write({
                    "company_code": company or source.company_code,
                    "fiscal_year": year or source.fiscal_year,
                    "backend": reader.backend_name,
                    "table_count": len(tables),
                    "state": "ready",
                    "note": False,
                })
            except AccessReaderError as exc:
                source.write({"state": "error", "note": str(exc)})
            except Exception as exc:  # noqa: BLE001
                _logger.exception("FactuSol scan failed")
                source.write({"state": "error", "note": str(exc)})
        return True

    def action_purge_file(self):
        """Borra el .accdb (dato personal sensible) conservando los metadatos."""
        self.write({"accdb_file": False})
        return True
