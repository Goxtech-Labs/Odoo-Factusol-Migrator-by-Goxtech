# -*- coding: utf-8 -*-
"""Catálogo del esquema real de FactuSol (única fuente de verdad de nombres de
campo). Extraído de ``docs/SCHEMA_CATALOG.md``. No inventar nombres de campo:
usar estos. El migrador igualmente descubre el esquema en runtime; este catálogo
fija claves, campos mínimos, orden de carga y mapeo a Odoo.

Convención: tablas ``F_<COD>``; columnas ``<CAMPO><COD>``. Clave de documento =
``TIP`` (serie) + ``COD`` (código); clave de línea = ``TIP``+``COD``+``POS``.
"""

PLANES = [
    ("0", "Configuración"),
    ("1", "Dimensiones"),
    ("2", "Hechos comerciales"),
    ("2b", "Tesorería"),
]

# Prefijos de tipo de documento (= código de la tabla cabecera).
DOC_PREFIXES = ("FAC", "FRE", "ALB", "ENT", "PPR", "PCL", "PRE")


def suffix(table):
    """'F_LFA' -> 'LFA' (sufijo de columna)."""
    return table[2:] if table.startswith("F_") else table


def header_field_map(table):
    """Campos de cabecera derivados del sufijo de la tabla (estructura común)."""
    s = suffix(table)
    return {
        "tip": "TIP" + s,
        "cod": "COD" + s,
        "fec": "FEC" + s,
        "est": "EST" + s,
        "alm": "ALM" + s,
        "tiv": "TIV" + s,
        "fop": "FOP" + s,
        "tot": "TOT" + s,
    }


def line_field_map(line_table):
    """Campos de línea derivados del sufijo (estructura IDÉNTICA en los 7 docs)."""
    s = suffix(line_table)
    return {
        "tip": "TIP" + s,
        "cod": "COD" + s,
        "pos": "POS" + s,
        "art": "ART" + s,
        "qty": "CAN" + s,
        "price": "PRE" + s,
        "d1": "DT1" + s,
        "d2": "DT2" + s,
        "d3": "DT3" + s,
        "iva": "IVA" + s,
        "ce1": "CE1" + s,
        "ce2": "CE2" + s,
        "tot": "TOT" + s,
    }


def _f(src, target, transform="str", key=False, minimal=False):
    return {"src": src, "target": target, "transform": transform,
            "key": key, "min": minimal}


# --------------------------------------------------------------------------- #
# PLANO 0 — CONFIGURACIÓN (opt-in)
# --------------------------------------------------------------------------- #
CONFIG = [
    {
        "code": "company", "plane": "0", "label": "Empresa", "table": "F_EMP",
        "model": "res.company", "key": "CODEMP", "xmlid_prefix": "emp",
        "load_order": 1,
        "fields": [
            _f("CODEMP", "code", "str", key=True, minimal=True),
            _f("DENEMP", "name", "str", minimal=True),
            _f("DOMEMP", "street"), _f("POBEMP", "city"),
            _f("CPOEMP", "zip"), _f("PROEMP", "state"),
        ],
    },
    {
        "code": "taxes", "plane": "0", "label": "Tipos de IVA / RE", "table": "F_CFG",
        "model": "account.tax", "key": "CODCFG", "xmlid_prefix": "cfg",
        "load_order": 2,
        "fields": [
            _f("CODCFG", "code", "str", key=True, minimal=True),
            _f("NUMCFG", "amount", "float", minimal=True),
        ],
    },
    {
        "code": "payment_terms", "plane": "0", "label": "Formas de pago", "table": "F_FPA",
        "model": "account.payment.term", "key": "CODFPA", "xmlid_prefix": "fpa",
        "load_order": 3,
        "fields": [
            _f("CODFPA", "code", "str", key=True, minimal=True),
            _f("VENFPA", "nb_terms", "int", minimal=True),
        ],
    },
    {
        "code": "banks", "plane": "0", "label": "Bancos / cuentas", "table": "F_BAN",
        "model": "account.journal", "key": "CODBAN", "xmlid_prefix": "ban",
        "load_order": 4,
        "fields": [
            _f("CODBAN", "code", "str", key=True, minimal=True),
            _f("NOMBAN", "name", "str", minimal=True),
            _f("CCOBAN", "account", "str"),
        ],
    },
]

# --------------------------------------------------------------------------- #
# PLANO 1 — DIMENSIONES
# --------------------------------------------------------------------------- #
DIMENSIONS = [
    {
        "code": "warehouse", "plane": "1", "label": "Almacenes", "table": "F_ALM",
        "model": "stock.warehouse", "key": "CODALM", "xmlid_prefix": "alm",
        "load_order": 10,
        "fields": [
            _f("CODALM", "code", "str", key=True, minimal=True),
            _f("DIRALM", "name", "str", minimal=True),
            _f("POBALM", "city", "str", minimal=True),
            _f("CPOALM", "zip"), _f("PROALM", "state"),
            _f("TELALM", "phone"), _f("EMAALM", "email"),
        ],
    },
    {
        "code": "section", "plane": "1", "label": "Secciones", "table": "F_SEC",
        "model": "product.category", "key": "CODSEC", "xmlid_prefix": "sec",
        "load_order": 20,
        "fields": [
            _f("CODSEC", "name", "str", key=True, minimal=True),
        ],
    },
    {
        "code": "family", "plane": "1", "label": "Familias", "table": "F_FAM",
        "model": "product.category", "key": "CODFAM", "xmlid_prefix": "fam",
        "load_order": 21,
        "fields": [
            _f("CODFAM", "code", "str", key=True, minimal=True),
            _f("DESFAM", "name", "str", minimal=True),
            _f("SECFAM", "parent_id", "str", minimal=True),
            _f("CUEFAM", "property_account_income"), _f("CUCFAM", "property_account_expense"),
        ],
    },
    {
        "code": "customer", "plane": "1", "label": "Clientes", "table": "F_CLI",
        "model": "res.partner", "key": "CODCLI", "xmlid_prefix": "cli",
        "partner_kind": "customer", "load_order": 30,
        "fields": [
            _f("CODCLI", "x_factusol_code", "str", key=True, minimal=True),
            _f("NOFCLI", "name", "str", minimal=True),
            _f("NIFCLI", "vat", "vat", minimal=True),
            _f("DOMCLI", "street", "str", minimal=True),
            _f("POBCLI", "city", "str", minimal=True),
            _f("CPOCLI", "zip", "str", minimal=True),
            _f("PROCLI", "state_id", "str", minimal=True),
            _f("NOCCLI", "comment"), _f("TELCLI", "phone"), _f("MOVCLI", "mobile"),
            _f("EMACLI", "email"), _f("WEBCLI", "website"), _f("PAICLI", "country_id"),
            _f("FPACLI", "property_payment_term_id"), _f("AGECLI", "x_factusol_agent_code"),
            _f("TARCLI", "property_product_pricelist"), _f("IVACLI", "x_factusol_iva_regime"),
            _f("DT1CLI", "x_disc1", "float"), _f("DT2CLI", "x_disc2", "float"),
            _f("DT3CLI", "x_disc3", "float"), _f("SWFCLI", "iban"),
        ],
    },
    {
        "code": "supplier", "plane": "1", "label": "Proveedores", "table": "F_PRO",
        "model": "res.partner", "key": "CODPRO", "xmlid_prefix": "pro",
        "partner_kind": "supplier", "load_order": 31,
        "fields": [
            _f("CODPRO", "x_factusol_code", "str", key=True, minimal=True),
            _f("NOFPRO", "name", "str", minimal=True),
            _f("NIFPRO", "vat", "vat", minimal=True),
            _f("DOMPRO", "street", "str", minimal=True),
            _f("POBPRO", "city", "str", minimal=True),
            _f("CPOPRO", "zip", "str", minimal=True),
            _f("PROPRO", "state_id", "str", minimal=True),
            _f("FPAPRO", "property_supplier_payment_term_id"), _f("IVAPRO", "x_factusol_iva_regime"),
            _f("SWFPRO", "iban"), _f("EMAPRO", "email"),
        ],
    },
    {
        "code": "product", "plane": "1", "label": "Artículos", "table": "F_ART",
        "model": "product.template", "key": "CODART", "xmlid_prefix": "art",
        "load_order": 40,
        "fields": [
            _f("CODART", "default_code", "str", key=True, minimal=True),
            _f("DESART", "name", "str", minimal=True),
            _f("PCOART", "standard_price", "float", minimal=True),
            _f("FAMART", "categ_id", "str", minimal=True),
            _f("EANART", "barcode", "str", minimal=True),
            _f("TIVART", "taxes_id", "selector"), _f("STOART", "is_storable", "int"),
            _f("DSCART", "active", "int"), _f("UMEART", "uom_id"),
        ],
    },
    {
        "code": "variant", "plane": "1", "label": "Tallas / Colores (variantes)",
        "table": "F_CE1", "model": "product.attribute", "key": "CODCE1",
        "xmlid_prefix": "ce", "load_order": 41,
        # El transformador lee F_CE1 (talla), F_CE2 (color), F_EAC (EAN por
        # artículo+talla+color) y detecta variantes por presencia en F_STC/F_EAC.
        "extra_tables": ["F_CE2", "F_EAC", "F_STC"],
        "fields": [
            _f("CODCE1", "value", "str", key=True, minimal=True),
        ],
    },
    {
        "code": "pricelist", "plane": "1", "label": "Tarifas (precios de venta)",
        "table": "F_TAR", "model": "product.pricelist", "key": "CODTAR",
        "xmlid_prefix": "tar", "load_order": 45,
        "extra_tables": ["F_LTA", "F_LTC"],
        "fields": [
            _f("CODTAR", "name", "str", key=True, minimal=True),
            _f("MARTAR", "margin", "float"), _f("IVATAR", "iva", "selector"),
        ],
    },
    {
        "code": "stock", "plane": "1", "label": "Stock inicial", "table": "F_STO",
        "model": "stock.quant", "key": None, "xmlid_prefix": "stq",
        "load_order": 49, "extra_tables": ["F_STC"], "last_year_only": True,
        "fields": [
            _f("ARTSTO", "product", "str", minimal=True),
            _f("ALMSTO", "location", "str", minimal=True),
            _f("ACTSTO", "quantity", "float", minimal=True),
        ],
    },
]

# --------------------------------------------------------------------------- #
# PLANO 2 — HECHOS COMERCIALES (7 documentos, estructura común)
# --------------------------------------------------------------------------- #
def _doc(code, label, table, line_table, prefix, xmlid_prefix, partner_field,
         partner_kind, kind, load_order, move_type=None, picking_type=None):
    return {
        "code": code, "plane": "2", "label": label, "table": table,
        "line_table": line_table, "prefix": prefix, "xmlid_prefix": xmlid_prefix,
        "partner_field": partner_field, "partner_kind": partner_kind,
        "kind": kind, "move_type": move_type, "picking_type": picking_type,
        "key": header_field_map(table)["cod"], "load_order": load_order,
        "header": header_field_map(table), "line": line_field_map(line_table),
    }


DOCUMENTS = [
    # --- VENTAS ---
    _doc("quotation", "Presupuestos (venta)", "F_PRE", "F_LPS", "PRE", "pre",
         "CLIPRE", "customer", "sale_order", 60),
    _doc("sale_order", "Pedidos de cliente", "F_PCL", "F_LPC", "PCL", "pcl",
         "CLIPCL", "customer", "sale_order", 61),
    _doc("delivery", "Remitos / Albaranes (venta)", "F_ALB", "F_LAL", "ALB", "alb",
         "CLIALB", "customer", "picking", 62, picking_type="outgoing"),
    _doc("customer_invoice", "Facturas de venta", "F_FAC", "F_LFA", "FAC", "fac",
         "CLIFAC", "customer", "move", 63, move_type="out_invoice"),
    # --- COMPRAS ---
    _doc("purchase_order", "Pedidos a proveedor", "F_PPR", "F_LPP", "PPR", "ppr",
         "PROPPR", "supplier", "purchase_order", 64),
    _doc("receipt", "Entradas / Recepciones", "F_ENT", "F_LEN", "ENT", "ent",
         "PROENT", "supplier", "picking", 65, picking_type="incoming"),
    _doc("vendor_bill", "Facturas recibidas", "F_FRE", "F_LFR", "FRE", "fre",
         "PROFRE", "supplier", "move", 66, move_type="in_invoice"),
]

# --------------------------------------------------------------------------- #
# PLANO 2b — TESORERÍA (opt-in)
# --------------------------------------------------------------------------- #
TREASURY = [
    {
        "code": "collection", "plane": "2b", "label": "Cobros", "table": "F_COB",
        "model": "account.payment", "key": "CODCOB", "xmlid_prefix": "cob",
        "payment_type": "inbound", "extra_tables": ["F_LCO"], "load_order": 80,
        "fields": [
            _f("CODCOB", "ref", "str", key=True, minimal=True),
            _f("FECCOB", "date", "date", minimal=True),
            _f("IMPCOB", "amount", "float", minimal=True),
            _f("CPTCOB", "memo"), _f("TIPCOB", "kind", "int"),
        ],
    },
    {
        "code": "payment", "plane": "2b", "label": "Pagos", "table": "F_PAG",
        "model": "account.payment", "key": "CODPAG", "xmlid_prefix": "pag",
        "payment_type": "outbound", "load_order": 81,
        "fields": [
            _f("CODPAG", "ref", "str", key=True, minimal=True),
            _f("PROPAG", "partner", "str", minimal=True),
            _f("IMPPAG", "amount", "float", minimal=True),
            _f("FEMPAG", "date", "date", minimal=True),
            _f("BANPAG", "journal", "str"), _f("TPAPAG", "method", "int"),
        ],
    },
    {
        "code": "customer_advance", "plane": "2b", "label": "Anticipos de cliente",
        "table": "F_ANT", "model": "account.payment", "key": "CODANT",
        "xmlid_prefix": "ant", "payment_type": "inbound", "load_order": 82,
        "fields": [
            _f("CODANT", "ref", "str", key=True, minimal=True),
            _f("CLIANT", "partner", "str", minimal=True),
            _f("IMPANT", "amount", "float", minimal=True),
            _f("FECANT", "date", "date", minimal=True),
            _f("ESTANT", "state", "int"),
        ],
    },
    {
        "code": "supplier_advance", "plane": "2b", "label": "Anticipos a proveedor",
        "table": "F_ANP", "model": "account.payment", "key": "CODANP",
        "xmlid_prefix": "anp", "payment_type": "outbound", "load_order": 83,
        "fields": [
            _f("CODANP", "ref", "str", key=True, minimal=True),
            _f("PROANP", "partner", "str", minimal=True),
            _f("IMPANP", "amount", "float", minimal=True),
            _f("ESTANP", "state", "int"),
        ],
    },
]


def all_entities():
    """Catálogo completo en orden de carga (planos 0→1→2→2b)."""
    return CONFIG + DIMENSIONS + DOCUMENTS + TREASURY


def entities_by_plane(plane):
    return [e for e in all_entities() if e["plane"] == plane]


def entity_by_code(code):
    for e in all_entities():
        if e["code"] == code:
            return e
    return None


def documents():
    return list(DOCUMENTS)


def document_by_code(code):
    for e in DOCUMENTS:
        if e["code"] == code:
            return e
    return None
