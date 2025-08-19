#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from typing import Any, Dict, List


PRODUCTS_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "products.csv"))
OUTPUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "items_import.json"))


def parse_pt_number(text: str) -> float:
    if text is None:
        return 0.0
    t = str(text).strip()
    if not t:
        return 0.0
    # Remove thousand separators and convert decimal comma to dot
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except Exception:
        return 0.0


def looks_like_url(value: str) -> bool:
    v = (value or "").strip().lower()
    return v.startswith("http://") or v.startswith("https://") or v.startswith("www.")


def detect_uom(item_name: str, notes: str) -> str:
    source = f"{item_name} {notes}".lower()
    if "hora" in source or "hour" in source:
        return "Hora"
    if "dia" in source or "day" in source:
        return "Dia"
    if "mês" in source or "mes" in source or "month" in source:
        return "Mês"
    return "Unidade"


def slugify_code(index: int, prefix: str = "PD-") -> str:
    return f"{prefix}{index:03d}"


def html_description(text: str) -> str:
    if not text:
        return ""
    # Escape basic HTML special chars
    escaped = (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )
    return f"<div><p>{escaped}</p></div>"


def build_item_doc(row: Dict[str, str], index: int, item_group_default: str, company_default: str | None) -> Dict[str, Any]:
    name = (row.get("Produto") or "").strip()
    notes = (row.get("Observações") or "").strip()
    cost = parse_pt_number(row.get("Custo"))
    price = parse_pt_number(row.get("Preço "))
    qty = parse_pt_number(row.get("Quantidade"))
    image = (row.get("Imagem") or "").strip()
    fiscal_cat = (row.get("Categoria Fiscal") or "").strip()

    item_code = slugify_code(index)
    item_name = name or item_code
    uom = detect_uom(item_name, notes)

    description_parts: List[str] = []
    if notes:
        description_parts.append(notes)
    if fiscal_cat:
        description_parts.append(f"Categoria Fiscal: {fiscal_cat}")
    description_html = html_description("\n".join(description_parts)) if description_parts else ""

    doc: Dict[str, Any] = {
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_name,
        "item_group": item_group_default,
        "stock_uom": uom,
        "is_stock_item": 0,
        "has_variants": 0,
        "opening_stock": 0,
        "valuation_rate": cost,
        "standard_rate": price,
        "is_fixed_asset": 0,
        "is_purchase_item": 1,
        "is_sales_item": 1,
        "include_item_in_manufacturing": 0,
        "allow_alternative_item": 0,
        "over_delivery_receipt_allowance": 0,
        "over_billing_allowance": 0,
        "country_of_origin": "Mozambique",
        "end_of_life": "2099-12-31",
        "description": description_html,
        "attributes": [],
        "customer_items": [],
        "reorder_levels": [],
        "barcodes": [],
        "supplier_items": [],
        "taxes": [],
    }

    # Quantity hints
    if qty > 0:
        doc["min_order_qty"] = qty

    # UOM conversion list (optional)
    doc["uoms"] = [{"uom": uom, "conversion_factor": 1}]

    # Image
    if looks_like_url(image) or image:
        doc["image"] = image

    # Item defaults with company only if provided, without warehouse to avoid link errors
    if company_default:
        doc["item_defaults"] = [{"company": company_default}]

    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Invoice Ninja products to ERPNext Item JSON")
    parser.add_argument("--products-csv", dest="products_csv", default=PRODUCTS_CSV, help="Path to products.csv")
    parser.add_argument("--output", dest="output_json", default=OUTPUT_JSON, help="Path to write items_import.json")
    parser.add_argument("--item-group", dest="item_group", default="Serviços", help="Default Item Group")
    parser.add_argument("--company", dest="company", default="", help="Default Company to set in item_defaults (optional)")
    args = parser.parse_args()

    with open(args.products_csv, "r", encoding="utf-8", newline="") as pf:
        reader = csv.DictReader(pf)
        items: List[Dict[str, Any]] = []
        for idx, row in enumerate(reader, start=1):
            doc = build_item_doc(row, idx, args.item_group, args.company or None)
            items.append(doc)

    with open(args.output_json, "w", encoding="utf-8") as out:
        json.dump(items, out, ensure_ascii=False, indent=2)

    print(f"Wrote {args.output_json} with {len(items)} items")


if __name__ == "__main__":
    main()


