import frappe
from erpnext_mz.setup.language import ensure_language_pt_mz, apply_system_settings
from erpnext_mz.setup.branding import apply_website_branding
from erpnext_mz.setup.uom import setup_portuguese_uoms_safe


def after_install():
    """Run setup tasks after app installation"""
    ensure_language_pt_mz()
    apply_system_settings(override=True)
    apply_website_branding(override=True)
    setup_portuguese_uoms_safe()
    ensure_mz_company_setup_doctype_and_single()

def after_migrate():
    """Run setup tasks after app migration"""
    # Re-apply defaults where fields are empty, without overriding admin choices
    ensure_language_pt_mz()
    apply_system_settings(override=False)
    apply_website_branding(override=False)
    ensure_mz_company_setup_doctype_and_single()


# All setup functions have been moved to the setup/ modules for better organization


def ensure_mz_company_setup_doctype_and_single():
    """Ensure DocType definition is loaded and the Single doc has baseline values.

    This is a safety net to guarantee onboarding dialogs have their backing DocType
    even if migrations ran in a non-standard order or on partially configured sites.
    """
    reloaded = False
    try:
        from frappe.modules.import_file import import_file_by_path
        doc_path = frappe.get_app_path(
            "erpnext_mz", "doctype", "mz_company_setup", "mz_company_setup.json"
        )
        import_file_by_path(doc_path, force=True)
        reloaded = True
    except Exception:
        frappe.log_error(
            title="Import MZ Company Setup DocType by Path Failed",
            message=frappe.get_traceback(),
        )

    try:
        # Ensure the DocType exists before initializing the Single
        if reloaded or frappe.db.exists("DocType", "MZ Company Setup"):
            baseline_checkbox_fields = [
                "step1_complete",
                "step2_complete",
                "step3_skipped",
                "is_applied",
                "trigger_onboarding",
            ]
            for fieldname in baseline_checkbox_fields:
                if frappe.db.get_single_value("MZ Company Setup", fieldname) is None:
                    frappe.db.set_single_value("MZ Company Setup", fieldname, 0)
    except Exception:
        frappe.log_error(
            title="Initialize MZ Company Setup Single Failed",
            message=frappe.get_traceback(),
        )
