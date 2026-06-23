# ARCHITECTURE.md — FactuSol Odoo by GoxTech (2 módulos)

La solución son **dos módulos** de Odoo Community, nada más. El detalle del migrador está en `docs/SPEC_migrator.md`; el de la capa de compatibilidad en `docs/MODULE_core.md`; el esquema real en `docs/SCHEMA_CATALOG.md`.

---

## 1. Módulos

| Módulo | Rol | Depende de |
|---|---|---|
| **`factusol_core`** | Capa de compatibilidad: lógica de FactuSol **no nativa** en Odoo (numeración `TIPO-TIP-COD`, triple descuento por línea, régimen de IVA por documento + traducción de impuestos, tarifas por margen, campos puente). Base reutilizable. | `base`, `account`, `sale`, `purchase`, `stock` |
| **`factusol_migrator`** | App de migración: sube `.accdb` (una por año), selecciona qué importar, carga maestros/documentos/tesorería/config de forma idempotente y verificable. Es la **App** visible (marca "FactuSol Odoo by GoxTech"). | `factusol_core` |

```
factusol_core  ←  factusol_migrator (App, marca GoxTech)
```

**Orden de construcción (Claude Code):** `factusol_core` → `factusol_migrator`, cada uno por fases con tests en verde.

> Sin verticales ni App paraguas separada. Las **variantes talla/color** se migran con el sistema **nativo de variantes de Odoo** (`product.attribute` Talla/Color → `product.product`); no hay módulo de escala/matriz. La gestión de **obras** queda fuera (vive en otro proyecto de Odoo, no se toca aquí).

---

## 2. Qué de FactuSol NO es nativo en Odoo → dónde se implementa

| Lógica FactuSol | Origen (tablas) | ¿Nativo en Odoo CE? | Dónde |
|---|---|---|---|
| Numeración `TIPO-TIP-COD` por serie y ejercicio | `TIP*`/`COD*` | Parcial (secuencias) | `factusol_core` |
| **Triple descuento** en cascada por línea | `DT1/DT2/DT3` en `F_L*` | No (un solo `discount`) | `factusol_core` |
| **Régimen de IVA por documento** + 3 IVAs + exento + recargo equiv. | `TIV*`,`NETx/BASx`,`PREC*` | Parcial | `factusol_core` (+ l10n) |
| **Tarifas por margen** (precio = coste + margen) | `F_TAR`/`F_LTA`/`F_LTC` (`MAR*`) | No | `factusol_core` |
| Campos puente / códigos origen FactuSol | claves `COD*` | No | `factusol_core` |
| Variantes Talla/Color | `F_CE1`,`F_CE2`,`F_STC`,`F_EAC`,`F_LTC` | **Sí** (variantes nativas) | `factusol_migrator` (mapea a `product.attribute`) |

Regla: lo que Odoo CE trae bien (terceros, productos, **variantes**, facturas, stock, pagos) se **reutiliza**; solo se crea lo que falte → eso vive en `factusol_core`.

---

## 3. Estructura del repositorio

```
factusol-odoo-goxtech/
├── README.md
├── CLAUDE.md
├── LICENSE                  # LGPL-3
├── docs/                    # esta documentación
├── factusol_core/           # addon: compatibilidad
└── factusol_migrator/       # addon: ETL / App (marca GoxTech)
```
Cada addon: `__manifest__.py` (autor "GoxTech", `license="LGPL-3"`), `models/`, `views/`, `security/`, `tests/`, `static/description/` (icono+capturas). El `factusol_migrator` declara `application=True` y el nombre visible **"FactuSol Odoo by GoxTech"**.

---

## 4. Marca y licencia

Autor/Mantenedor: **GoxTech**. LGPL-3 en ambos addons. Sin dependencias propietarias ni servicios de pago. Publicable estilo OCA (tests, manifiestos correctos, capturas).
