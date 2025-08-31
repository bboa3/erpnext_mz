#!/usr/bin/env python3
"""
Language setup and configuration for ERPNext Mozambique.

This module handles:
- Creating and enabling pt-MZ language
- Setting system language defaults
- Language-related configuration
"""

import frappe


def ensure_language_pt_mz():
    """
    Ensure Language 'pt-MZ' exists and is enabled so the site can select it.
    This does not depend on frappe.geo.languages.json (which lacks pt-MZ).
    Idempotent and safe to call repeatedly.
    """
    try:
        if not frappe.db.exists("Language", "pt-MZ"):
            frappe.get_doc(
                {
                    "doctype": "Language",
                    "language_code": "pt-MZ",
                    "language_name": "Português (Moçambique)",
                    "based_on": "pt",
                    "enabled": 1,
                }
            ).insert(ignore_permissions=True)
        else:
            # Make sure it is enabled and linked to base Portuguese
            frappe.db.set_value("Language", "pt-MZ", {
                "enabled": 1,
                "based_on": "pt",
            })
    except Exception:
        frappe.log_error(title="ensure_language_pt_MZ failed", message=frappe.get_traceback())
        return {"applied": False, "error": frappe.get_traceback()}


def apply_system_settings(override: bool = True):
    """
    Idempotently set Mozambique-friendly defaults.
    - System Settings: number/date/time/language/precisions
    - Global Defaults: default currency (MZN)
    """
    try:
        desired = {
            "app_name": "ERPNext Moçambique",
            "country": "Mozambique",
            "currency": "MZN",
            "language": "pt-MZ",
            "lang": "pt-MZ",
            "number_format": "#.###,##",  # 1.234,56
            "float_precision": 2,
            "currency_precision": 2,
            "date_format": "dd/mm/yyyy",
            "time_zone": "Africa/Maputo"
        }

        applied = {}

        def _is_empty(val) -> bool:
            return val is None or (isinstance(val, str) and val.strip() == "")

        # System Settings
        for field, value in desired.items():
            current = frappe.db.get_single_value("System Settings", field)
            if override or _is_empty(current):
                frappe.db.set_single_value("System Settings", field, value)
                applied[field] = value

        # Global Defaults (singleton)
        for field, value in desired.items():
            current = frappe.db.get_default(field)
            if override or _is_empty(current):
                frappe.db.set_default(field, value)
                applied[field] = value
        
        # Cache refresh so Desk picks up language/formatting immediately
        frappe.clear_cache()

        return {"applied": True, "applied_fields": applied}

    except Exception:
        frappe.log_error(title="apply_system_settings failed", message=frappe.get_traceback())
        return {"applied": False, "error": frappe.get_traceback()}
