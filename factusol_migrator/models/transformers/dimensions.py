# -*- coding: utf-8 -*-
"""Plano 1 — Dimensiones (maestros). Carga idempotente con fusión multi-año
(External ID sin año). Reutiliza lo nativo de Odoo (terceros, productos,
variantes, categorías, tarifas, stock)."""
from .base import _stats


def _wl(line):
    """Whitelist de campos opt-in del perfil (vacío = solo mínimos)."""
    if line and getattr(line, "field_whitelist", None):
        return {x.strip() for x in line.field_whitelist.split(",") if x.strip()}
    return set()


class DimensionMixin:

    # -- utilidades ----------------------------------------------------------
    def _register_xmlid(self, xmlid, rec):
        if self.dry_run or not rec or self.ref(xmlid):
            return
        self.env["ir.model.data"].create({
            "module": self.MODULE, "name": xmlid, "model": rec._name,
            "res_id": rec.id, "noupdate": True,
        })

    def _resolve_state(self, name):
        if not name:
            return self.env["res.country.state"]
        if not hasattr(self, "_state_cache"):
            self._state_cache = {}
        if name not in self._state_cache:
            domain = [("name", "ilike", name)]
            if self.company.country_id:
                domain.append(("country_id", "=", self.company.country_id.id))
            self._state_cache[name] = self.env["res.country.state"].search(domain, limit=1)
        return self._state_cache[name]

    # -- Almacenes -----------------------------------------------------------
    def do_warehouse(self, source, reader, entity, line):
        if not reader.has_table("F_ALM"):
            return _stats()
        n = ok = fail = 0
        for row in reader.iter_rows("F_ALM"):
            n += 1
            code = self.s(row, "CODALM")
            if not code:
                self.log("warning", "warehouse", "", "Almacén sin código", year=source.fiscal_year)
                fail += 1
                continue
            vals = {
                "name": self.s(row, "DIRALM") or ("Almacén %s" % code),
                "code": code[:5],
                "company_id": self.company.id,
            }
            try:
                self.upsert("stock.warehouse", self.dim_xmlid("alm", code), vals)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "warehouse", code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)

    # -- Secciones / Familias → product.category -----------------------------
    def do_section(self, source, reader, entity, line):
        if not reader.has_table("F_SEC"):
            return _stats()
        n = ok = fail = 0
        for row in reader.iter_rows("F_SEC"):
            n += 1
            code = self.s(row, "CODSEC")
            if not code:
                fail += 1
                continue
            try:
                self.upsert("product.category", self.dim_xmlid("sec", code), {"name": code})
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "section", code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)

    def do_family(self, source, reader, entity, line):
        if not reader.has_table("F_FAM"):
            return _stats()
        n = ok = fail = 0
        for row in reader.iter_rows("F_FAM"):
            n += 1
            code = self.s(row, "CODFAM")
            if not code:
                fail += 1
                continue
            vals = {"name": self.s(row, "DESFAM") or code}
            parent = self.ref(self.dim_xmlid("sec", self.s(row, "SECFAM")))
            if parent:
                vals["parent_id"] = parent.id
            try:
                self.upsert("product.category", self.dim_xmlid("fam", code), vals)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "family", code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)

    # -- Terceros ------------------------------------------------------------
    def _do_partner(self, source, reader, kind, line):
        table = "F_CLI" if kind == "customer" else "F_PRO"
        sfx = "CLI" if kind == "customer" else "PRO"
        prefix = "cli" if kind == "customer" else "pro"
        if not reader.has_table(table):
            return _stats()
        wl = _wl(line)
        n = ok = fail = 0
        for row in reader.iter_rows(table):
            n += 1
            code = self.s(row, "COD" + sfx)
            if not code:
                fail += 1
                continue
            vals = {
                "name": self.s(row, "NOF" + sfx) or code,
                "street": self.s(row, "DOM" + sfx),
                "city": self.s(row, "POB" + sfx),
                "zip": self.s(row, "CPO" + sfx),
                "company_type": "company",
                "x_factusol_code": code,
                ("customer_rank" if kind == "customer" else "supplier_rank"): 1,
            }
            vat = self.cv(row.get("NIF" + sfx), "vat")
            if vat:
                vals["vat"] = vat
            state = self._resolve_state(self.s(row, "PRO" + sfx))
            if state:
                vals["state_id"] = state.id
            if "EMA" + sfx in wl and self.s(row, "EMA" + sfx):
                vals["email"] = self.s(row, "EMA" + sfx)
            if "TEL" + sfx in wl and self.s(row, "TEL" + sfx):
                vals["phone"] = self.s(row, "TEL" + sfx)
            if "AGE" + sfx in wl and self.s(row, "AGE" + sfx):
                vals["x_factusol_agent_code"] = self.s(row, "AGE" + sfx)
            try:
                self.upsert("res.partner", self.dim_xmlid(prefix, code), vals)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", kind, code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)

    def do_customer(self, source, reader, entity, line):
        return self._do_partner(source, reader, "customer", line)

    def do_supplier(self, source, reader, entity, line):
        return self._do_partner(source, reader, "supplier", line)

    # -- Artículos -----------------------------------------------------------
    def do_product(self, source, reader, entity, line):
        if not reader.has_table("F_ART"):
            return _stats()
        wl = _wl(line)
        n = ok = fail = 0
        for row in reader.iter_rows("F_ART"):
            n += 1
            code = self.s(row, "CODART")
            if not code:
                fail += 1
                continue
            vals = {
                "default_code": code,
                "name": self.s(row, "DESART") or code,
                "standard_price": self.fl(row, "PCOART"),
                "x_factusol_code": code,
            }
            fam = self.category_ref(self.s(row, "FAMART"))
            if fam:
                vals["categ_id"] = fam.id
            barcode = self.s(row, "EANART")
            if barcode:
                vals["barcode"] = barcode
            if self.it(row, "DSCART"):
                vals["active"] = False
            if "STOART" in wl:
                vals["is_storable"] = bool(self.it(row, "STOART"))
            if "TIVART" in wl:
                tax = self.resolve_tax(self.cv(row.get("TIVART"), "selector"), "sale")
                if tax:
                    vals["taxes_id"] = [(6, 0, [tax.id])]
            try:
                self.upsert("product.template", self.dim_xmlid("art", code), vals)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "product", code, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail)

    # -- Variantes Talla/Color (nativas de Odoo) -----------------------------
    def do_variant(self, source, reader, entity, line):
        talla = self.upsert("product.attribute", self.dim_xmlid("attr", "talla"),
                            {"name": "Talla", "create_variant": "always"})
        color = self.upsert("product.attribute", self.dim_xmlid("attr", "color"),
                            {"name": "Color", "create_variant": "always"})
        t_val, t_inv = self._load_attr_values(reader, "F_CE1", "CODCE1", None, talla, "t")
        c_val, c_inv = self._load_attr_values(reader, "F_CE2", "CODCE2", "DESCE2", color, "c")

        combos, eans = {}, {}
        for tbl, fa, f1, f2, fe in (
            ("F_EAC", "ARTEAC", "CE1EAC", "CE2EAC", "EANEAC"),
            ("F_STC", "ARTSTC", "CE1STC", "CE2STC", None),
        ):
            if not reader.has_table(tbl):
                continue
            for row in reader.iter_rows(tbl):
                art = self.s(row, fa)
                if not art:
                    continue
                e1, e2 = self.s(row, f1), self.s(row, f2)
                combos.setdefault(art, set()).add((e1, e2))
                if fe and self.s(row, fe):
                    eans[(art, e1, e2)] = self.s(row, fe)

        n = ok = fail = skip = 0
        for art, pairs in combos.items():
            n += 1
            tmpl = self.product_tmpl_ref(art)
            if not tmpl:
                self.log("warning", "variant", art,
                         "Artículo con variantes no encontrado (cargar artículos primero)",
                         year=source.fiscal_year)
                skip += 1
                continue
            if self.dry_run:
                ok += 1
                continue
            try:
                self._apply_variant_lines(tmpl, pairs, talla, color, t_val, c_val)
                self._tag_variants(tmpl, art, talla, color, t_inv, c_inv, eans)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.log("error", "variant", art, str(exc), year=source.fiscal_year)
                fail += 1
        return _stats(n, ok, fail, skip)

    def _load_attr_values(self, reader, table, code_field, name_field, attribute, tag):
        """Carga valores de atributo; devuelve (code→value, value_id→code)."""
        values, inverse = {}, {}
        if not attribute or not reader.has_table(table):
            return values, inverse
        for row in reader.iter_rows(table):
            code = self.s(row, code_field)
            if not code:
                continue
            name = self.s(row, name_field) if name_field else code
            rec = self.upsert("product.attribute.value",
                              self.dim_xmlid("cev", "%s_%s" % (tag, code)),
                              {"name": name or code, "attribute_id": attribute.id})
            if rec:
                values[code] = rec
                inverse[rec.id] = code
        return values, inverse

    def _apply_variant_lines(self, tmpl, pairs, talla, color, t_val, c_val):
        if tmpl.attribute_line_ids:
            return  # ya tiene variantes (idempotente)
        lines = []
        used_t = {p[0] for p in pairs if p[0] and p[0] in t_val}
        used_c = {p[1] for p in pairs if p[1] and p[1] in c_val}
        if used_t and talla:
            lines.append((0, 0, {"attribute_id": talla.id,
                                 "value_ids": [(6, 0, [t_val[t].id for t in used_t])]}))
        if used_c and color:
            lines.append((0, 0, {"attribute_id": color.id,
                                 "value_ids": [(6, 0, [c_val[c].id for c in used_c])]}))
        if lines:
            tmpl.write({"attribute_line_ids": lines})

    def _tag_variants(self, tmpl, art, talla, color, t_inv, c_inv, eans):
        for variant in tmpl.product_variant_ids:
            e1 = e2 = "0"
            for ptav in variant.product_template_attribute_value_ids:
                base_val = ptav.product_attribute_value_id.id
                if talla and ptav.attribute_id.id == talla.id:
                    e1 = t_inv.get(base_val, "0")
                elif color and ptav.attribute_id.id == color.id:
                    e2 = c_inv.get(base_val, "0")
            token = "%s_%s_%s" % (art, e1, e2)
            self._register_xmlid(self.dim_xmlid("var", token), variant)
            variant.x_factusol_code = token
            ean = eans.get((art, e1 if e1 != "0" else "", e2 if e2 != "0" else "")) \
                or eans.get((art, e1, e2))
            if ean and not variant.barcode:
                variant.barcode = ean

    # -- Tarifas (precios de venta) ------------------------------------------
    def do_pricelist(self, source, reader, entity, line):
        if not reader.has_table("F_TAR"):
            return _stats()
        n = ok = 0
        tar_list = sorted(reader.read_all("F_TAR"), key=lambda r: self.s(r, "CODTAR"))
        main_code = self.s(tar_list[0], "CODTAR") if tar_list else None
        for row in tar_list:
            n += 1
            code = self.s(row, "CODTAR")
            self.upsert("product.pricelist", self.dim_xmlid("tar", code),
                        {"name": "Tarifa %s" % code, "company_id": self.company.id})
            ok += 1
        if reader.has_table("F_LTA") and not self.dry_run:
            for row in reader.iter_rows("F_LTA"):
                tar, art = self.s(row, "TARLTA"), self.s(row, "ARTLTA")
                price = self.fl(row, "PRELTA")
                tmpl = self.product_tmpl_ref(art)
                pl = self.ref(self.dim_xmlid("tar", tar))
                if not tmpl:
                    continue
                if tar == main_code:
                    tmpl.write({"list_price": price})
                if pl:
                    self.upsert("product.pricelist.item",
                                self.dim_xmlid("pli", "%s_%s" % (tar, art)),
                                {"pricelist_id": pl.id, "applied_on": "1_product",
                                 "product_tmpl_id": tmpl.id, "compute_price": "fixed",
                                 "fixed_price": price})
        return _stats(n, ok, 0)

    # -- Stock inicial → stock.quant (solo último año) -----------------------
    def do_stock(self, source, reader, entity, line):
        Quant = self.env["stock.quant"]
        n = ok = fail = 0

        def _set_qty(product, wh, qty, key):
            if not product or not wh or not wh.lot_stock_id:
                self.log("warning", "stock", key, "Falta producto o almacén",
                         year=source.fiscal_year)
                return False
            if self.dry_run:
                return True
            Quant.with_context(inventory_mode=True)._update_available_quantity(
                product, wh.lot_stock_id, qty
            )
            return True

        if reader.has_table("F_STO"):
            for row in reader.iter_rows("F_STO"):
                n += 1
                art, alm, qty = self.s(row, "ARTSTO"), self.s(row, "ALMSTO"), self.fl(row, "ACTSTO")
                tmpl = self.product_tmpl_ref(art)
                product = tmpl.product_variant_id if tmpl else None
                try:
                    ok += 1 if _set_qty(product, self.warehouse_ref(alm), qty, "%s@%s" % (art, alm)) else 0
                    fail += 0 if product else 1
                except Exception as exc:  # noqa: BLE001
                    self.log("error", "stock", "%s@%s" % (art, alm), str(exc), year=source.fiscal_year)
                    fail += 1
        if reader.has_table("F_STC"):
            for row in reader.iter_rows("F_STC"):
                n += 1
                art, alm = self.s(row, "ARTSTC"), self.s(row, "ALMSTC")
                e1, e2, qty = self.s(row, "CE1STC"), self.s(row, "CE2STC"), self.fl(row, "ACTSTC")
                var = self.variant_ref(art, e1, e2)
                try:
                    if _set_qty(var, self.warehouse_ref(alm), qty, "%s/%s/%s" % (art, e1, e2)):
                        ok += 1
                    else:
                        fail += 1
                except Exception as exc:  # noqa: BLE001
                    self.log("error", "stock", "%s/%s/%s" % (art, e1, e2), str(exc), year=source.fiscal_year)
                    fail += 1
        return _stats(n, ok, fail)
