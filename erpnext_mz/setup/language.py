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
    - System Settings: number/date/time/language/precisions/update notifications
    - Global Defaults: default currency (MZN)
    - Disables system update notifications and change log popups
    """
    try:
        # Fields specific to System Settings DocType
        system_settings_fields = {
            "app_name": "MozEconomia Cloud",
            "country": "Mozambique",
            "currency": "MZN",
            "language": "pt-MZ",
            "number_format": "#.###,##",  # European: 1.234,56
            "float_precision": "2",  # Must be string per DocType definition
            "currency_precision": "2",  # Must be string per DocType definition
            "date_format": "dd/mm/yyyy",
            "time_zone": "Africa/Maputo",
            "disable_system_update_notification": 1,
            "disable_change_log_notification": 1,
            "disable_standard_email_footer": 1,
        }

        # Fields specific to Global Defaults
        global_defaults_fields = {
            "country": "Mozambique",
            "currency": "MZN",
            "lang": "pt-MZ",  # Note: 'lang' for Global Defaults, not 'language'
            "disable_standard_email_footer": 1,
        }

        applied = {"system_settings": {}, "global_defaults": {}}
        errors = []

        def _is_empty(val) -> bool:
            """Check if value is empty, handling None, empty strings, and zero properly"""
            if val is None:
                return True
            if isinstance(val, str) and val.strip() == "":
                return True
            # Don't treat 0 or False as empty
            return False

        # Apply System Settings using proper document API
        try:
            doc = frappe.get_doc("System Settings", "System Settings")
            fields_to_update = {}
            
            for field, value in system_settings_fields.items():
                try:
                    current = doc.get(field)
                    if override or _is_empty(current):
                        fields_to_update[field] = value
                        applied["system_settings"][field] = value
                except Exception as field_error:
                    errors.append({
                        "field": field,
                        "context": "System Settings",
                        "error": str(field_error)
                    })
            
            if fields_to_update:
                doc.update(fields_to_update)
                doc.flags.ignore_permissions = True
                doc.save()
                frappe.db.commit()
        
        except Exception as e:
            frappe.log_error(
                title="System Settings Update Failed",
                message=f"Error: {str(e)}\n{frappe.get_traceback()}"
            )
            errors.append({"context": "System Settings (general)", "error": str(e)})

        # Apply Global Defaults
        for field, value in global_defaults_fields.items():
            try:
                current = frappe.db.get_default(field)
                if override or _is_empty(current):
                    frappe.db.set_default(field, value)
                    applied["global_defaults"][field] = value
            except Exception as e:
                errors.append({
                    "field": field,
                    "context": "Global Defaults",
                    "error": str(e)
                })
                frappe.log_error(
                    title=f"Failed to set Global Default: {field}",
                    message=f"Value: {value}\nError: {str(e)}\n{frappe.get_traceback()}"
                )
        
        # Commit global defaults changes
        frappe.db.commit()
        
        # Clear cache to ensure changes take effect immediately
        frappe.clear_cache()

        result = {
            "applied": True,
            "applied_fields": applied,
        }
        
        if errors:
            result["partial_errors"] = errors
            frappe.log_error(
                title="apply_system_settings: Partial Errors",
                message=frappe.as_json(errors, indent=2)
            )

        return result

    except Exception as e:
        frappe.log_error(
            title="apply_system_settings: Critical Failure",
            message=frappe.get_traceback()
        )
        return {
            "applied": False,
            "error": str(e),
            "traceback": frappe.get_traceback()
        }
