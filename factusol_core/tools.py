# -*- coding: utf-8 -*-
"""Pure helpers shared by factusol_core and factusol_migrator.

No Odoo imports here on purpose: these functions are unit-testable in isolation
and importable from the migrator via
``from odoo.addons.factusol_core.tools import ...``.
"""

DOC_PREFIXES = ("FAC", "FRE", "ALB", "ENT", "PPR", "PCL", "PRE")


def _pad(cod, mask_width=6):
    """Zero-pad a document code to ``mask_width`` digits (FactuSol mask [F=...])."""
    try:
        return "%0*d" % (int(mask_width or 6), int(cod))
    except (TypeError, ValueError):
        # Non numeric code: keep as-is, left-padded with zeros to width.
        return str(cod).strip().zfill(int(mask_width or 6))


def format_doc_ref(tipo, tip, cod, mask_width=6):
    """Build the legible FactuSol document reference ``<TIPO>-<TIP>-<COD>``.

    ``tipo``  -> header table code / prefix (FAC, FRE, ALB, ENT, PPR, PCL, PRE).
    ``tip``   -> series (1 char, e.g. ``"1"``).
    ``cod``   -> integer code, zero-padded to ``mask_width`` (usually 6).

    >>> format_doc_ref("FAC", "1", 1)
    'FAC-1-000001'
    >>> format_doc_ref("fre", "2", 345, 6)
    'FRE-2-000345'
    """
    return "%s-%s-%s" % (
        str(tipo).strip().upper(),
        str(tip).strip(),
        _pad(cod, mask_width),
    )


def combine_discounts(d1=0.0, d2=0.0, d3=0.0):
    """Combine the FactuSol triple cascade discount into a single % discount.

    ``discount = (1 - (1-d1/100)(1-d2/100)(1-d3/100)) * 100``

    A single discount is preserved (compatible with native ``discount``):

    >>> round(combine_discounts(10, 0, 0), 6)
    10.0
    >>> round(combine_discounts(10, 10, 10), 4)
    27.1
    """
    factor = 1.0
    for d in (d1, d2, d3):
        factor *= 1.0 - (float(d or 0.0) / 100.0)
    return (1.0 - factor) * 100.0


def price_from_margin(cost, margin, basis="cost"):
    """Sale price derived from cost + margin (FactuSol margin-based tariffs).

    ``basis="cost"``  -> markup over cost:  ``price = cost * (1 + margin/100)``
    ``basis="price"`` -> margin over price: ``price = cost / (1 - margin/100)``

    >>> price_from_margin(100, 25)
    125.0
    >>> price_from_margin(100, 20, "price")
    125.0
    """
    cost = float(cost or 0.0)
    margin = float(margin or 0.0)
    if basis == "price":
        denom = 1.0 - (margin / 100.0)
        return cost / denom if denom > 0 else 0.0
    return cost * (1.0 + margin / 100.0)


def _slug(code):
    """Normalise a master code into an xmlid-safe token."""
    return "".join(c if (c.isalnum() or c in "_-") else "_" for c in str(code).strip())


def dimension_xmlid(prefix, code):
    """External ID for a *dimension* (master): no year -> merges across years.

    >>> dimension_xmlid("cli", "000123")
    'cli_000123'
    """
    return "%s_%s" % (prefix, _slug(code))


def fact_xmlid(prefix, year, tip, cod, mask_width=6):
    """External ID for a *fact* / treasury record: includes the fiscal year.

    >>> fact_xmlid("fac", 2026, "1", 1)
    'fac_2026_1-000001'
    """
    return "%s_%s_%s-%s" % (prefix, year, str(tip).strip(), _pad(cod, mask_width))
