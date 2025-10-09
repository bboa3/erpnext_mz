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


def _upsert_terms(
    company_name: str,
    entry_name: str,
    terms_text: str,
    category: str | None,
    update_existing: bool = False
) -> Tuple[str, str]:
    """Create or optionally update a Terms and Conditions document.
    
    Args:
        company_name: Company name for context
        entry_name: Name/ID of the terms document
        terms_text: The terms content
        category: Category (SELLING/BUYING) for applicability
        update_existing: If False, skip updates to existing terms (idempotent)
    
    Returns:
        Tuple of (document_name, status) where status is "created", "updated", or "skipped"
    """
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
        LOGGER.info(f"Terms '{entry_name}' already exists (as '{existing_name}')")
        
        # If update_existing is False, skip updates (idempotent behavior)
        if not update_existing:
            LOGGER.info(f"Skipping update for existing terms '{entry_name}' (update_existing=False)")
            return existing_name, "skipped"
        
        # Update existing document
        doc = frappe.get_doc("Terms and Conditions", existing_name)
        needs_save = False
        
        # Track original values for comparison
        original_title = getattr(doc, "title", None)
        original_terms = (doc.terms or "").strip()
        original_disabled = bool(doc.disabled)
        original_selling = doc.selling
        original_buying = doc.buying
        
        # Ensure title and name align with JSON name
        if original_title != title:
            doc.title = title
            needs_save = True
            LOGGER.info(f"Title changed: '{original_title}' → '{title}'")
            
        if doc.name != entry_name:
            try:
                frappe.rename_doc(doc.doctype, doc.name, entry_name, force=True)
                doc.name = entry_name
                LOGGER.info(f"Renamed: '{existing_name}' → '{entry_name}'")
            except Exception:
                # If rename fails, continue with existing name
                pass
                
        # Update terms/body
        if original_terms != prepared_terms.strip():
            doc.terms = prepared_terms
            needs_save = True
            LOGGER.info(f"Terms content updated (length: {len(original_terms)} → {len(prepared_terms)})")
            
        # Reactivate if disabled
        if original_disabled:
            doc.disabled = 0
            needs_save = True
            LOGGER.info(f"Re-enabled terms (was disabled)")
            
        # Apply category-based applicability and check if changed
        _apply_category_fields(doc, category or "")
        if doc.selling != original_selling or doc.buying != original_buying:
            needs_save = True
            LOGGER.info(f"Category fields updated: selling={doc.selling}, buying={doc.buying}")
        
        if needs_save:
            doc.save(ignore_permissions=True)
            LOGGER.info(f"✅ Updated existing terms '{doc.name}'")
            return doc.name, "updated"
        else:
            LOGGER.info(f"No changes needed for terms '{doc.name}'")
            return doc.name, "skipped"

    # Create new document with explicit name = JSON 'name'
    LOGGER.info(f"Creating new terms document '{entry_name}'")
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
    LOGGER.info(f"✅ Created terms document '{doc.name}'")
    
    return doc.name, "created"


def ensure_terms_from_json(
    company_name: str,
    json_path: Optional[str] = None,
    commit: bool = True,
    update_existing: bool = False
) -> Dict[str, object]:
    """Load terms and conditions from JSON file and create/update them.
    
    Args:
        company_name: Company name for context
        json_path: Path to JSON file (defaults to packaged file)
        commit: Whether to commit after operations
        update_existing: If False, only create new terms, don't update existing ones (idempotent)
    
    Returns:
        Dict with status and statistics
    """
    created = 0
    updated = 0
    skipped = 0
    items: List[str] = []
    
    try:
        spec = _load_terms_spec(json_path)
        for row in spec:
            name, status = _upsert_terms(
                company_name,
                row["name"],
                row["terms"],
                row.get("category"),
                update_existing=update_existing
            )
            if status == "created":
                created += 1
            elif status == "updated":
                updated += 1
            elif status == "skipped":
                skipped += 1
            items.append(name)
            
        if commit:
            frappe.db.commit()
            
        LOGGER.info(
            "Terms loading complete | company=%s created=%s updated=%s skipped=%s update_existing=%s",
            company_name, created, updated, skipped, update_existing
        )
        
        return {
            "ok": True,
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "items": items,
            "update_existing": update_existing
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure Terms from JSON failed")
        return {"ok": False, "error": _("Failed to ensure Terms and Conditions from JSON")}


def set_default_selling_terms(company_name: str, terms_name: str = "Factura") -> Dict[str, object]:
    """Set default selling terms for a company.
    
    Args:
        company_name: Name of the company
        terms_name: Name of the Terms and Conditions document to set as default
    
    Returns:
        Dict with status and details
    """
    try:
        # Verify the company exists
        if not frappe.db.exists("Company", company_name):
            error_msg = f"Company '{company_name}' not found"
            LOGGER.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        # Verify the terms document exists
        if not frappe.db.exists("Terms and Conditions", terms_name):
            error_msg = f"Terms and Conditions '{terms_name}' not found"
            LOGGER.error(error_msg)
            return {"ok": False, "error": error_msg}
        
        # Check if the terms has selling enabled
        is_selling = frappe.db.get_value("Terms and Conditions", terms_name, "selling")
        if not is_selling:
            LOGGER.warning(f"Terms '{terms_name}' does not have 'selling' enabled. Enabling it now.")
            frappe.db.set_value("Terms and Conditions", terms_name, "selling", 1)
        
        # Get current default to check if update is needed
        current_default = frappe.db.get_value("Company", company_name, "default_selling_terms")
        
        if current_default == terms_name:
            LOGGER.info(f"Default selling terms for '{company_name}' is already set to '{terms_name}'")
            return {
                "ok": True,
                "already_set": True,
                "company": company_name,
                "terms": terms_name
            }
        
        # Set the default selling terms
        frappe.db.set_value("Company", company_name, "default_selling_terms", terms_name)
        frappe.db.commit()
        
        LOGGER.info(f"Set default selling terms for '{company_name}' to '{terms_name}'")
        
        return {
            "ok": True,
            "already_set": False,
            "company": company_name,
            "terms": terms_name,
            "previous_default": current_default
        }
        
    except Exception as e:
        error_msg = f"Failed to set default selling terms: {str(e)}"
        LOGGER.error(error_msg)
        frappe.log_error(frappe.get_traceback(), "Set Default Selling Terms Failed")
        return {"ok": False, "error": error_msg}


def ensure_terms_and_set_defaults(
    company_name: str,
    json_path: Optional[str] = None,
    commit: bool = True,
    update_existing: bool = False,
    set_factura_as_default: bool = True
) -> Dict[str, object]:
    """Complete workflow: Load terms from JSON and set Factura as default selling terms.
    
    This is the recommended function to use for setting up terms and conditions for a company.
    It is fully idempotent and safe to run multiple times.
    
    Args:
        company_name: Company name
        json_path: Path to terms JSON file
        commit: Whether to commit changes
        update_existing: Whether to update existing terms (False for idempotent behavior)
        set_factura_as_default: Whether to set "Factura" as default selling terms
    
    Returns:
        Dict with comprehensive status information
    """
    result = {
        "ok": True,
        "company": company_name,
        "terms_loading": {},
        "default_setting": {}
    }
    
    # Step 1: Load terms from JSON
    terms_result = ensure_terms_from_json(
        company_name,
        json_path=json_path,
        commit=commit,
        update_existing=update_existing
    )
    result["terms_loading"] = terms_result
    
    if not terms_result.get("ok"):
        result["ok"] = False
        return result
    
    # Step 2: Set Factura as default selling terms (if requested)
    if set_factura_as_default and "Factura" in terms_result.get("items", []):
        default_result = set_default_selling_terms(company_name, "Factura")
        result["default_setting"] = default_result
        
        if not default_result.get("ok"):
            result["ok"] = False
            LOGGER.warning(f"Terms loaded successfully but failed to set default: {default_result.get('error')}")
    
    return result


@frappe.whitelist()
def create_terms_from_json_manually(json_path: Optional[str] = None) -> Dict[str, object]:
    """Whitelist function for manual terms creation from UI.
    
    Note: This uses update_existing=True for backwards compatibility.
    """
    if frappe.session.user != "Administrator" and not frappe.has_permission(doctype="Terms and Conditions", ptype="write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"ok": False, "error": _("No Company found")}
    return set_default_selling_terms(company_name)


