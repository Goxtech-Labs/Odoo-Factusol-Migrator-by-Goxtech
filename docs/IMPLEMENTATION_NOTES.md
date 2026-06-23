# IMPLEMENTATION_NOTES.md — estado de la implementación (v1)

Notas de la primera construcción de la suite (`factusol_core` + `factusol_migrator`)
por Claude Code. Registra **qué se hizo**, los **desvíos** respecto del spec y lo
que **falta verificar en un Odoo real** (esta máquina de desarrollo no tiene Odoo;
solo se verificó sintaxis, XML bien formado y la lógica pura).

## Verificado fuera de Odoo
- `python -m py_compile` de todo el Python (core + migrador): OK.
- Todos los `.xml` bien formados.
- Lógica pura probada con asserts: `factusol_core/tools.py` (triple descuento,
  `format_doc_ref`, `price_from_margin`, External IDs) y
  `factusol_migrator/tools` (`convert`, `schema`, `AccessReader`+`DictBackend`,
  `parse_company_year`).

## Pendiente de verificar en un CT (smoke-test)
```bash
odoo -d <db> -i factusol_core --stop-after-init
odoo -d <db> -i factusol_migrator --stop-after-init
odoo -d <db> --test-enable --test-tags=/factusol_core,/factusol_migrator \
     -i factusol_core,factusol_migrator --stop-after-init
pip install access-parser   # o pyaccdb, para leer .accdb real
```
Puntos sensibles a mirar en el install:
1. **xpaths de `factusol_core`** sobre las listas de líneas
   (`//field[@name='order_line']/list/field[@name='discount']`, idem
   `invoice_line_ids`): patrón estándar de Odoo 18, pero confirmarlo.
2. **`account.payment` / `action_post`** en tesorería: requiere diario de
   banco/caja con cuentas pendientes; si no, el pago queda en borrador (capturado).
3. **`stock.warehouse`** y `stock.quant._update_available_quantity`: API interna de
   stock; validar contra una base real.

## Desvíos respecto del spec (decisiones de ingeniería)
- **Catálogo y presets se siembran por `post_init_hook`** (`_seed_from_catalog` /
  `_seed_presets`) desde `tools/schema.py`, en vez de un `data/*.xml` gigante
  escrito a mano. La única fuente de verdad de nombres de campo es `schema.py`;
  los registros quedan editables en `factusol.table.profile` /
  `factusol.field.mapping` (siguen siendo "datos/perfiles", no lógica). El
  `default_field_profile.xml` del spec se reemplaza por el flag `include` (mínimos
  premarcados) sembrado desde el catálogo.
- **Localización fiscal**: default asumido **`l10n_ar`** (contexto del usuario).
  La tabla `factusol.tax.map` es agnóstica; F6 (`do_taxes`) busca el impuesto que ya
  exista por porcentaje y solo crea lo que falte. Decisión #1 de `DECISIONS.md`.
- **Remitos / entradas (`stock.picking`)**: se cargan en **borrador** (no se valida
  el stock histórico). El stock real entra como **inventario inicial** (`F_STO`/
  `F_STC` → `stock.quant`, solo último año). Evita generar movimientos de stock
  históricos inconsistentes.
- **Facturas**: se crean y se intenta `action_post` (estado final); si falla
  (cuentas/impuestos), quedan en **borrador** con aviso, sin abortar el run.
- **Cobros/pagos**: se importan **sueltos**; la **conciliación** es opcional
  (`perfil → options.reconcile`), default off (Decisión #8).
- **Idempotencia**: `ir.model.data` con módulo lógico **`__factusol__`**
  (xmlid determinista; reimportar no duplica).
- **Asíncrono (F5)**: el run hace `commit` por año (runs largos no bloquean la
  transacción entera); aún **no** hay cola `queue_job`/cron (fallback síncrono).
  Es el punto natural de mejora si aparecen volúmenes muy grandes.

## Soporte parcial (mejorable en v2)
- Tarifas por **variante** (`F_LTC`): se cargan `F_TAR`/`F_LTA` (tarifa principal →
  `list_price`; resto → `pricelist.item` por plantilla). `F_LTC` por variante: TODO.
- **Comisiones de agente**: campos puente + cálculo simple en factura; sin informe.
- **`F_SEC`** sin descripción → se usa el código como nombre (Decisión #6).
- **Formas de pago / bancos** (F6): creación básica (term al 100% inmediato; diario
  banco). Vencimientos múltiples/proporcionales de `F_FPA`: TODO.

## Mapa rápido del código
```
factusol_core/        capa de compatibilidad (mixins + factusol.tax.map + helpers)
factusol_migrator/
  tools/              convert · schema (catálogo) · access_reader (backends)
  models/             source · catalog · import_profile · staging · import_run
  models/transformers/ base · dimensions · documents · config_treasury · engine
  wizard/             asistente de 4 pasos
  tests/              convert · readers · schema · engine (2 años, DictBackend)
```
