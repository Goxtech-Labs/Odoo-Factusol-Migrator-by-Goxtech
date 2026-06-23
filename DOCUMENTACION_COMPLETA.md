# FactuSol Odoo by GoxTech — DOCUMENTACIÓN COMPLETA

_Documento consolidado · generado 2026-06-22._

Reúne, en orden de lectura, toda la documentación del proyecto para Claude Code. Los mismos contenidos están en archivos separados dentro del repositorio (`CLAUDE.md`, `README.md`, `docs/`), que es lo que se entrega a Claude Code; este archivo es la versión unificada para lectura/revisión.

## Índice

1. **Presentación del proyecto**  ·  `README.md`
2. **Manual operativo del agente (entrypoint)**  ·  `CLAUDE.md`
3. **Arquitectura (2 módulos)**  ·  `docs/SUITE_ARCHITECTURE.md`
4. **Módulo factusol_core (compatibilidad)**  ·  `docs/MODULE_core.md`
5. **Especificación del migrador (factusol_migrator)**  ·  `docs/SPEC_migrator.md`
6. **Catálogo del esquema real de FactuSol**  ·  `docs/SCHEMA_CATALOG.md`
7. **Decisiones abiertas**  ·  `docs/DECISIONS.md`
8. **Licencia**  ·  `LICENSE`

---



<a id='sec1'></a>

# 1. Presentación del proyecto

> Archivo de origen: `README.md`

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


---



<a id='sec2'></a>

# 2. Manual operativo del agente (entrypoint)

> Archivo de origen: `CLAUDE.md`

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


---



<a id='sec3'></a>

# 3. Arquitectura (2 módulos)

> Archivo de origen: `docs/SUITE_ARCHITECTURE.md`

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


---



<a id='sec4'></a>

# 4. Módulo factusol_core (compatibilidad)

> Archivo de origen: `docs/MODULE_core.md`

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


---



<a id='sec5'></a>

# 5. Especificación del migrador (factusol_migrator)

> Archivo de origen: `docs/SPEC_migrator.md`

# SPEC.md — Especificación técnica `factusol_migrator`

> Módulo de **FactuSol Odoo by GoxTech** (ver `docs/SUITE_ARCHITECTURE.md`). **Depende de `factusol_core`** (capa de compatibilidad). Es la **App** visible. Autor: GoxTech · LGPL-3. Las variantes talla/color se migran con el sistema **nativo** de variantes de Odoo.

Documento maestro y autocontenido para Claude Code. Cubre los seis ejes: **técnico, seguridad, infraestructura, fidelidad de datos, conversión e interactividad**. El catálogo exhaustivo de tablas/campos está en `docs/SCHEMA_CATALOG.md`; las decisiones abiertas, en `docs/DECISIONS.md`.

---

## 1. Visión y principios

Migrador autónomo FactuSol → **Odoo Community** autohospedado, open source y gratuito. Un usuario sin perfil técnico completa cuatro pasos —**subir** las bases `.accdb` (una por año), **seleccionar** qué importar, **migrar**, **verificar**— y obtiene en Odoo lo esencial de FactuSol.

Principios (ver `CLAUDE.md` §2): Community-only · LGPL-3 · self-hosted · sin Windows · sin binarios obligatorios · sin telemetría · **selectividad total** · idempotente · **multi-ejercicio** · fidelidad verificable.

---

## 2. Alcance funcional — planos y etapas

La migración se organiza en **planos seleccionables**, cargados en orden de dependencia:

| Plano / Etapa | Contenido | Tablas FactuSol | Destino Odoo |
|---|---|---|---|
| **0 — Configuración** (opt-in) | empresa, tipos de IVA/RE, formas de pago, bancos | `F_EMP`, `F_CFG`, `F_FPA`, `F_BAN` | `res.company`, `account.tax`, `account.payment.term`, `account.journal` |
| **1 — Dimensiones** | almacenes, secciones, familias, clientes, proveedores, artículos, tallas/colores, tarifas, stock | `F_ALM`,`F_SEC`,`F_FAM`,`F_CLI`,`F_PRO`,`F_ART`,`F_CE1`,`F_CE2`,`F_TAR`/`F_LTA`/`F_LTC`,`F_STO`,`F_STC` | `stock.warehouse`, `product.category`, `res.partner`, `product.template/product`, `product.attribute`, `product.pricelist`, `stock.quant` |
| **2 — Hechos comerciales** | Compras: pedido→entrada→factura. Ventas: presupuesto→pedido→albarán→factura | Compras `F_PPR`→`F_ENT`→`F_FRE`; Ventas `F_PRE`→`F_PCL`→`F_ALB`→`F_FAC` (+ líneas `F_L*`) | `purchase.order`, `stock.picking`, `account.move`, `sale.order` |
| **2b — Tesorería** (opt-in) | cobros, pagos, anticipos | `F_COB`(+`F_LCO`),`F_PAG`,`F_ANT`,`F_ANP` | `account.payment` (+ conciliación opcional) |

Todos los planos, entidades y campos son **individualmente seleccionables** (§5). El mapeo campo a campo está en `docs/SCHEMA_CATALOG.md`.

---

## 3. Lectura de Access (puro Python)

Backends tras `AccessReader` con degradación automática: **`pyaccdb`** (primario, lazy, soporta cifrado) → **`access-parser`** (fallback) → **`mdbtools`** (opcional). Ver `CLAUDE.md` §5. La introspección (`list_tables`/`list_fields` con nombre+tipo+tamaño+descripción) alimenta el asistente de selección.

## 3.1. Multi-ejercicio y multi-empresa (UN `.accdb` POR AÑO)

FactuSol guarda **una base por ejercicio**; una migración real consume **varios `.accdb`** y el usuario elige **uno o varios años**. Estructural, no opcional.

**Identificación empresa+año:** el nombre del fichero codifica `EEEAAAA.accdb` (ejemplo real `0022026.accdb` → empresa `002`, año `2026`); fuente autoritativa de respaldo `F_EMP`/`EJEEMP`. Cada `factusol.source` = un fichero = una empresa+año.

**Estrategia de claves (CRÍTICA para fidelidad):** los códigos de documento se reinician cada año.

| Plano | External ID | Motivo |
|---|---|---|
| **Dimensiones** | `cli_<código>` (**sin año**) | mismo código = mismo registro en todos los años → fusiona, no duplica |
| **Hechos / Tesorería** | `fac_<ejercicio>_<TIP>-<COD>` (**con año**), p. ej. `fac_2026_1-000001` | `CODFAC` se reinicia; sin año, `1-000001`/2024 colisiona con `1-000001`/2025 |

**Consolidación multi-año:**
- **Dimensiones — fusión por código:** maestro repetido se actualiza (idempotencia). Precedencia configurable; **por defecto gana el año más reciente**; registrar cambios.
- **Documentos — unión por año:** se cargan los de cada año elegido, con clave por ejercicio.
- **Stock — solo el último año seleccionado** (foto, no acumulable; sumar años duplicaría).
- **Orden:** años en cronológico ascendente; dentro de cada año, planos 0→1→2→2b.

Los N ficheros-año **colapsan en una sola base Odoo** con transacciones fechadas; varias empresas (EEE) → varias `res.company`. El informe de fidelidad desglosa **por año**.

---

## 4. Selección mínima de campos (manifiesto)

El módulo viene con un **perfil mínimo por defecto**: solo clave + datos imprescindibles. Todo lo demás es **opt-in**. Filosofía: *lo justo y necesario.*

Ejemplos de mínimos (catálogo completo en `docs/SCHEMA_CATALOG.md`):
- **Tercero** (`F_CLI`/`F_PRO`): código, nombre, NIF, domicilio, población, CP, provincia.
- **Artículo** (`F_ART`): código, descripción, costo, familia, cód. barras. *(El precio de venta está en tarifas, no en `F_ART`.)*
- **Stock** (`F_STO`/`F_STC`): artículo, almacén, stock actual (+ talla/color si hay variante).
- **Documento** (cabecera): serie, código, fecha, tercero, almacén, estado, total. **Línea**: artículo, cantidad, precio, IVA (selector), talla/color.

Implementación: el manifiesto se carga en `data/default_field_profile.xml`. Todo campo no listado entra como `include=False` (visible, desmarcado). La UI muestra por defecto solo los incluidos, con toggle "Mostrar todos".

---

## 5. Selectividad total y perfiles de importación (requisito rector)

**Elegir qué importar y qué no es el núcleo del producto.** Cada cliente migra con distinto criterio.

**Tres niveles** de conmutadores on/off en cascada:
```
PLANO     (Configuración · Dimensiones · Hechos · Tesorería)
 └ ENTIDAD (Clientes · Proveedores · Artículos · Cobros · Anticipos · …)
    └ CAMPO (mínimos premarcados; resto opt-in)
```
Desactivar un nivel desactiva sus hijos; activar un hecho **avisa** (no obliga) sobre las dimensiones que necesita. El usuario decide siempre.

**Perfiles** (`factusol.import.profile` + `.line`): selección + opciones guardadas y reutilizables.
```python
# factusol.import.profile
name, description, is_preset
line_ids -> factusol.import.profile.line(entity, enabled, field_whitelist, options:Json)
```
**Presets de fábrica** (clonables, no editables):

| Preset | Incluye |
|---|---|
| **Mínimo** | Dimensiones básicas + stock |
| **Comercial** | Mínimo + documentos de ventas y compras |
| **Contable completo** | Comercial + Configuración fiscal + Tesorería (conciliación opcional) |
| **Personalizado** | Vacío; el usuario arma su criterio |

Un perfil se puede **exportar/importar** (registro de datos) para compartir criterios entre instalaciones. El dry-run y la migración respetan el perfil activo. El manifiesto de campos mínimos (§4) es el perfil del preset "Mínimo".

---

## 6. Arquitectura técnica

### 6.1. Modelos
- `factusol.source` — fichero `.accdb` (= empresa+año), `company_code`, `fiscal_year` (detectados), backend, estado.
- `factusol.table.profile` — tabla, plano, modelo Odoo destino, `load_order`, activo.
- `factusol.field.mapping` — campo origen→destino, transformación, `is_key`, `include`.
- `factusol.import.profile` (+ `.line`) — perfil de selección reutilizable (§5).
- `factusol.staging.row` — fila cruda (JSON) por lote, estado.
- `factusol.import.run` — ejecución sobre **uno o varios** `source` (años) hacia una `res.company`; contadores por año; informe de fidelidad.
- `factusol.import.log` — error por fila: tabla, clave, campo, mensaje, payload.

### 6.2. Transformador genérico de documentos
**Identidad y unión (regla fundamental):** todo documento se identifica por `TIP` (serie) + `COD` (código). El número legible es `<TIPO>-<TIP>-<COD>` con el prefijo de tipo (`FAC`,`FRE`,`ALB`,`ENT`,`PPR`,`PCL`,`PRE`) y el cero-relleno de la máscara `[F=…]` (p. ej. `FAC-1-000001`, `FRE-1-000001`); el prefijo evita ambigüedad entre tipos. La cabecera y sus líneas se **unen por `(TIP, COD)`** y las líneas se **ordenan por `POS`**. El External ID multi-año es `<doc>_<ejercicio>_<TIP>-<COD>`.

Las siete tablas de líneas (`F_LFA`,`F_LFR`,`F_LAL`,`F_LEN`,`F_LPP`,`F_LPC`,`F_LPS`) comparten **estructura idéntica** y este mismo patrón de unión. Implementar **un solo** `DocumentTransformer` parametrizado por (tabla cabecera, tabla de líneas, modelo/`move_type` destino, campo de referencia): para cada cabecera agrupa sus líneas por `(TIP,COD)` ordenadas por `POS`, y resuelve tercero, impuestos y variantes con la misma lógica. Guarda `TIP-COD` como referencia legible en Odoo. Evita siete transformadores casi iguales.

### 6.3. Pipeline ETL
`Extract` (reader, por lotes) → `Stage` (`staging.row`) → `Transform+Validate` (conversión + resolución de FK) → `Load` (upsert idempotente; orden de planos 0→1→2→2b; años ascendente). Idempotencia vía `ir.model.data` con xmlid determinista según §3.1.

---

## 7. Interactividad / UX (autogestión)

Asistente lineal de **4 pasos**, lenguaje no técnico:

1. **Subir base(s)**: arrastrar **uno o varios** `.accdb`; validación inmediata; contraseña si están cifrados; muestra **empresa y año detectados** de cada fichero.
2. **Elegir qué migrar**:
   - **Años**: casillas con ejercicios detectados → uno, varios o todos. Varias empresas → elegir destino `res.company`.
   - **Entidades** con interruptores on/off (nombres amigables: "Clientes", no `F_CLI`).
   - **Campos** con mínimos premarcados + toggle "Mostrar todos".
   - Aplicar/guardar un **perfil** (preset o personalizado).
3. **Previsualizar y validar** (dry-run): ejecuta extracción+transformación **sin escribir**; muestra conteos por entidad/año, muestra de filas convertidas y **avisos** (FK faltantes, NIF inválidos, decimales raros). El usuario corrige y reintenta.
4. **Migrar y verificar**: carga real idempotente, progreso, ejecución en background si el volumen es grande; al terminar, **informe de fidelidad** descargable + incidencias con acciones sugeridas.

Transversal: reanudable/repetible (re-correr solo una etapa o solo los `failed`); mensajes accionables ("No se migraron 4 facturas porque falta su cliente. ¿Migrar clientes primero?"); sin callejones sin salida; i18n (es/en mínimo).

---

## 8. Fidelidad de datos

**Garantías:** idempotencia por External ID; integridad referencial (hecho sin dimensión → `failed` con motivo); trazabilidad (cada registro Odoo guarda la clave origen `serie+código+año`).

**Informe de fidelidad** (obligatorio al cerrar un run), **por año**: por entidad, `registros_origen · migrados_ok · fallidos · omitidos`; para documentos, **cuadre de importes** (suma `TOT*`/`BAS*` origen vs Odoo, con tolerancia ±0,01). Descuadres en rojo con enlace a incidencias.

**Validaciones por registro:** tipos, obligatorios, formato email/NIF (aviso, no bloqueo), resolución de FK, rango de fechas, decimales. Todo fallo → `import.log` con payload para reproceso.

---

## 9. Conversión (reglas técnicas)

| Tema | Regla |
|---|---|
| **Codificación** | Origen **cp1252** → UTF-8 en extracción (verificar `Ñ`, acentos, `€`). |
| **Decimales** | Coma española → punto (`1.234,56` → `1234.56`). |
| **Fechas** | `Fecha con hora` (8 bytes) → `date`/`datetime`; tratar nulas/`00/00/0000`. |
| **IVA por línea** | El campo `IVA*` es **selector** `0=IVA1,1=IVA2,2=IVA3,3=Exento`, **no** el %. Los porcentajes están en config (`F_CFG`) y la cabecera admite hasta 3 IVAs + exento (`NETx`/`BASx`/`TIVAx`). Resolver a `account.tax`. |
| **Triple descuento** | Línea con `DT1`,`DT2`,`DT3` en cascada → combinar en `discount` único: `1-(1-d1)(1-d2)(1-d3)`. |
| **Variantes** | Resolver `CE1`(talla)/`CE2`(color) → `product.product`. Detectar artículos con variante por presencia en `F_STC`/`F_EAC`. |
| **NIF/CIF** | Normalizar (mayúsculas, sin espacios); inválido → aviso, no bloqueo. |
| **Numeración** | Preservar `serie+código+año` origen en campo de referencia; Odoo asigna su secuencia. |
| **Documentos históricos** | Cargar en **estado final** (no re-ejecutar el flujo presupuesto→pedido→albarán→factura). |
| **Localización fiscal** | **Decisión bloqueante** (`docs/DECISIONS.md`): `l10n_ar` vs `l10n_es`. Implementar **tabla de traducción de impuestos** configurable FactuSol→destino, alimentada por `F_CFG`. |

---

## 10. Seguridad

**Datos personales:** el `.accdb` contiene NIF/domicilio/contacto. Acceso restringido al grupo **Migrador FactuSol / Manager**; **nunca** loguear su contenido; opción de **borrar** el `.accdb` y la staging tras migrar; almacenado como adjunto privado (cifrado en reposo a nivel filestore/OS si se desea — documentar en README).

**Superficie de ataque:** validar upload (extensión, tamaño máximo configurable, que el reader lo abre como Access) antes de procesar; **sin `eval`/`exec`** sobre datos del fichero (transformaciones "python" solo vía **`safe_eval`** de Odoo); **sin egress de red** en runtime; permisos finos en `ir.model.access.csv`.

**Robustez del parser:** procesar de forma defensiva (límites de memoria/tiempo por tabla, captura de excepciones, degradación de backend); nunca confiar en offsets/tamaños del propio fichero sin verificar.

---

## 11. Infraestructura

- **Destino:** Odoo **Community** autohospedado (bare-metal, VM o Docker). Sin Odoo.sh ni Enterprise.
- **Instalación:** copiar a `addons/`, `pip install -r requirements.txt`, instalar desde Apps. README para no técnicos, incluida la opción **Docker** (imagen oficial `odoo:18` + addons montados + deps).
- **Dependencias:** en `__manifest__.py` (`external_dependencies.python=["pyaccdb"]`, …) y `requirements.txt`. Mínimas y open source.
- **Rendimiento:** extracción/carga por lotes (1.000–5.000); `with_context(tracking_disable=True, mail_create_nolog=True)` en carga masiva; commits por lote en runs largos.
- **Asíncrono:** volúmenes grandes → cron/cola (`queue_job` de OCA **opcional**; fallback a cron propio). La UI no se bloquea.
- **Requisitos mínimos** documentados (RAM/disco según tamaño `.accdb`); por eso `pyaccdb` (lazy) es primario.

---

## 12. Pruebas

- **`tests/fixtures/`:** `.accdb` sintético mínimo (pocas filas por tabla `F_*` clave) + CSV/JSON esperados. Incluir **dos años** para probar multi-ejercicio. No usar datos reales de cliente.
- **`test_readers.py`:** cada backend lee tablas/campos/filas; degradación de backend funciona.
- **`test_transformers.py`:** conversión campo a campo (cp1252, coma decimal, fecha nula, IVA selector→tax, triple descuento, variante talla/color, NIF) y **agrupación cabecera↔línea por `(TIP,COD)` con orden por `POS`** y número `<TIPO>-<TIP>-<COD>` correcto (p. ej. `FAC-1-000001`).
- **`test_fidelity.py`:** conteos origen==ok+failed; cuadre de importes; **idempotencia**; FK faltante → `failed`; **multi-año** (claves con/sin año; stock del último año; fusión de dimensiones).
- Ejecutar con `--test-tags=/factusol_migrator`. Verde obligatorio por fase.

---

## 13. Roadmap por fases (Definition of Done)

| Fase | Entregable | DoD |
|---|---|---|
| **F0 — Andamiaje** | módulo instalable en CE, modelos vacíos, menús, grupo de seguridad | Instala/actualiza sin error en Odoo CE limpio |
| **F1 — Lectura + multi-año** | `AccessReader` + `pyaccdb`/`access-parser`, introspección, detección empresa+año | Lee `.accdb` real sin mdbtools; detecta años; degradación de backend |
| **F2 — Selección + mínimos** | wizards subir/seleccionar (incl. años), manifiesto, dry-run | Usuario elige años/entidades/campos desde UI; preview sin escribir |
| **F2.5 — Selectividad** | `factusol.import.profile` + presets + UI 3 niveles + export/import | Crear/clonar/exportar perfil; dry-run respeta perfil |
| **F3 — Dimensiones** | transformadores de maestros + carga idempotente + fusión multi-año | Migra maestros/variantes/tarifas/stock; idempotente; stock del último año |
| **F4 — Hechos** | `DocumentTransformer` genérico, ambos circuitos, claves por año | Migra compras y ventas con FK resueltas; estados mapeados |
| **F5 — Fidelidad + robustez** | informe por año, logs, reproceso, async, i18n | Cuadre OK; reproceso de `failed`; tests en verde; README no técnico |
| **F6 — Config fiscal** | `F_EMP`/`F_CFG`/`F_FPA`/`F_BAN` → company/tax/term/journal reutilizando `l10n_*` | No duplica impuestos; resuelve selector IVA |
| **F7 — Tesorería** | cobros/pagos/anticipos → `account.payment`; conciliación opcional | Importa pagos; concilia contra facturas migradas cuando se active |

---

## 14. Licencia y gobernanza open source

- **LGPL-3** en `LICENSE` y `__manifest__.py` (`"license": "LGPL-3"`).
- `README.md` del módulo: qué hace, requisitos, instalación (incl. Docker), guía de 4 pasos, limitaciones, cómo contribuir.
- Sin dependencias propietarias ni servicios de pago en ninguna ruta de código.
- Estructura estándar publicable (GitHub / OCA-style): tests, manifiesto correcto, capturas en `static/description/`.


---



<a id='sec6'></a>

# 6. Catálogo del esquema real de FactuSol

> Archivo de origen: `docs/SCHEMA_CATALOG.md`

# SCHEMA_CATALOG.md — Catálogo del esquema real de FactuSol

Referencia de datos para los transformadores. **No inventar nombres de campo**: usar estos, extraídos del análisis de una base real (`0022026.accdb`, 170 tablas). El migrador igualmente descubre el esquema en runtime; este catálogo fija claves, campos mínimos y mapeo a Odoo.

**Convención:** tablas `F_<COD>`; columnas `<CAMPO><COD>` (p. ej. `NOFCLI` = Nombre Fiscal de `F_CLI`). Texto en **cp1252**; decimales con **coma**. Clave de documento = `TIP` (serie, 1 car.) + `COD` (código). Clave de línea = `TIP`+`COD`+`POS`.

**Número de documento** = `<TIPO>-<TIP>-<COD>`: prefijo de tipo de documento + serie + código con el cero-relleno de la máscara `[F=…]` del campo `COD`. Ejemplos: `FAC-1-000001` (factura venta), `FRE-1-000001` (factura recibida), `ALB-1-000001`, `ENT-1-000001`, `PPR-1-000001`, `PCL-1-000001`, `PRE-1-000001`. El prefijo evita ambigüedad entre tipos (una factura emitida y una recibida pueden compartir `1-000001`). Es la identidad legible del documento; la **unión cabecera↔línea** sigue siendo por `(TIP, COD)` dentro de cada par de tablas.

Prefijos de tipo: `FAC`,`FRE`,`ALB`,`ENT`,`PPR`,`PCL`,`PRE` (= código de la tabla cabecera).

Leyenda External ID: dimensiones **sin año** (`cli_<cod>`); hechos/tesorería **con año** (`fac_<eje>_<TIP>-<COD>`, p. ej. `fac_2026_1-000001`).

---

## PLANO 0 — CONFIGURACIÓN (opt-in)

| Entidad | Tabla | Clave / campos mínimos | Destino Odoo | Nota |
|---|---|---|---|---|
| Empresa | `F_EMP` | `CODEMP`, `DENEMP` (razón social), `DOMEMP`,`POBEMP`,`CPOEMP`,`PROEMP`, ejercicios `EJE*EMP` | `res.company` | multi-ejercicio aquí |
| Tipos de IVA / RE | `F_CFG` | `CODCFG` (=`IVA1/IVA2/IVA3…`), `NUMCFG` (%) | `account.tax` | clave/valor; **base de la traducción fiscal** |
| Formas de pago | `F_FPA` | `CODFPA`, `VENFPA` (nº venc.), `DIA1..6FPA` (días), `PRO2/4/6FPA` (proporciones), `CCOFPA`/`CPAFPA` (contrapartidas) | `account.payment.term` (+ líneas) | vencimientos múltiples/proporcionales |
| Bancos / cuentas | `F_BAN` | `CODBAN`, `NOMBAN`, `ENTBAN`/`OFIBAN`/`DCOBAN`/`CUEBAN` (CCC), `CCOBAN` (cta. contable), `TCUBAN` (tipo) | `account.journal` (banco) + `res.bank`/`res.partner.bank` | — |

> Los **porcentajes de IVA no están por fila**: el selector de línea (`0=IVA1,1=IVA2,2=IVA3,3=Exento`) se resuelve contra `F_CFG`. Criterio: **reutilizar la localización destino** (`l10n_ar`/`l10n_es`) y crear solo lo que falte.

---

## PLANO 1 — DIMENSIONES

### Almacén — `F_ALM` → `stock.warehouse` + `stock.location`
Clave `CODALM`. Mín.: `CODALM`, `DIRALM` (domicilio), `POBALM`. (Opt-in: `CPOALM`,`PROALM`,`TELALM`,`EMAALM`.)

### Sección — `F_SEC` → `product.category` (raíz)
Clave `CODSEC`. ⚠️ **Sin campo descripción** (solo código + flags web): usar el código como nombre o cruzar con otra fuente (confirmar).

### Familia — `F_FAM` → `product.category` (hija de sección)
Clave `CODFAM`. Mín.: `CODFAM`, `DESFAM` (nombre), `SECFAM` (padre→`sec_<>`). Opt-in: `CUEFAM` (cta. ventas), `CUCFAM` (cta. compras).

### Cliente — `F_CLI` → `res.partner` (customer_rank=1)
Clave `CODCLI`. Mín.: `CODCLI`, `NOFCLI` (nombre fiscal), `NIFCLI` (NIF→`vat`), `DOMCLI` (domicilio), `POBCLI`,`CPOCLI`,`PROCLI`.
Opt-in frecuente: `NOCCLI` (nombre comercial), `TELCLI`/`MOVCLI`, `EMACLI`, `WEBCLI`, `PAICLI`, `FPACLI` (forma de pago), `AGECLI` (agente), `TARCLI` (tarifa→pricelist), `DT1/2/3CLI` (descuentos), `IVACLI` (régimen→posición fiscal), `REQCLI` (recargo equiv.), `SWFCLI` (IBAN), `NO1..5CLI`+`TF/EM` (contactos), `PGCCLI` (cta. cliente 430).

### Proveedor — `F_PRO` → `res.partner` (supplier_rank=1)
Clave `CODPRO`. Mín.: `CODPRO`, `NOFPRO`, `NIFPRO`, `DOMPRO`, `POBPRO`,`CPOPRO`,`PROPRO`.
Opt-in: `FPAPRO`,`IVAPRO`,`CCEPRO` (cta. compras),`SWFPRO` (IBAN),`EMAPRO`,`NO1..5PRO`.

### Artículo — `F_ART` → `product.template`/`product.product`
Clave `CODART`. Mín.: `CODART` (→`default_code`), `DESART` (→`name`), `PCOART` (costo→`standard_price`), `FAMART` (→`categ_id`), `EANART` (→`barcode`).
Opt-in: `TIVART` (selector IVA→`taxes_id`), `NCCART`/`CUCART` (cuentas), `PHAART`/`REFART` (proveedor→`seller_ids`), `STOART` (controla stock→`is_storable`), `DSCART` (descatalogado→`active=False`), `UMEART` (→`uom_id`).
> ⚠️ `F_ART` **no tiene precio de venta**; está en tarifas (ver abajo).

### Tallas/Colores → atributos de variante
| FactuSol | Significado | Odoo |
|---|---|---|
| `F_CE1` (`CODCE1`) | Talla (escala 1) | `product.attribute` "Talla" + `.value` |
| `F_CE2` (`CODCE2`,`DESCE2`) | Color (escala 2) | `product.attribute` "Color" + `.value` |
| `F_EAC` (`ARTEAC`,`EANEAC`,`CE1EAC`,`CE2EAC`) | EAN por artículo+talla+color | `barcode` de cada `product.product` |

Procedimiento: cargar valores (`F_CE1`/`F_CE2`) → detectar artículos con variante (presencia en `F_STC`/`F_EAC`) → crear `product.template.attribute.line` (Odoo genera variantes) → `barcode` por variante desde `F_EAC`.

### Tarifas (precios de venta) → `product.pricelist`
| Tabla | Campos | Odoo |
|---|---|---|
| `F_TAR` | `CODTAR`,`MARTAR`,`IVATAR` | `product.pricelist` (cabecera) |
| `F_LTA` | `TARLTA`,`ARTLTA`,`PRELTA` (precio) | `pricelist.item` por producto |
| `F_LTC` | `TARLTC`,`CE1LTC`,`CE2LTC`,`PRELTC` | `pricelist.item` por variante |

Estrategia: tarifa principal → `list_price`; tarifas adicionales → `pricelist` (confirmar nº de tarifas).

### Stock inicial → `stock.quant`
| Origen | Cuándo | Campos | Destino |
|---|---|---|---|
| `F_STO` | artículo **sin** variantes | `ARTSTO`,`ALMSTO`,`ACTSTO` (actual) | `stock.quant` sobre variante única |
| `F_STC` | artículo **con** variantes | `ARTSTC`,`ALMSTC`,`CE1STC`,`CE2STC`,`ACTSTC` | `stock.quant` por `product.product` |

Regla: con variantes → solo `F_STC`; sin variantes → solo `F_STO`. Carga como **inventario inicial**, del **último año** seleccionado.

---

## PLANO 2 — HECHOS COMERCIALES

### Identidad del documento y enlace cabecera↔línea (FUNDAMENTAL)

**Todos** los documentos se identifican por `TIP` (serie, 1 car.) + `COD` (código). El transformador debe:

1. **Número de documento** = `f"{TIPO}-{TIP}-{COD:0{ancho}d}"` donde `TIPO` es el código de la tabla cabecera (`FAC`,`FRE`,`ALB`,`ENT`,`PPR`,`PCL`,`PRE`) y `ancho` viene de la máscara `[F=…]` del campo `COD` (habitual 6 → `FAC-1-000001`). Guardarlo como referencia legible en Odoo.
2. **Unir cabecera y líneas por `(TIP, COD)`** y **ordenar las líneas por `POS`**. Ejemplo: una fila de `F_FAC` con `TIPFAC='1'`, `CODFAC=1` agrupa todas las filas de `F_LFA` con `TIPLFA='1'` y `CODLFA=1` (líneas `POSLFA` 1,2,3…). **Idéntico en los 7 documentos** (`FAC`/`LFA`, `FRE`/`LFR`, `ALB`/`LAL`, `ENT`/`LEN`, `PPR`/`LPP`, `PCL`/`LPC`, `PRE`/`LPS`).
3. **External ID** (multi-año) = `<doc>_<ejercicio>_<TIP>-<COD>` (p. ej. `fac_2026_1-000001`). El ejercicio evita la colisión entre años (la factura `1-000001` existe en cada año). La **referencia legible** que ve el usuario lleva además el prefijo de tipo: `FAC-1-000001`.

| Documento | Cabecera (clave) | Línea (clave de unión + orden) | Nº / referencia legible |
|---|---|---|---|
| Factura venta | `F_FAC` (`TIPFAC`,`CODFAC`) | `F_LFA` (`TIPLFA`,`CODLFA`,`POSLFA`) | `FAC-1-000001` → `name`/`ref` |
| Factura recibida | `F_FRE` (`TIPFRE`,`CODFRE`) | `F_LFR` (`TIPLFR`,`CODLFR`,`POSLFR`) | `FRE-1-000001` → `ref` |
| Albarán/Remito | `F_ALB` (`TIPALB`,`CODALB`) | `F_LAL` (`TIPLAL`,`CODLAL`,`POSLAL`) | `ALB-1-000001` → `origin`/`name` |
| Entrada compra | `F_ENT` (`TIPENT`,`CODENT`) | `F_LEN` (`TIPLEN`,`CODLEN`,`POSLEN`) | `ENT-1-000001` → `origin`/`name` |
| Pedido proveedor | `F_PPR` (`TIPPPR`,`CODPPR`) | `F_LPP` (`TIPLPP`,`CODLPP`,`POSLPP`) | `PPR-1-000001` → `name`/`partner_ref` |
| Pedido cliente | `F_PCL` (`TIPPCL`,`CODPCL`) | `F_LPC` (`TIPLPC`,`CODLPC`,`POSLPC`) | `PCL-1-000001` → `name`/`client_order_ref` |
| Presupuesto | `F_PRE` (`TIPPRE`,`CODPRE`) | `F_LPS` (`TIPLPS`,`CODLPS`,`POSLPS`) | `PRE-1-000001` → `name` |

### Estructura común
**Cabeceras** comparten: `TIP*` (serie), `COD*` (código), `FEC*` (fecha), tercero (`CLI*`/`PRO*`), `ALM*` (almacén), `TIV*` (régimen IVA), `FOP*` (forma de pago), `EST*` (estado), `NETx`/`BASx`/`TOT*` (importes), `VEN*` (vencimientos), `OB1/2*` (observaciones).

**Líneas** (`F_L*`) — estructura **idéntica** en los 7 documentos:

| Campo línea | Odoo | Nota |
|---|---|---|
| `POS*` | `sequence` | — |
| `ART*` | `product_id` → `art_<cod>` | FK artículo |
| `CAN*` | `quantity`/`product_uom_qty` | cantidad |
| `PRE*` | `price_unit` | precio |
| `DT1*`,`DT2*`,`DT3*` | `discount` | triple dto. → combinar |
| `IVA*` | `tax_ids` | **selector** 0/1/2/3 → impuesto real |
| `CE1*`,`CE2*` | resolución de variante | talla/color |
| `TOT*` | control/cuadre | recalculado por Odoo |

### Circuito COMPRAS
| Documento | Cabecera | Líneas | Odoo | Estado origen |
|---|---|---|---|---|
| Pedido a proveedor | `F_PPR` (`PROPPR`,`FECPPR`,`ALMPPR`) | `F_LPP` | `purchase.order` (+line) | `ESTPPR` 0 Pte recibir/1 Parcial/2 Recibido |
| Entrada / recepción | `F_ENT` (`PROENT`,`FECENT`,`ALMENT`) | `F_LEN` | `stock.picking` (in) + `stock.move` | `ESTENT` 0 Pte/1 Fact. |
| Factura recibida | `F_FRE` (`PROFRE`,`FECFRE`,`FACFRE` nº fact. prov.) | `F_LFR` | `account.move` (in_invoice) | `ESTFRE` 0 Pte/1 Parcial/2 Pagada |

### Circuito VENTAS
| Documento | Cabecera | Líneas | Odoo | Estado origen |
|---|---|---|---|---|
| Presupuesto | `F_PRE` (`CLIPRE`,`FECPRE`,`AGEPRE`) | `F_LPS` | `sale.order` (presupuesto) | `ESTPRE` 0 Pte/1 Aceptado/2 Rechazado/3 Enviado |
| Pedido cliente | `F_PCL` (`CLIPCL`,`FECPCL`,`ALMPCL`) | `F_LPC` (+`ANULPC` cant. anulada) | `sale.order` (confirmado) | `ESTPCL` 0..4 |
| Remito / Albarán | `F_ALB` (`CLIALB`,`FECALB`,`ALMALB`) | `F_LAL` | `stock.picking` (out) + `stock.move` | `ESTALB` 0 Pte/1 Facturado; `COBALB` estado cobro |
| Factura | `F_FAC` (`CLIFAC`,`FECFAC`,`TDRFAC` rectificada) | `F_LFA` | `account.move` (out_invoice) | `ESTFAC` 0 Pte/1 Parcial/2 Cobrada/3 Devuelta/4 Anulada |

> "Remito" (AR) = "Albarán" (ES) = `F_ALB`. `F_REC`=recibos/vencimientos y `F_REM`=remesas bancarias **no** son recepciones; la entrada de compra es `F_ENT`.

---

## PLANO 2b — TESORERÍA (opt-in)

### Cobros — `F_COB` (+ `F_LCO`) → `account.payment` (in) + conciliación
`CODCOB`,`FECCOB`,`IMPCOB`,`CPTCOB` (concepto),`CPACOB` (contrapartida),`TIPCOB` (0 Fact. emitida/1 Albarán/2 Recibo/3 Fact. recibida). `F_LCO` (`TFALCO`,`CFALCO`,`LINLCO`) **enlaza el cobro con las facturas** → conciliar contra los `account.move` migrados.

### Pagos — `F_PAG` → `account.payment` (out)
`CODPAG`,`PROPAG` (proveedor),`IMPPAG`,`FEMPAG`/`FVEPAG` (emisión/vencimiento),`BANPAG` (→diario),`TPAPAG` (1 Pagaré/2 Cheque),`CHEPAG` (ref.).

### Anticipo cliente — `F_ANT` → `account.payment` (anticipo) / saldo a favor
`CODANT`,`CLIANT`,`FECANT`,`IMPANT`,`ESTANT` (0 Sin aplicar/1 Aplicado),`TDOANT`/`CDOANT`/`SDOANT` (doc aplicado),`CRIANT` (0 Vale/1 Anticipo efectivo/2 Otros).

### Anticipo proveedor — `F_ANP` → `account.payment` (out, anticipo)
`CODANP`,`PROANP`,`IMPANP`,`ESTANP`,`TDOANP`/`CDOANP`.

> **Conciliación** = paso **opcional** (requiere documentos de la Etapa 2 ya migrados). Se puede importar el pago sin conciliar.

---

## Notas transversales

1. **Precio de venta** fuera de `F_ART` → tarifas (`F_TAR`/`F_LTA`/`F_LTC`).
2. **IVA por línea = selector**, no %; resolver con `F_CFG`; cabecera admite 3 IVAs + exento.
3. **Triple descuento** en cascada por línea → `1-(1-d1)(1-d2)(1-d3)`.
4. **Multi-año:** dimensiones clave sin año (fusión); hechos/tesorería clave con año; stock del último año.
5. **`F_SEC` sin descripción**; **`F_RET`** parece retiradas de caja TPV (no retenciones) — confirmar.
6. **Obras NO se migran** (no se usan en FactuSol): las tablas `F_OBR`,`F_CAP`,`F_ORD`,`F_HOR`/`F_LHO`,`F_MAT`/`F_LMA` quedan **fuera de alcance** (la gestión de obras vive en un módulo Odoo aparte). Inventario completo: 170 tablas; lo demás fuera de los planos anteriores (cartera avanzada, contabilidad, trazabilidad, TPV, config extendida, `T_*`/`R_*`) salvo indicación.


---



<a id='sec7'></a>

# 7. Decisiones abiertas

> Archivo de origen: `docs/DECISIONS.md`

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


---



<a id='sec8'></a>

# 8. Licencia

> Archivo de origen: `LICENSE`

FactuSol Odoo by GoxTech
Copyright (C) GoxTech

Esta suite se distribuye bajo la licencia GNU Lesser General Public License v3.0 (LGPL-3),
la misma familia de licencias que usan los módulos de Odoo Community.

Texto completo de la licencia: https://www.gnu.org/licenses/lgpl-3.0.html

Cada addon declara "license": "LGPL-3" en su __manifest__.py.
Reemplazar/añadir el texto íntegro de la LGPL-3 en este archivo al publicar el repositorio.


---
