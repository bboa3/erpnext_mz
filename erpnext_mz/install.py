import frappe
from erpnext_mz.setup.language import ensure_language_pt_mz, apply_system_settings
from erpnext_mz.setup.branding import apply_website_branding
from erpnext_mz.setup.uom import setup_portuguese_uoms_complete


def after_install():
    """Run setup tasks after app installation"""
    ensure_language_pt_mz()
    apply_system_settings(override=True)
    apply_website_branding(override=True)
    setup_portuguese_uoms()


def setup_portuguese_uoms():
    """Setup Portuguese UOMs on installation"""
    try:
        setup_portuguese_uoms_complete()
    except Exception as e:
        frappe.log_error(title="Portuguese UOM Setup Failed", message=str(e))
        pass


def after_migrate():
    """Run setup tasks after app migration"""
    # Re-apply defaults where fields are empty, without overriding admin choices
    ensure_language_pt_mz()
    apply_system_settings(override=False)
    apply_website_branding(override=False)


# All setup functions have been moved to the setup/ modules for better organization
