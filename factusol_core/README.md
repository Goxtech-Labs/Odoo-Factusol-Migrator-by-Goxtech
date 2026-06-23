# FactuSol Core (capa de compatibilidad)

Parte de la suite **FactuSol Odoo by GoxTech**. Reproduce la lógica de FactuSol
que **no es nativa** en Odoo Community, como base reutilizable por
`factusol_migrator`. Se implementa como **mixins** sobre los modelos estándar,
sin romper su comportamiento nativo.

> Autor: **GoxTech** · Licencia: **LGPL-3** · Odoo Community 18.0

## Qué aporta

| Función | Dónde | Detalle |
|---|---|---|
| Numeración / referencia `TIPO-TIP-COD` | documentos | Campos puente `x_factusol_ref` (`FAC-1-000001`), `x_factusol_serie`, `x_factusol_code`, `x_factusol_year`. Odoo conserva su secuencia interna. |
| Triple descuento en cascada | líneas | `x_disc1/2/3` (%) → se combinan en el `discount` nativo: `1-(1-d1)(1-d2)(1-d3)`. Un solo descuento equivale al nativo. |
| Régimen de IVA por documento | documentos | `x_factusol_iva_regime` (Con IVA / Sin IVA / Intracomunitario / Export-Import) para guiar la posición fiscal. |
| Traducción de impuestos | `factusol.tax.map` | Tabla configurable: selector IVA origen (0=IVA1…3=Exento) → `account.tax`, por compañía y uso. Menú en **Contabilidad → Configuración**. |
| Tarifas por margen | helper | `price_from_margin(coste, margen, basis)` (`cost`=markup sobre coste, `price`=margen sobre PVP). |
| Campos puente / trazabilidad | `res.partner`, `product.*`, documentos | `x_factusol_code` para conciliar y re-migrar de forma idempotente. |
| Agente / comisión (básico) | documentos | `x_factusol_agent_code`, `x_factusol_commission_rate`; en facturas, `x_factusol_commission_amount` = base × %. |

## Helpers reutilizables

Funciones puras en `factusol_core/tools.py`, importables desde el migrador:

```python
from odoo.addons.factusol_core.tools import (
    format_doc_ref, combine_discounts, price_from_margin,
    dimension_xmlid, fact_xmlid,
)
```

También expuestas como métodos de modelo vía `factusol.helper.mixin`
(`self.env['factusol.helper.mixin'].fs_format_doc_ref(...)`), aptas para
`safe_eval`.

## Convención de External IDs (la consume el migrador)

- **Dimensiones** (maestros): `dimension_xmlid('cli', cod)` → `cli_<cod>` (**sin año**; se fusionan entre ejercicios).
- **Hechos / tesorería**: `fact_xmlid('fac', año, tip, cod)` → `fac_2026_1-000001` (**con año**; los códigos se reinician cada ejercicio).

## Instalación

```bash
# copiar a addons_path y:
odoo -d <db> -i factusol_core --stop-after-init
```

Depende de `base`, `account`, `sale`, `purchase`, `stock` (todo Community).

## Tests

```bash
odoo -d <db> --test-enable --test-tags=/factusol_core -i factusol_core --stop-after-init
```

Cubren: triple descuento (combinación y equivalencia con descuento único),
referencia `TIPO-TIP-COD` con distintos anchos, traducción de IVA
selector→`account.tax` con tabla configurable, y precio por margen.
