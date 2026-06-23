# FactuSol Odoo by GoxTech — Migrador

App de migración **FactuSol → Odoo Community** autohospedado, open source y
gratuita. En **cuatro pasos** —subir las bases `.accdb` (una por año), elegir
qué importar, migrar y verificar— llevás lo esencial de FactuSol a Odoo,
conservando tu forma de trabajar.

> Autor: **GoxTech** · Licencia: **LGPL-3** · Odoo Community 18.0
> Depende de **factusol_core** (capa de compatibilidad).

## Instalación

1. Copiá `factusol_core` y `factusol_migrator` a tu `addons_path`.
2. Instalá un lector de Access (cualquiera alcanza; degradan entre sí):
   ```bash
   pip install -r factusol_migrator/requirements.txt   # pyaccdb / access-parser
   ```
   *(`mdbtools` del sistema es opcional, nunca obligatorio.)*
3. Apps → actualizar lista → instalar **FactuSol Odoo by GoxTech**.

### Docker
Usá la imagen oficial `odoo:18` montando los addons y las dependencias:
```dockerfile
FROM odoo:18
USER root
RUN pip install pyaccdb access-parser
USER odoo
# montar ./factusol_core y ./factusol_migrator en /mnt/extra-addons
```

## Los 4 pasos (menú **FactuSol Odoo by GoxTech → Importar**)

1. **Subir base(s)**: arrastrá uno o varios `.accdb` (uno por ejercicio). Se
   detecta **empresa y año** de cada fichero (`EEEAAAA.accdb` / `F_EMP`).
2. **Elegir qué migrar**: un **perfil** (Mínimo · Comercial · Contable completo ·
   Personalizado) + los **años** detectados. Selectividad por plano / entidad / campo.
3. **Previsualizar** (dry-run): conteos y avisos **sin escribir** en Odoo.
4. **Migrar y verificar**: carga idempotente + **informe de fidelidad por año**
   (conteos y cuadre de importes) con las incidencias y sus acciones sugeridas.

## Qué migra

| Plano | Contenido |
|---|---|
| 0 · Configuración (opt-in) | empresa, tipos de IVA/RE, formas de pago, bancos |
| 1 · Dimensiones | almacenes, secciones/familias, clientes, proveedores, artículos, **variantes talla/color nativas**, tarifas, stock inicial (último año) |
| 2 · Hechos | Compras (pedido→entrada→factura) y Ventas (presupuesto→pedido→remito→factura) |
| 2b · Tesorería (opt-in) | cobros, pagos, anticipos (conciliación opcional) |

## Cómo está hecho (para Claude Code / contribuir)

- **Lectura `.accdb`** en `tools/access_reader.py`: `AccessReader` con backends
  `pyaccdb → access-parser → mdbtools` (degradación automática) y `DictBackend`
  para tests sin dependencias.
- **Catálogo del esquema** en `tools/schema.py` (única fuente de verdad de los
  nombres de campo; se siembra en `factusol.table.profile`/`factusol.field.mapping`
  por `post_init_hook`).
- **ETL** en `models/transformers/`: un `MigrationEngine` con un `do_*` por
  entidad y **un solo `DocumentTransformer` genérico** para los 7 documentos
  (unión cabecera↔línea por `(TIP,COD)`, orden `POS`, número `TIPO-TIP-COD`).
- **Multi-ejercicio**: dimensiones con External ID **sin año** (fusionan), hechos
  y tesorería **con año** (`fac_2026_1-000001`), stock del **último** año.
- **Idempotencia** vía `ir.model.data` (módulo `__factusol__`): reimportar no duplica.

## Tests

```bash
odoo -d <db> --test-enable --test-tags=/factusol_migrator -i factusol_migrator --stop-after-init
```

Cubren lectura (DictBackend), conversión (cp1252/coma decimal/fechas), catálogo,
y el motor end-to-end con **dos años** (dimensiones, idempotencia, fusión
multi-año, documento genérico con triple descuento y orden por `POS`).

## Límites de la v1 (ver `docs/`)

- Localización fiscal destino: **decisión** `l10n_ar` vs `l10n_es` (afecta solo el
  mapeo de impuestos; default asumido `l10n_ar`).
- Remitos/entradas (`stock.picking`) se cargan en **borrador** (no se valida el
  stock histórico); el stock real entra como **inventario inicial**.
- Cobros/pagos se importan **sueltos**; la **conciliación** es opcional (perfil →
  `options.reconcile`).
- Tarifas por **variante** (`F_LTC`) y comisiones de agente: soporte básico.
