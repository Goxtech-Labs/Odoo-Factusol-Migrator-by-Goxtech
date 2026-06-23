# -*- coding: utf-8 -*-
"""Lectura de bases Access ``.accdb`` en Python puro, con degradación de backends.

Orden de preferencia (CLAUDE.md §5):
    pyaccdb (primario, lazy, soporta cifrado)
      -> access-parser (fallback puro-python)
        -> mdbtools (opcional, binario de sistema; nunca requisito)

Todos los backends exponen la MISMA interfaz (``list_tables`` / ``list_fields`` /
``iter_rows``). ``DictBackend`` permite alimentar datos en memoria (tests) sin
ninguna dependencia externa.
"""
import os
import re
import shutil
import subprocess

from .convert import clean_str


class AccessReaderError(Exception):
    """No hay ningún backend capaz de abrir el fichero."""


def parse_company_year(filename):
    """``EEEAAAA.accdb`` -> ``("002", 2026)`` (empresa de 3 díg. + año de 4).

    Fuente de respaldo autoritativa: ``F_EMP``/``EJEEMP``. Si el patrón no calza,
    intenta extraer un año de 4 cifras del nombre.
    """
    base = os.path.basename(filename or "")
    stem = os.path.splitext(base)[0]
    digits = re.sub(r"\D", "", stem)
    if len(digits) == 7:
        return digits[:3], int(digits[3:])
    m = re.search(r"(19|20)\d{2}", stem)
    year = int(m.group(0)) if m else 0
    company = digits[:3] if len(digits) >= 3 else (digits or "")
    return company, year


# --------------------------------------------------------------------------- #
# Backends
# --------------------------------------------------------------------------- #
class _BaseBackend:
    name = "base"

    @classmethod
    def is_available(cls):
        return False

    def list_tables(self):
        raise NotImplementedError

    def list_fields(self, table):
        """[{'name','type','size','description'}] — descripción best-effort."""
        raise NotImplementedError

    def iter_rows(self, table, columns=None, batch_size=1000):
        raise NotImplementedError

    def close(self):
        pass


class PyaccdbBackend(_BaseBackend):
    name = "pyaccdb"

    @classmethod
    def is_available(cls):
        try:
            import pyaccdb  # noqa: F401
            return True
        except Exception:
            return False

    def __init__(self, path, password=None):
        import pyaccdb
        # La API exacta puede variar entre versiones; se intentan las formas
        # habituales y, si ninguna abre, se deja degradar al siguiente backend.
        self._db = None
        for opener in ("open", "Database", "AccessDatabase", "Reader"):
            fn = getattr(pyaccdb, opener, None)
            if fn is None:
                continue
            try:
                self._db = fn(path, password=password) if password else fn(path)
                break
            except TypeError:
                try:
                    self._db = fn(path)
                    break
                except Exception:
                    continue
            except Exception:
                continue
        if self._db is None:
            raise AccessReaderError("pyaccdb no pudo abrir el fichero")

    def _tables_obj(self):
        for attr in ("tables", "table_names", "list_tables"):
            obj = getattr(self._db, attr, None)
            if obj is None:
                continue
            return obj() if callable(obj) else obj
        raise AccessReaderError("pyaccdb: API de tablas desconocida")

    def list_tables(self):
        return [t for t in self._tables_obj() if not str(t).startswith("MSys")]

    def list_fields(self, table):
        rows = list(self.iter_rows(table, batch_size=1))
        names = list(rows[0].keys()) if rows else []
        return [{"name": n, "type": "", "size": 0, "description": ""} for n in names]

    def iter_rows(self, table, columns=None, batch_size=1000):
        reader = None
        for attr in ("read", "rows", "iter_rows", "read_table"):
            fn = getattr(self._db, attr, None)
            if fn:
                reader = fn(table)
                break
        if reader is None:
            raise AccessReaderError("pyaccdb: API de lectura desconocida")
        for row in reader:
            yield dict(row)


class AccessParserBackend(_BaseBackend):
    name = "access-parser"

    @classmethod
    def is_available(cls):
        try:
            import access_parser  # noqa: F401
            return True
        except Exception:
            return False

    def __init__(self, path, password=None):
        from access_parser import AccessParser
        self._db = AccessParser(path)
        # Cache columna-orientada por tabla (access_parser no es lazy).
        self._cache = {}

    def list_tables(self):
        catalog = getattr(self._db, "catalog", {}) or {}
        return [t for t in catalog.keys() if not str(t).startswith("MSys")]

    def _parsed(self, table):
        if table not in self._cache:
            self._cache[table] = self._db.parse_table(table) or {}
        return self._cache[table]

    def list_fields(self, table):
        cols = self._parsed(table)
        return [{"name": n, "type": "", "size": 0, "description": ""} for n in cols.keys()]

    def iter_rows(self, table, columns=None, batch_size=1000):
        parsed = self._parsed(table)
        names = list(parsed.keys())
        if not names:
            return
        length = max((len(v) for v in parsed.values()), default=0)
        use = [c for c in (columns or names) if c in parsed]
        for i in range(length):
            yield {c: parsed[c][i] if i < len(parsed[c]) else None for c in use}


class MdbtoolsBackend(_BaseBackend):
    name = "mdbtools"

    @classmethod
    def is_available(cls):
        return bool(shutil.which("mdb-tables") and shutil.which("mdb-export"))

    def __init__(self, path, password=None):
        self.path = path
        if not self.is_available():
            raise AccessReaderError("mdbtools no está instalado")

    def list_tables(self):
        out = subprocess.check_output(["mdb-tables", "-1", self.path], text=True)
        return [t for t in out.split("\n") if t and not t.startswith("MSys")]

    def list_fields(self, table):
        rows = list(self.iter_rows(table, batch_size=1))
        names = list(rows[0].keys()) if rows else []
        return [{"name": n, "type": "", "size": 0, "description": ""} for n in names]

    def iter_rows(self, table, columns=None, batch_size=1000):
        import csv
        import io
        out = subprocess.check_output(
            ["mdb-export", "-D", "%Y-%m-%d", self.path, table], text=True
        )
        reader = csv.DictReader(io.StringIO(out))
        for row in reader:
            yield {k: (clean_str(v) if v is not None else None) for k, v in row.items()}


class DictBackend(_BaseBackend):
    """Backend en memoria para tests/fixtures (sin dependencias externas).

    ``data`` = ``{table: {"fields": [..], "rows": [{col: val}, ...]}}`` o, más
    corto, ``{table: [ {col: val}, ... ]}``.
    """
    name = "dict"

    @classmethod
    def is_available(cls):
        return True

    def __init__(self, data, password=None):
        self.data = {}
        for table, spec in (data or {}).items():
            if isinstance(spec, dict):
                rows = list(spec.get("rows", []))
                fields = spec.get("fields") or (list(rows[0].keys()) if rows else [])
            else:
                rows = list(spec)
                fields = list(rows[0].keys()) if rows else []
            self.data[table] = {"fields": list(fields), "rows": rows}

    def list_tables(self):
        return list(self.data.keys())

    def list_fields(self, table):
        spec = self.data.get(table, {"fields": []})
        return [{"name": n, "type": "", "size": 0, "description": ""}
                for n in spec["fields"]]

    def iter_rows(self, table, columns=None, batch_size=1000):
        for row in self.data.get(table, {"rows": []})["rows"]:
            yield dict(row) if columns is None else {c: row.get(c) for c in columns}


_BACKENDS = (PyaccdbBackend, AccessParserBackend, MdbtoolsBackend)


# --------------------------------------------------------------------------- #
# Fachada
# --------------------------------------------------------------------------- #
class AccessReader:
    """Fachada que delega en el primer backend disponible (con degradación)."""

    def __init__(self, backend):
        self._backend = backend
        self.backend_name = backend.name

    # -- Construcción --------------------------------------------------------
    @classmethod
    def open(cls, path, password=None, preferred=None):
        order = list(_BACKENDS)
        if preferred:
            order.sort(key=lambda b: 0 if b.name == preferred else 1)
        errors = []
        for backend_cls in order:
            if not backend_cls.is_available():
                errors.append("%s: no disponible" % backend_cls.name)
                continue
            try:
                backend = backend_cls(path, password=password)
                # Verificación temprana: que liste tablas.
                backend.list_tables()
                return cls(backend)
            except Exception as exc:  # noqa: BLE001  (degradación intencional)
                errors.append("%s: %s" % (backend_cls.name, exc))
                continue
        raise AccessReaderError(
            "No se pudo leer el .accdb con ningún backend.\n" + "\n".join(errors)
            + "\nInstale 'pyaccdb' o 'access-parser' (pip), o 'mdbtools' (sistema)."
        )

    @classmethod
    def from_dict(cls, data):
        """Reader en memoria para tests/fixtures."""
        return cls(DictBackend(data))

    @classmethod
    def available_backends(cls):
        return [b.name for b in _BACKENDS if b.is_available()]

    # -- Interfaz ------------------------------------------------------------
    def list_tables(self):
        return self._backend.list_tables()

    def has_table(self, table):
        return table in set(self._backend.list_tables())

    def list_fields(self, table):
        return self._backend.list_fields(table)

    def field_names(self, table):
        return [f["name"] for f in self._backend.list_fields(table)]

    def iter_rows(self, table, columns=None, batch_size=1000):
        return self._backend.iter_rows(table, columns=columns, batch_size=batch_size)

    def read_all(self, table, columns=None):
        return list(self.iter_rows(table, columns=columns))

    def count(self, table):
        return sum(1 for _ in self.iter_rows(table))

    def close(self):
        self._backend.close()
