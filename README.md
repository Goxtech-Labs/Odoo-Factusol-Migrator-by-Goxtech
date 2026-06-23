# FactuSol Odoo by GoxTech

Solución **open source** que lleva FactuSol a **Odoo Community** autohospedado: migra los datos y reproduce la lógica de FactuSol que Odoo no tiene de forma nativa. **Dos módulos, nada más.** El objetivo: que cualquier usuario de FactuSol pase a Odoo, gratis y sobre infraestructura propia, conservando su forma de trabajar.

> Marca / autor: **GoxTech**. Licencia: **LGPL-3**. Sin telemetría, sin servicios de pago.

## Los módulos

| Módulo | Rol | Depende de |
|---|---|---|
| **`factusol_core`** | Capa de compatibilidad: lógica de FactuSol **no nativa** en Odoo (numeración `TIPO-TIP-COD`, triple descuento por línea, régimen de IVA por documento + traducción de impuestos, tarifas por margen, campos puente). | `base`, `account`, `sale`, `purchase`, `stock` |
| **`factusol_migrator`** | App de migración: sube `.accdb` (una por año), elige qué importar, carga maestros/documentos/tesorería/config de forma idempotente y verificable. Es la App visible. | `factusol_core` |

Grafo: `factusol_core` ← `factusol_migrator`.

> Variantes talla/color → variantes **nativas** de Odoo (sin módulo de escala). Obras → **fuera de alcance** (viven en otro proyecto de Odoo).

## Cómo usar esta documentación con Claude Code

1. Coloca esta carpeta como raíz del repositorio.
2. Abre Claude Code dentro.
3. Indícale: **"Lee `CLAUDE.md` y `docs/SUITE_ARCHITECTURE.md`, y construye `factusol_core` y luego `factusol_migrator`, fase por fase con tests."**

## Documentación

| Archivo | Qué es |
|---|---|
| `CLAUDE.md` | Manual operativo del agente: misión, principios, estructura, orden de construcción, DoD. **Entrypoint.** |
| `docs/SUITE_ARCHITECTURE.md` | Arquitectura (2 módulos): core vs migrador y qué de FactuSol no es nativo. |
| `docs/MODULE_core.md` | Spec de `factusol_core`. |
| `docs/SPEC_migrator.md` | Especificación completa del migrador (los 6 ejes + roadmap). |
| `docs/SCHEMA_CATALOG.md` | Catálogo del esquema real de FactuSol (tablas, claves, campos, mapeo a Odoo). |
| `docs/DECISIONS.md` | Decisiones abiertas a confirmar. |

## Requisitos del entorno

Odoo **Community** 18.0 (portable a 17/19) · Python 3.10+ · PostgreSQL · lectura `.accdb` en Python puro (`pyaccdb`/`access-parser`). Sin Enterprise, sin Windows obligatorio.
