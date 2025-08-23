import frappe

def after_install():
    apply_system_settings(override=True)


def after_migrate():
    # Re-apply defaults where fields are empty, without overriding admin choices
    apply_system_settings(override=False)


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
            "language": "pt",
            "number_format": "#.###,##",  # 1.234,56
            "float_precision": 2,
            "currency_precision": 2,
            "date_format": "dd/mm/yyyy",
            "time_zone": "Africa/Maputo",
            "enable_onboarding": 0,
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