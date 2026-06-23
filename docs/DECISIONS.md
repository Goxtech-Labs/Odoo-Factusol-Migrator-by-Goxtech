# DECISIONS.md — Decisiones abiertas

Confirmar con el responsable del proyecto. Solo la #1 bloquea código (y solo el módulo fiscal); el resto tiene valor por defecto razonable para no frenar el desarrollo.

| # | Decisión | Por defecto asumido | Impacto | Bloqueante |
|---|---|---|---|---|
| 1 | **Localización fiscal destino: `l10n_ar` (Argentina) vs `l10n_es`** | — (pendiente) | Define la **tabla de traducción de impuestos**. FactuSol trae modelo español (RE, IVA intracom.); el usuario opera en Argentina. | **Sí** (solo F6) |
| 2 | Versión Odoo Community primaria | 18.0 LTS (portar a 17/19) | Manifiesto y APIs menores | No |
| 3 | Tarifas: ¿una (→`list_price`) o varias (→`pricelist`)? | Principal→`list_price`; resto→`pricelist` | Plano 1 (precios) | No |
| 4 | Profundidad histórica de documentos | Los años que el usuario seleccione | Volumen Etapa 2 | No |
| 5 | Triple descuento por línea | Combinar en `discount` único | Conversión líneas | No |
| 6 | Nombre de secciones (`F_SEC` sin descripción) | Usar el código como nombre | Plano 1 (categorías) | No |
| 7 | `F_RET`: ¿retiradas de caja TPV o retenciones fiscales? | Tesorería/caja (no fiscal) | Clasificación 2b | No |
| 8 | Cobros/pagos: ¿sueltos o conciliados contra facturas? | Importar sueltos; conciliación opcional | Plano 2b | No |
| 9 | Anticipos: ¿`account.payment` no conciliado o nota de crédito? | `account.payment` (saldo a favor) | Plano 2b | No |
| 10 | Dimensiones que cambian entre años (p. ej. domicilio) | Gana el **año más reciente** | Fusión multi-año | No |
| 11 | Detección de artículos con variante | Presencia en `F_STC`/`F_EAC` | Plano 1 (variantes nativas) | No |
| 12 | Marca/nombre de la App | "FactuSol Odoo by GoxTech" (autor GoxTech), sobre `factusol_migrator` | Branding | No |
| 13 | Alcance de módulos | **Solo `factusol_core` + `factusol_migrator`**. Sin verticales ni App paraguas. Obras fuera de alcance (otro proyecto). Variantes talla/color nativas. | Alcance | No |
