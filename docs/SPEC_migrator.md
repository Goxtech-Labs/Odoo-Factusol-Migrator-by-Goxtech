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
