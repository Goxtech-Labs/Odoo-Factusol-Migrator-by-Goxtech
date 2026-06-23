# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class FactusolImportWizard(models.TransientModel):
    """Asistente lineal de 4 pasos (autogestión, lenguaje no técnico)."""

    _name = "factusol.import.wizard"
    _description = "Asistente de migración FactuSol"

    step = fields.Selection(
        [("upload", "1 · Subir base(s)"),
         ("select", "2 · Elegir qué migrar"),
         ("preview", "3 · Previsualizar"),
         ("migrate", "4 · Migrar y verificar")],
        default="upload", required=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía destino", required=True,
        default=lambda self: self.env.company,
    )
    file_ids = fields.One2many("factusol.import.wizard.file", "wizard_id", string="Ficheros .accdb")
    source_ids = fields.Many2many("factusol.source", string="Bases detectadas (años)")
    profile_id = fields.Many2one("factusol.import.profile", string="Perfil de importación")
    run_id = fields.Many2one("factusol.import.run", string="Ejecución")
    preview_html = fields.Html(string="Resultado", readonly=True, sanitize=False)

    # -- Navegación ----------------------------------------------------------
    def _reload(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "name": _("Migración FactuSol"),
        }

    def action_back_to_upload(self):
        self.step = "upload"
        return self._reload()

    def action_back_to_select(self):
        self.step = "select"
        return self._reload()

    # -- Paso 1 → 2: analizar las bases --------------------------------------
    def action_scan(self):
        self.ensure_one()
        if not self.file_ids:
            raise UserError(_("Suba al menos un fichero .accdb."))
        Source = self.env["factusol.source"]
        sources = self.source_ids
        for upload in self.file_ids:
            if not upload.accdb_file:
                continue
            src = Source.create({
                "accdb_file": upload.accdb_file,
                "file_name": upload.file_name,
                "password": upload.password,
            })
            src.action_scan()
            sources |= src
        errors = sources.filtered(lambda s: s.state == "error")
        if errors:
            raise UserError(_(
                "No se pudieron leer algunas bases:\n%s"
            ) % "\n".join("· %s: %s" % (s.file_name, s.note) for s in errors))
        self.source_ids = [(6, 0, sources.ids)]
        if not self.profile_id:
            self.profile_id = self.env["factusol.import.profile"].search(
                [("name", "=", "Comercial"), ("is_preset", "=", True)], limit=1)
        self.step = "select"
        return self._reload()

    # -- Run subyacente ------------------------------------------------------
    def _ensure_run(self):
        if not self.source_ids:
            raise UserError(_("Seleccione al menos una base (año)."))
        vals = {
            "company_id": self.company_id.id,
            "source_ids": [(6, 0, self.source_ids.ids)],
            "profile_id": self.profile_id.id if self.profile_id else False,
        }
        if self.run_id:
            self.run_id.write(vals)
        else:
            self.run_id = self.env["factusol.import.run"].create(vals)
        return self.run_id

    # -- Paso 2 → 3: dry-run -------------------------------------------------
    def action_dry_run(self):
        self.ensure_one()
        run = self._ensure_run()
        run.action_dry_run()
        self.preview_html = run.fidelity_html
        self.step = "preview"
        return self._reload()

    # -- Paso 3 → 4: migrar de verdad ----------------------------------------
    def action_migrate(self):
        self.ensure_one()
        run = self._ensure_run()
        run.action_migrate()
        self.preview_html = run.fidelity_html
        self.step = "migrate"
        return self._reload()

    def action_open_run(self):
        self.ensure_one()
        if not self.run_id:
            raise UserError(_("Todavía no hay ejecución."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "factusol.import.run",
            "res_id": self.run_id.id,
            "view_mode": "form",
            "target": "current",
        }


class FactusolImportWizardFile(models.TransientModel):
    _name = "factusol.import.wizard.file"
    _description = "Fichero .accdb subido al asistente"

    wizard_id = fields.Many2one("factusol.import.wizard", required=True, ondelete="cascade")
    accdb_file = fields.Binary(string="Fichero .accdb", required=True)
    file_name = fields.Char(string="Nombre")
    password = fields.Char(string="Contraseña")
