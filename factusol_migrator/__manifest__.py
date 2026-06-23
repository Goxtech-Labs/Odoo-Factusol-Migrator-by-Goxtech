# -*- coding: utf-8 -*-
{
    "name": "FactuSol Odoo by GoxTech",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Migrador autónomo FactuSol → Odoo Community: sube las bases .accdb "
               "(una por año), elige qué importar, migra de forma idempotente y "
               "verifica la fidelidad.",
    "description": """
FactuSol Odoo by GoxTech — Migrador
===================================

App de migración FactuSol → **Odoo Community** autohospedado, open source y
gratuita. El usuario completa cuatro pasos —subir las bases ``.accdb`` (una por
año), seleccionar qué importar, migrar y verificar— y obtiene en Odoo lo
esencial de FactuSol.

* Lectura de ``.accdb`` en **Python puro** (pyaccdb / access-parser; mdbtools
  opcional), sin Windows ni binarios obligatorios.
* **Multi-ejercicio**: un fichero por año, claves correctas (dimensiones sin
  año → fusionan; hechos/tesorería con año → no colisionan; stock del último año).
* **Selectividad total**: planos / entidades / campos con perfiles reutilizables
  (Mínimo, Comercial, Contable completo, Personalizado).
* **Idempotente** (External IDs) y con **informe de fidelidad** por año.

Depende de ``factusol_core`` (capa de compatibilidad). Autor: GoxTech · LGPL-3.
""",
    "author": "GoxTech",
    "website": "https://github.com/Goxtech-Labs/Odoo-Factusol-Migrator-by-Goxtech",
    "license": "LGPL-3",
    "depends": ["factusol_core", "account", "sale", "purchase", "stock"],
    "data": [
        "security/factusol_security.xml",
        "security/ir.model.access.csv",
        "views/factusol_source_views.xml",
        "views/factusol_import_run_views.xml",
        "views/factusol_import_profile_views.xml",
        "views/factusol_import_log_views.xml",
        "views/factusol_catalog_views.xml",
        "wizard/factusol_import_wizard_views.xml",
        "views/factusol_menus.xml",
    ],
    "post_init_hook": "post_init_seed",
    "application": True,
    "installable": True,
    # Los lectores .accdb se cargan en runtime y degradan entre sí: NO se
    # declaran como external_dependencies para no bloquear la instalación en un
    # CE limpio. Ver requirements.txt y README.
}
