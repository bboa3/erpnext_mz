from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _


LOGGER = frappe.logger("erpnext_mz.setup.terms", allow_site=True)


def _default_terms_json_path() -> str:
    # Try packaged under module package path: apps/erpnext_mz/erpnext_mz/setup/data
    packaged_module = frappe.get_app_path("erpnext_mz", "erpnext_mz", "setup", "data", "mozcloud_terms_mz.json")
    if os.path.exists(packaged_module):
        return packaged_module

    # Try packaged directly under app root: apps/erpnext_mz/setup/data (less common)
    packaged_root = frappe.get_app_path("erpnext_mz", "setup", "data", "mozcloud_terms_mz.json")
    if os.path.exists(packaged_root):
        return packaged_root

    # Development fallback: bench root
    try:
        bench_root = frappe.utils.get_bench_path()
        bench_candidate = os.path.join(bench_root, "mozcloud_terms_mz.json")
        if os.path.exists(bench_candidate):
            return bench_candidate
    except Exception:
        pass

    # Final fallback: relative to current working directory
    return os.path.abspath("mozcloud_terms_mz.json")


def _load_terms_spec(json_path: Optional[str]) -> List[Dict[str, str]]:
    path = json_path or _default_terms_json_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Terms JSON not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Terms JSON must be a list of objects")
    validated: List[Dict[str, str]] = []
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"Row {i} is not an object")
        name = (row.get("name") or "").strip()
        terms = (row.get("terms") or "").strip()
        if not name or not terms:
            raise ValueError(f"Row {i} missing required fields 'name' and/or 'terms'")
        validated.append({
            "name": name,
            "category": (row.get("category") or "").strip(),
            "terms": terms,
        })
    return validated


def _compose_title(company_name: str, entry_name: str) -> str:
    # Use JSON 'name' as title as well to keep both aligned
    return entry_name


def _prepare_terms_value(raw_text: str) -> str:
    """Return a value appropriate for the Terms field.

    If the field is a rich text editor, convert newlines to HTML paragraphs and <br>.
    Otherwise, return the text with normalized newlines.
    """
    try:
        meta = frappe.get_meta("Terms and Conditions")
        terms_field = meta.get_field("terms")
        fieldtype = getattr(terms_field, "fieldtype", "") if terms_field else ""
    except Exception:
        terms_field = None
        fieldtype = ""

    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    if fieldtype in ("Text Editor", "HTML Editor"):
        # Convert \n\n to new paragraphs and single \n to <br>
        paragraphs = text.split("\n\n")
        html_parts: List[str] = []
        for idx, para in enumerate(paragraphs):
            safe = frappe.utils.escape_html(para)
            safe = safe.replace("\n", "<br>")
            if safe.strip():
                style = "margin-top:6px;" if idx > 0 else "margin-top:0;"
                html_parts.append(f"<p style=\"{style}\">{safe}</p>")
        return "".join(html_parts) if html_parts else ""
    return text


def _apply_category_fields(doc, category: str) -> None:
    """Best-effort mapping of JSON 'category' to Terms applicability fields.

    Supports a variety of schema possibilities across ERPNext versions.
    """
    try:
        meta = frappe.get_meta(doc.doctype)
    except Exception:
        return

    normalized = (category or "").strip().upper()
    is_selling = normalized in {"SELLING", "SALES", "SALE"}
    is_buying = normalized in {"BUYING", "PURCHASING", "PURCHASE", "BUY"}

    # Helper to set a field only if present
    def set_if_exists(fieldname: str, value):
        if meta.get_field(fieldname) is not None:
            setattr(doc, fieldname, value)

    # Common fields across versions
    set_if_exists("selling", 1 if is_selling else 0)
    set_if_exists("buying", 1 if is_buying else 0)
    set_if_exists("applicable_on", "Sales" if is_selling else ("Purchase" if is_buying else None))
    set_if_exists("terms_type", "Sales" if is_selling else ("Purchase" if is_buying else None))
    set_if_exists("module", "Selling" if is_selling else ("Buying" if is_buying else None))


def _upsert_terms(company_name: str, entry_name: str, terms_text: str, category: str | None) -> Tuple[str, bool]:
    title = _compose_title(company_name, entry_name)

    # Determine schema
    has_company_field = False
    try:
        meta = frappe.get_meta("Terms and Conditions")
        has_company_field = bool(meta.get_field("company"))
    except Exception:
        has_company_field = False

    # 1) Prefer exact docname match to honor JSON 'name' as ID
    existing_name = frappe.db.exists("Terms and Conditions", entry_name)
    if not existing_name:
        # 2) Fallback: find by title (from older runs)
        existing_name = frappe.db.get_value("Terms and Conditions", {"title": title}, "name") or \
                        frappe.db.get_value("Terms and Conditions", {"title": entry_name}, "name")

    prepared_terms = _prepare_terms_value(terms_text)

    if existing_name:
        doc = frappe.get_doc("Terms and Conditions", existing_name)
        # Ensure title and name align with JSON name
        needs_save = False
        if getattr(doc, "title", None) != title:
            doc.title = title
            needs_save = True
        if doc.name != entry_name:
            try:
                frappe.rename_doc(doc.doctype, doc.name, entry_name, force=True)
                doc.name = entry_name
            except Exception:
                # If rename fails, continue with existing name
                pass
        # Update terms/body
        if (doc.terms or "").strip() != prepared_terms.strip():
            doc.terms = prepared_terms
            needs_save = True
        # Reactivate if disabled
        if bool(doc.disabled):
            doc.disabled = 0
            needs_save = True
        # Apply category-based applicability
        _apply_category_fields(doc, category or "")
        if needs_save:
            doc.save(ignore_permissions=True)
        return doc.name, False

    # Create new document with explicit name = JSON 'name'
    doc = frappe.new_doc("Terms and Conditions")
    doc.title = title
    doc.terms = prepared_terms
    if has_company_field:
        try:
            doc.company = company_name
        except Exception:
            pass
    # Set explicit name to match JSON 'name'
    try:
        doc.name = entry_name
        doc.flags.name_set = True
    except Exception:
        pass
    _apply_category_fields(doc, category or "")
    doc.insert(ignore_permissions=True)
    return doc.name, True


def ensure_terms_from_json(company_name: str, json_path: Optional[str] = None, commit: bool = True) -> Dict[str, object]:
    created = 0
    updated = 0
    items: List[str] = []
    try:
        spec = _load_terms_spec(json_path)
        for row in spec:
            name, was_created = _upsert_terms(company_name, row["name"], row["terms"], row.get("category"))
            created += int(was_created)
            updated += int(not was_created)
            items.append(name)
        if commit:
            frappe.db.commit()
        LOGGER.info(
            "Terms upsert complete | company=%s created=%s updated=%s", company_name, created, updated
        )
        return {"ok": True, "created": created, "updated": updated, "items": items}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure Terms from JSON failed")
        return {"ok": False, "error": _("Failed to ensure Terms and Conditions from JSON")}


@frappe.whitelist()
def create_terms_from_json_manually(json_path: Optional[str] = None) -> Dict[str, object]:
    if frappe.session.user != "Administrator" and not frappe.has_permission(doctype="Terms and Conditions", ptype="write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"ok": False, "error": _("No Company found")}
    return ensure_terms_from_json(company_name, json_path=json_path, commit=True)


