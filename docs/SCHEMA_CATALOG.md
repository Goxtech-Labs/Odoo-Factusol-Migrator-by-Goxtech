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
