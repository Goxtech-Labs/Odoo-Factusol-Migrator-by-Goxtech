# MODULE_core.md — `factusol_core` (capa de compatibilidad)

Reproduce la lógica de FactuSol **no nativa** en Odoo Community, como base reutilizable por el migrador. Se implementa como **extensiones (mixins) de modelos estándar**, sin romper el comportamiento nativo.

**Depende:** `base`, `account`, `sale`, `purchase`, `stock`. **Autor:** GoxTech. **Licencia:** LGPL-3.

---

## 1. Numeración y referencia de documento `TIPO-TIP-COD`

- Campos puente en documentos (`account.move`, `sale.order`, `purchase.order`, `stock.picking`): `x_factusol_ref` (`FAC-1-000001`), `x_factusol_serie` (`TIP`), `x_factusol_code` (`COD`), `x_factusol_year` (ejercicio).
- Helper para construir la referencia: `format_doc_ref(tipo, tip, cod, mask_width)` → `"FAC-1-000001"` (cero-relleno según máscara).
- Mantiene la numeración original como referencia legible; Odoo conserva su propia secuencia interna.

## 2. Triple descuento por línea (no nativo)

- En las líneas (`sale.order.line`, `purchase.order.line`, `account.move.line`): campos `x_disc1`, `x_disc2`, `x_disc3` (%).
- Cálculo del descuento efectivo y volcado al `discount` nativo: `discount = (1-(1-d1/100)(1-d2/100)(1-d3/100))*100`.
- Visible en la vista de líneas; editable; recalcula importes. Compatible con el `discount` estándar (si solo hay uno, equivale).

## 3. Régimen de IVA por documento

- Campo `x_factusol_iva_regime` en documentos (`0 Con IVA / 1 Sin IVA / 2 Intracomunitario / 3 Exportación|Importación`) que ayuda a fijar la **posición fiscal** (`fiscal_position_id`).
- Soporte para documentos con **varios tipos de IVA + exento** (los `account.tax` por línea siguen siendo el mecanismo real; este campo guía la posición fiscal y la traducción).
- Helper de **traducción de impuestos** FactuSol→localización destino (`l10n_ar`/`l10n_es`), alimentado por la config (`F_CFG`). Tabla configurable `factusol.tax.map` (selector IVA origen → `account.tax`).

## 4. Tarifas por margen (no nativo)

- FactuSol calcula precio = coste + margen (`F_TAR.MARTAR`, `F_LTA.MARLTA`).
- `factusol_core` genera `product.pricelist` con reglas o precios fijos derivados, y un helper `price_from_margin(cost, margin)`.
- Permite reproducir tarifas basadas en margen sobre coste, además de precios fijos (`PRELTA`/`PRELTC`).

## 5. Campos puente y trazabilidad

- En `res.partner`, `product.template/product`, documentos: `x_factusol_code` (código origen), para conciliar y re-migrar.
- Convención de External IDs consumida por el migrador (dimensiones sin año, hechos con año — ver `docs/SCHEMA_CATALOG.md`).

## 6. Comisiones de agente (básico, opcional)

- Campo de agente/comercial en terceros y documentos; cálculo simple de comisión por documento. Solo si el cliente lo usa; CE no lo trae completo.

---

## Pruebas
- Triple descuento: combinación correcta y equivalencia con descuento único.
- Referencia `TIPO-TIP-COD` con distintos anchos de máscara.
- Traducción de IVA selector→`account.tax` con tabla configurable.
- Precio por margen.

## Definition of Done
- Instala en CE sin romper sale/purchase/account/stock nativos.
- Los campos y helpers están disponibles para que el migrador los use.
- Tests en verde.
