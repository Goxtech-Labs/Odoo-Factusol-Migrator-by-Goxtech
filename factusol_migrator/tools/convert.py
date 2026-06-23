# -*- coding: utf-8 -*-
"""Field-level conversion helpers (FactuSol cp1252/Spanish-decimals → Odoo).

Pure functions, unit-testable in isolation.
"""
import datetime
from decimal import Decimal

# Fechas basura que FactuSol/Access pueden traer.
_NULL_DATES = {"", "00/00/0000", "0000-00-00", "1900-01-01", "01/01/1900"}


def clean_str(value):
    """Return a stripped unicode string. Decodes cp1252 bytes if needed."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            value = value.decode("cp1252")
        except UnicodeDecodeError:
            value = value.decode("cp1252", errors="replace")
    return str(value).strip()


def to_float(value, default=0.0):
    """Parse a number, tolerating the Spanish format ``1.234,56`` → ``1234.56``.

    Numeric inputs (int/float/Decimal) pass straight through.
    """
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    s = str(value).strip()
    if not s:
        return default
    if "," in s:
        # Coma decimal española; el punto es separador de miles.
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return default


def to_int(value, default=0):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(to_float(value, default))


def to_date(value):
    """Return a ``datetime.date`` or ``False`` (Odoo-friendly null)."""
    if value is None:
        return False
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    s = clean_str(value)
    if not s or s in _NULL_DATES:
        return False
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S"):
        try:
            d = datetime.datetime.strptime(s, fmt)
            if d.year <= 1900:
                return False
            return d.date()
        except ValueError:
            continue
    return False


def norm_vat(value):
    """Normalise a NIF/CIF: uppercase, no spaces/dots/dashes. Empty → False."""
    s = clean_str(value).upper().replace(" ", "").replace(".", "").replace("-", "")
    return s or False


def to_selector(value, default=0):
    """FactuSol per-line IVA selector (0=IVA1,1=IVA2,2=IVA3,3=Exento)."""
    return to_int(value, default)
