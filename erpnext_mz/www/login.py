import frappe
from frappe.translate import get_all_languages

no_cache = True


def get_context(context):
    desired = (
        frappe.form_dict.get("_lang")
        or frappe.db.get_default("lang")
        or frappe.db.get_single_value("System Settings", "language")
        or "pt-MZ"
    )

    try:
        enabled = set(get_all_languages())
    except Exception:
        enabled = set()

    if desired not in enabled and "-" in desired:
        parent = desired.split("-", 1)[0]
        if parent in enabled:
            desired = parent

    frappe.local.lang = desired

    if frappe.session.user == "Guest" and hasattr(frappe.local, "cookie_manager"):
        try:
            frappe.local.cookie_manager.set_cookie("preferred_language", desired)
        except Exception:
            pass

    return context


