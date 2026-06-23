# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools import schema
from .transformers import MigrationEngine

_logger = logging.getLogger(__name__)


class FactusolImportRun(models.Model):
    """Ejecución de migración sobre uno o varios ``source`` (años) → una
    ``res.company``. Mantiene contadores por año e informe de fidelidad."""

    _name = "factusol.import.run"
    _description = "Ejecución de migración FactuSol"
    _order = "id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company", string="Compañía destino", required=True,
        default=lambda self: self.env.company,
    )
    source_ids = fields.Many2many("factusol.source", string="Bases (años)")
    profile_id = fields.Many2one("factusol.import.profile", string="Perfil")
    dry_run = fields.Boolean(string="Última ejecución en modo previo", readonly=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("preview", "Previsualizado"),
         ("done", "Migrado"), ("failed", "Con errores")],
        default="draft", required=True, index=True,
    )
    date_start = fields.Datetime(readonly=True)
    date_end = fields.Datetime(readonly=True)
    result_summary = fields.Json(string="Resumen", readonly=True)
    fidelity_html = fields.Html(string="Informe de fidelidad", readonly=True, sanitize=False)
    log_ids = fields.One2many("factusol.import.log", "run_id", string="Incidencias")
    staging_ids = fields.One2many("factusol.staging.row", "run_id")
    count_source = fields.Integer(compute="_compute_counts", string="Origen")
    count_ok = fields.Integer(compute="_compute_counts", string="Migrados")
    count_failed = fields.Integer(compute="_compute_counts", string="Fallidos")
    count_skipped = fields.Integer(compute="_compute_counts", string="Omitidos")
    log_count = fields.Integer(compute="_compute_counts", string="Nº de incidencias")

    @api.depends("source_ids", "company_id")
    def _compute_name(self):
        for run in self:
            years = run.source_ids.mapped("fiscal_year")
            label = ", ".join(str(y) for y in sorted(set(years))) if years else "—"
            run.name = "Migración %s [%s]" % (run.company_id.name or "", label)

    @api.depends("result_summary", "log_ids")
    def _compute_counts(self):
        for run in self:
            src = ok = failed = skipped = 0
            for ydata in (run.result_summary or {}).values():
                for stats in ydata.values():
                    src += stats.get("source", 0)
                    ok += stats.get("ok", 0)
                    failed += stats.get("failed", 0)
                    skipped += stats.get("skipped", 0)
            run.count_source = src
            run.count_ok = ok
            run.count_failed = failed
            run.count_skipped = skipped
            run.log_count = len(run.log_ids)

    # -- Plan de carga -------------------------------------------------------
    def _enabled_entity_codes(self):
        """Códigos de entidad habilitados por el perfil (o todos si no hay)."""
        self.ensure_one()
        if not self.profile_id:
            return [e["code"] for e in schema.all_entities()]
        return self.profile_id.line_ids.filtered("enabled").mapped("entity")

    def _plan(self):
        """Definiciones de entidad a cargar, en orden de plano/carga."""
        enabled = set(self._enabled_entity_codes())
        return [e for e in schema.all_entities() if e["code"] in enabled]

    def _sources_sorted(self):
        return self.source_ids.sorted(key=lambda s: (s.fiscal_year or 0, s.company_code or ""))

    # -- Motor ---------------------------------------------------------------
    def _execute(self, dry_run):
        self.ensure_one()
        sources = self._sources_sorted()
        if not sources:
            raise UserError(_("Seleccione al menos una base (año) para migrar."))
        not_ready = sources.filtered(lambda s: s.state != "ready")
        if not_ready:
            raise UserError(_(
                "Analice las bases antes de migrar (estado 'Listo'): %s"
            ) % ", ".join(not_ready.mapped("name")))

        # Limpia resultados previos de este run.
        self.log_ids.unlink()
        self.staging_ids.unlink()

        last_year = max(sources.mapped("fiscal_year") or [0])
        plan = self._plan()
        engine = MigrationEngine(self.env, self, dry_run=dry_run)
        summary = {}

        self.write({"date_start": fields.Datetime.now(), "dry_run": dry_run})
        for source in sources:
            try:
                reader = source.get_reader()
            except Exception as exc:  # noqa: BLE001
                engine.log("error", "source", source.name, str(exc), year=source.fiscal_year)
                continue
            year_key = str(source.fiscal_year or 0)
            ybucket = summary.setdefault(year_key, {})
            for entity in plan:
                # Stock: solo el último año seleccionado (foto, no acumulable).
                if entity.get("last_year_only") and source.fiscal_year != last_year:
                    continue
                line = self._profile_line(entity["code"])
                try:
                    stats = engine.run_entity(source, reader, entity, line)
                except Exception as exc:  # noqa: BLE001
                    _logger.exception("FactuSol entity %s failed", entity["code"])
                    engine.log("error", entity["code"], "", str(exc), year=source.fiscal_year)
                    stats = {"source": 0, "ok": 0, "failed": 1, "skipped": 0}
                ybucket[entity["code"]] = stats
            if not dry_run:
                self.env.cr.commit()  # commit por año en runs largos

        self.result_summary = summary
        self.fidelity_html = self._render_fidelity(summary)
        self.write({
            "date_end": fields.Datetime.now(),
            "state": "preview" if dry_run else (
                "failed" if self.count_failed else "done"
            ),
        })
        return True

    def _profile_line(self, entity_code):
        if not self.profile_id:
            return self.env["factusol.import.profile.line"]
        return self.profile_id.line_ids.filtered(lambda l: l.entity == entity_code)[:1]

    # -- Acciones ------------------------------------------------------------
    def action_dry_run(self):
        self.ensure_one()
        self._execute(dry_run=True)
        return self._reload_action()

    def action_migrate(self):
        self.ensure_one()
        self._execute(dry_run=False)
        return self._reload_action()

    def action_reprocess_failed(self):
        """Re-ejecuta la migración (idempotente): los OK se saltan, los failed
        se reintentan."""
        self.ensure_one()
        self.log_ids.filtered(lambda l: l.level == "error").write({"state": "reprocessed"})
        self._execute(dry_run=False)
        return self._reload_action()

    def _reload_action(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    # -- Informe de fidelidad ------------------------------------------------
    def _render_fidelity(self, summary):
        labels = {e["code"]: e["label"] for e in schema.all_entities()}
        rows = []
        for year in sorted(summary.keys()):
            rows.append("<tr class='table-primary'><th colspan='6'>Ejercicio %s</th></tr>" % year)
            for code, st in sorted(summary[year].items(), key=lambda kv: kv[0]):
                amt_src = st.get("amount_src")
                amt_odoo = st.get("amount_odoo")
                squared = ""
                if amt_src is not None:
                    diff = abs((amt_src or 0.0) - (amt_odoo or 0.0))
                    ok = diff <= 0.01
                    squared = (
                        "<span style='color:%s'>%.2f / %.2f%s</span>" % (
                            "green" if ok else "red", amt_src or 0.0, amt_odoo or 0.0,
                            "" if ok else " ⚠",
                        )
                    )
                cls = " style='color:red'" if st.get("failed") else ""
                rows.append(
                    "<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                        cls, labels.get(code, code),
                        st.get("source", 0), st.get("ok", 0),
                        st.get("failed", 0), st.get("skipped", 0), squared,
                    )
                )
        head = (
            "<thead><tr><th>Entidad</th><th>Origen</th><th>OK</th>"
            "<th>Fallidos</th><th>Omitidos</th><th>Cuadre importes (origen/Odoo)</th></tr></thead>"
        )
        return (
            "<table class='table table-sm table-bordered'>%s<tbody>%s</tbody></table>"
            % (head, "".join(rows))
        )
