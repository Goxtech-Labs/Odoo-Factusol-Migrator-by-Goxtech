# CLAUDE.md — Manual operativo (suite FactuSol Odoo by GoxTech)

> Entrypoint para Claude Code. Léelo completo antes de tocar código.
> Arquitectura de la suite: **`docs/SUITE_ARCHITECTURE.md`**. Migrador: **`docs/SPEC_migrator.md`**. Esquema real: **`docs/SCHEMA_CATALOG.md`**. Módulos: **`docs/MODULE_*.md`**. Decisiones: **`docs/DECISIONS.md`**.

---

## 1. Misión

Construir **FactuSol Odoo by GoxTech**: **dos módulos** de Odoo Community que permiten a cualquier usuario de FactuSol pasar a **Odoo autohospedado, gratis y open source**, conservando su forma de trabajar. La solución **migra** los datos (`factusol_migrator`) y **reproduce la lógica de FactuSol no nativa** en Odoo (`factusol_core`). Sin verticales ni App paraguas.

## 2. Principios inviolables (NO negociar)

1. **Solo Odoo Community** (sin Enterprise/Odoo.sh/Studio). 2. **Open source — LGPL-3**, autor **GoxTech**. 3. **Autohospedado y gratis** (sin SaaS/APIs de terceros/costes). 4. **Sin Windows ni binarios obligatorios** (lectura `.accdb` en Python puro). 5. **Sin telemetría.** 6. **Autogestión** (todo desde la UI). 7. **Selectividad total** (elegir qué importar; perfiles). 8. **Idempotencia** (External IDs). 9. **Multi-ejercicio** (un `.accdb` por año, claves correctas). 10. **Fidelidad verificable** (informe de cuadre por año). 11. **Modularidad**: se instala solo lo necesario; reutilizar lo nativo de Odoo, crear solo lo que falte.

## 3. Módulos y orden de construcción

```
factusol_core       (compatibilidad: lógica FactuSol no nativa)   ← construir 1º
  └ factusol_migrator  (ETL / App; ver docs/SPEC_migrator.md)     ← 2º
```
**Dos módulos, nada más.** No empieces el migrador sin que `factusol_core` pase sus tests. Cada módulo se construye **por fases** con tests en verde.
**Variantes talla/color** → variantes **nativas** de Odoo (sin módulo de escala). **Obras** → fuera de alcance (viven en otro proyecto de Odoo, no se tocan aquí).

## 4. Estructura del repositorio (multi-addon)

```
factusol-odoo-goxtech/
├── README.md
├── CLAUDE.md
├── LICENSE                  # LGPL-3
├── docs/                    # esta documentación
├── factusol_core/
└── factusol_migrator/       # App (application=True); estructura interna en docs/SPEC_migrator.md §CLAUDE
```
Cada addon: `__manifest__.py` (autor "GoxTech", `license="LGPL-3"`), `models/`, `views/`, `security/` (`ir.model.access.csv`), `tests/`, `static/description/` (icono+capturas). El `factusol_migrator` es la App visible "FactuSol Odoo by GoxTech".

## 5. Lectura de `.accdb` (regla de oro de la autonomía)

Backends tras `AccessReader` con degradación automática: **`pyaccdb`** (primario, lazy, soporta cifrado) → **`access-parser`** (fallback) → **`mdbtools`** (opcional, nunca requisito). Detalle en `docs/SPEC_migrator.md` §3/§5.

## 6. Multi-ejercicio y claves (crítico)

Un `.accdb` por año; códigos de documento se reinician cada ejercicio.
- **Dimensiones**: External ID **sin año** (`cli_<cod>`) → se fusionan entre años (gana el más reciente).
- **Hechos/tesorería**: External ID **con año** (`fac_<eje>_<TIP>-<COD>`). Número legible = `<TIPO>-<TIP>-<COD>` (`FAC-1-000001`). Cabecera↔línea se unen por `(TIP,COD)`, líneas por `POS`.
- **Stock**: solo del último año seleccionado. Detalle en `docs/SPEC_migrator.md` §3.1 y `docs/SCHEMA_CATALOG.md`.

## 7. Cómo trabaja el agente

- Construye módulo a módulo y fase a fase; cada cambio con su test.
- **No inventes nombres de campo**: usa `docs/SCHEMA_CATALOG.md`.
- **No hardcodees** nombres de campo en la lógica: viven en datos/perfiles configurables.
- **Reutiliza lo nativo de Odoo**; crea solo lo que falte (ver tabla "no nativo" en `docs/SUITE_ARCHITECTURE.md` §3).
- Mensajes de error orientados al usuario final.

## 8. Comandos

```bash
# Instalar/actualizar un addon (ajustar nombre)
odoo -d goxtech -i factusol_core --addons-path=addons,. --stop-after-init
odoo -d goxtech -u factusol_migrator --addons-path=addons,. --stop-after-init
# Tests de un addon
odoo -d goxtech --test-enable --test-tags=/factusol_core -i factusol_core --stop-after-init
pip install -r factusol_migrator/requirements.txt
```

## 9. Definition of Done (suite)

- [ ] Ambos addons instalan en Odoo **Community** limpio, dependen solo de CE + `factusol_core`.
- [ ] `factusol_core` aporta los campos/helpers que el migrador consume.
- [ ] Migrador end-to-end (4 pasos, multi-año, selectividad, idempotente, informe de fidelidad).
- [ ] Variantes talla/color creadas con el sistema **nativo** de Odoo.
- [ ] `factusol_migrator` es la App visible con identidad de marca "FactuSol Odoo by GoxTech".
- [ ] Tests en verde por módulo. README de instalación para usuario no técnico.

## 10. Guardarraíles de seguridad

- El `.accdb` es dato personal sensible: acceso restringido, opción de borrado, nunca loguear su contenido.
- Validar upload antes de procesar. Sin `eval`/`exec` (solo `safe_eval`). **Sin egress de red** en runtime.
