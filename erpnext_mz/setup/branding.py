#!/usr/bin/env python3
"""
Website branding and appearance setup for ERPNext Mozambique.

This module handles:
- Website logo configuration
- Brand name settings
- Website appearance customization
"""

import frappe


def apply_website_branding(override: bool = False):
    """
    Set website logo / brand text.
    Idempotent: by default only fills blanks. Pass override=True to force.
    """
    try:
        ws = frappe.get_single("Website Settings")

        logo = "/assets/erpnext_mz/images/logo180.png"
        brand = "MozEconomia Cloud"

        changed = False

        def set_if_needed(field: str, value: str) -> None:
            nonlocal changed
            current = getattr(ws, field, None)
            if override or not current:
                setattr(ws, field, value)
                changed = True

        # Correct fields on Website Settings
        set_if_needed("app_logo", logo)
        set_if_needed("app_name", brand)

        if changed:
            ws.save(ignore_permissions=True)
            from frappe.website.utils import clear_website_cache
            clear_website_cache()

        return {"applied": True, "changed": changed}

    except Exception:
        frappe.log_error(title="apply_website_branding failed", message=frappe.get_traceback())
        return {"applied": False, "error": frappe.get_traceback()}
