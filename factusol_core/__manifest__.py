# -*- coding: utf-8 -*-
{
    "name": "FactuSol Core (compatibilidad)",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "Capa de compatibilidad FactuSol para Odoo Community: numeracion "
               "TIPO-TIP-COD, triple descuento por linea, regimen de IVA por "
               "documento, tarifas por margen y campos puente.",
    "description": """
FactuSol Core
=============

Reproduce la logica de FactuSol que **no es nativa** en Odoo Community, como
base reutilizable por *factusol_migrator*. Se implementa como extensiones
(mixins) de los modelos estandar, sin romper su comportamiento nativo:

* Numeracion / referencia de documento ``TIPO-TIP-COD`` (campos puente).
* Triple descuento en cascada por linea (``x_disc1/2/3`` -> ``discount``).
* Regimen de IVA por documento + tabla de traduccion de impuestos
  (``factusol.tax.map``: selector de IVA origen -> ``account.tax``).
* Tarifas por margen (precio = coste + margen).
* Campos puente / codigos origen FactuSol para conciliar y re-migrar.

Parte de la suite **FactuSol Odoo by GoxTech**.
""",
    "author": "GoxTech",
    "website": "https://github.com/Goxtech-Labs/Odoo-Factusol-Migrator-by-Goxtech",
    "license": "LGPL-3",
    "depends": ["base", "account", "sale", "purchase", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/factusol_tax_map_views.xml",
        "views/factusol_document_views.xml",
        "views/factusol_line_views.xml",
    ],
    "installable": True,
    "application": False,
}
