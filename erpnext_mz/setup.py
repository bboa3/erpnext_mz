# -*- coding: utf-8 -*-
"""
Setup Script for ERPNext Mozambique Custom App

This script sets up all Mozambique compliance features:
- VAT templates
- HR & Payroll components
- Custom fields
"""

import frappe
from frappe import _

def setup_mozambique_compliance(company):
    """
    Setup complete Mozambique compliance for a company
    
    Args:
        company (str): Company name
    """
    
    try:
        frappe.msgprint(_("A iniciar configuração de conformidade para Moçambique na empresa: {0}").format(company))
        
        # 1. Setup VAT Templates (incl. Sales/Purchase Taxes and Charges Templates)
        frappe.msgprint(_("A configurar modelos de IVA..."))
        from .modules.accounting.vat_templates import setup_mozambique_vat_templates, ensure_sales_purchase_tax_templates
        setup_mozambique_vat_templates(company)
        ensure_sales_purchase_tax_templates(company)
        
        # 2. Setup HR & Payroll Components
        frappe.msgprint(_("A configurar componentes de RH & Folha..."))
        from .modules.hr_payroll.inss_irps import create_inss_salary_component, create_irps_salary_component
        create_inss_salary_component(company)
        create_irps_salary_component(company)
        
        # 2.1 Setup Benefits in Kind
        frappe.msgprint(_("A configurar Benefícios em Espécie..."))
        from .modules.hr_payroll.benefits_in_kind import create_benefits_custom_fields
        create_benefits_custom_fields()
        
        # 3. Setup Custom Fields
        frappe.msgprint(_("A configurar campos personalizados..."))
        setup_custom_fields(company)
        
        # 4. Setup Company Settings
        frappe.msgprint(_("A configurar definições da empresa..."))
        setup_company_settings(company)
        
        frappe.msgprint(_("Configuração de conformidade para Moçambique concluída com sucesso!"))
        # Ensure Workspace exists (idempotent)
        ensure_workspace()
        
    except Exception as e:
        frappe.log_error(f"Error in Mozambique compliance setup: {str(e)}")
        frappe.throw(_("Error in setup: {0}").format(str(e)))

def ensure_workspace():
    """
    Ensure a public Workspace exists so the app is visible on the Desk.
    """
    try:
        ensure_module_def()
        # Prefer new label
        new_label = "Moçambique"
        old_label = "ERPNext Mozambique"
        # Rename old workspace if exists
        if frappe.db.exists("Workspace", {"label": old_label}):
            try:
                ws_old = frappe.get_doc("Workspace", {"label": old_label})
                frappe.db.set_value("Workspace", ws_old.name, "label", new_label)
                frappe.db.set_value("Workspace", ws_old.name, "title", new_label)
                frappe.db.commit()
            except Exception:
                pass
        
        if not frappe.db.exists("Workspace", {"label": new_label}):
            ws = frappe.new_doc("Workspace")
            ws.label = new_label
            ws.title = new_label
            # Insert as non-public to avoid Workspace Manager validation, then flip to public via db_set
            ws.public = 0
            ws.module = "ERPNext Mozambique"
            ws.flags.ignore_permissions = True
            ws.insert(ignore_permissions=True)
            frappe.db.commit()
            try:
                frappe.db.set_value("Workspace", ws.name, "public", 1)
                frappe.db.commit()
            except Exception:
                pass
            # Populate with curated links
            try:
                ws.reload()
                _populate_mz_workspace(ws)
            except Exception:
                pass
        else:
            # Ensure existing workspace is public and bound to our module
            try:
                ws = frappe.get_doc("Workspace", {"label": new_label})
                if not getattr(ws, "public", 0):
                    frappe.db.set_value("Workspace", ws.name, "public", 1)
                    frappe.db.commit()
                if getattr(ws, "module", "") != "ERPNext Mozambique":
                    frappe.db.set_value("Workspace", ws.name, "module", "ERPNext Mozambique")
                    frappe.db.commit()
                if not getattr(ws, "title", None) or ws.title != new_label:
                    frappe.db.set_value("Workspace", ws.name, "title", new_label)
                    frappe.db.commit()
                # Repopulate links if empty
                try:
                    ws.reload()
                    if not getattr(ws, "links", None) and not getattr(ws, "content", None):
                        _populate_mz_workspace(ws)
                except Exception:
                    pass
            except Exception:
                pass
        # Ensure HR workspaces exist to prevent 'Module not found' errors
        ensure_hr_workspaces()
        # Ensure child workspaces configured via UI are mirrored (e.g., 'Conformidade')
        ensure_mz_child_workspaces()
    except Exception as e:
        frappe.log_error(f"Failed to ensure ERPNext Mozambique workspace: {str(e)}")

def ensure_module_def():
    """Ensure a `Module Def` exists for ERPNext Mozambique (required for Workspace)."""
    try:
        if not frappe.db.exists("Module Def", "ERPNext Mozambique"):
            md = frappe.new_doc("Module Def")
            md.module_name = "ERPNext Mozambique"
            try:
                md.app_name = "erpnext_mz"
            except Exception:
                pass
            md.insert()
    except Exception as e:
        frappe.log_error(f"Failed to ensure Module Def: {str(e)}")

def ensure_mz_child_workspaces():
    """Ensure child workspaces under 'Moçambique' that reflect current UI structure.

    Mirrors the 'Conformidade' workspace with a basic header 'SAF-T'.
    """
    try:
        parent_label = "Moçambique"
        label = "Conformidade"
        # Create or update child workspace
        if frappe.db.exists("Workspace", {"label": label}):
            ws = frappe.get_doc("Workspace", {"label": label})
        else:
            ws = frappe.new_doc("Workspace")
            ws.label = label
            ws.title = label
            ws.public = 1
        # Ensure parent binding and icon
        try:
            if getattr(ws, "parent_page", None) != parent_label:
                ws.parent_page = parent_label
        except Exception:
            pass
        try:
            ws.icon = "organization"
        except Exception:
            pass
        # Clear legacy child tables to avoid duplication and set content JSON
        for child in ("links", "shortcuts", "charts", "number_cards", "quick_lists"):
            try:
                ws.set(child, [])
            except Exception:
                pass
        try:
            import json as _json
            ws.content = _json.dumps([
                {"type": "header", "data": {"text": "SAF-T"}},
            ])
        except Exception:
            pass
        ws.flags.ignore_permissions = True
        ws.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to ensure child workspaces for Moçambique: {str(e)}")

@frappe.whitelist()
def cleanup_hr_module_defs_for_hrms_install():
    """Remove pre-created HR module defs to avoid duplicate errors during HRMS install."""
    try:
        for mod in ("HR", "HR and Payroll"):
            if frappe.db.exists("Module Def", mod):
                try:
                    frappe.delete_doc("Module Def", mod, ignore_permissions=True)
                except Exception:
                    # As a fallback, mark as custom to allow overwrite
                    try:
                        frappe.db.set_value("Module Def", mod, "custom", 1)
                    except Exception:
                        pass
    except Exception as e:
        frappe.log_error(f"cleanup_hr_module_defs_for_hrms_install failed: {str(e)}")

def _populate_mz_workspace(ws):
    """Clear and populate the ERPNext Mozambique workspace with curated links."""
    # Clear legacy child tables if present
    for child in ("links", "shortcuts", "charts", "number_cards", "quick_lists"):
        try:
            ws.set(child, [])
        except Exception:
            pass
    # Section: Compliance
    ws.append("links", {"type": "Card Break", "label": "Compliance"})
    ws.append("links", {"type": "Link", "label": "Integration Requests (AT)", "link_type": "DocType", "link_to": "Integration Request"})
    ws.append("links", {"type": "Link", "label": "Files (SAF-T)", "link_type": "DocType", "link_to": "File"})
    # Section: Accounting & Tax
    ws.append("links", {"type": "Card Break", "label": "Accounting & Tax"})
    ws.append("links", {"type": "Link", "label": "Item Tax Templates", "link_type": "DocType", "link_to": "Item Tax Template"})
    ws.append("links", {"type": "Link", "label": "Tax Categories", "link_type": "DocType", "link_to": "Tax Category"})
    ws.append("links", {"type": "Link", "label": "Sales Taxes and Charges Template", "link_type": "DocType", "link_to": "Sales Taxes and Charges Template"})
    ws.append("links", {"type": "Link", "label": "Purchase Taxes and Charges Template", "link_type": "DocType", "link_to": "Purchase Taxes and Charges Template"})
    # Section: HR & Payroll
    ws.append("links", {"type": "Card Break", "label": "HR & Payroll"})
    ws.append("links", {"type": "Link", "label": "Salary Component", "link_type": "DocType", "link_to": "Salary Component"})
    ws.append("links", {"type": "Link", "label": "Payroll Entry", "link_type": "DocType", "link_to": "Payroll Entry"})
    ws.append("links", {"type": "Link", "label": "Employee", "link_type": "DocType", "link_to": "Employee"})
    # Section: Tools
    ws.append("links", {"type": "Card Break", "label": "Tools"})
    ws.flags.ignore_permissions = True
    ws.save(ignore_permissions=True)
    frappe.db.commit()
    # Also set content JSON for modern workspace renderer
    try:
        import json as _json
        cards = [
            {
                "type": "card",
                "title": "Compliance",
                "links": [
                    {"type": "doctype", "label": "Integration Requests (AT)", "name": "Integration Request"},
                    {"type": "doctype", "label": "Files (SAF-T)", "name": "File"},
                ],
            },
            {
                "type": "card",
                "title": "Accounting & Tax",
                "links": [
                    {"type": "doctype", "label": "Item Tax Template", "name": "Item Tax Template"},
                    {"type": "doctype", "label": "Tax Category", "name": "Tax Category"},
                    {"type": "doctype", "label": "Sales Taxes and Charges Template", "name": "Sales Taxes and Charges Template"},
                    {"type": "doctype", "label": "Purchase Taxes and Charges Template", "name": "Purchase Taxes and Charges Template"},
                ],
            },
            {
                "type": "card",
                "title": "HR & Payroll",
                "links": [
                    {"type": "doctype", "label": "Salary Component", "name": "Salary Component"},
                    {"type": "doctype", "label": "Payroll Entry", "name": "Payroll Entry"},
                    {"type": "doctype", "label": "Employee", "name": "Employee"},
                ],
            },
        ]
        ws.content = _json.dumps(cards)
        ws.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass

@frappe.whitelist()
def rebuild_mz_workspace():
    """Force rebuild the ERPNext Mozambique workspace contents (idempotent)."""
    try:
        label = "Moçambique"
        if frappe.db.exists("Workspace", {"label": label}):
            ws = frappe.get_doc("Workspace", {"label": label})
        else:
            ws = frappe.new_doc("Workspace")
            ws.label = label
            ws.title = label
            ws.public = 1
            ws.module = "ERPNext Mozambique"
            ws.insert(ignore_permissions=True)
        _populate_mz_workspace(ws)
        return {"success": True}
    except Exception as e:
        frappe.log_error(f"rebuild_mz_workspace failed: {str(e)}")
        return {"success": False, "error": str(e)}

def setup_custom_fields(company):
    """
    Setup custom fields for Mozambique compliance
    
    Args:
        company (str): Company name
    """
    
    try:
        # Company NUIT field
        if not frappe.db.exists("Custom Field", {"fieldname": "nuit", "dt": "Company"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Company"
            custom_field.fieldname = "nuit"
            custom_field.label = "NUIT"
            custom_field.fieldtype = "Data"
            custom_field.insert_after = "tax_id"
            custom_field.in_standard_filter = 1
            custom_field.description = "Número Único de Identificação Tributária (da Empresa)"
            custom_field.insert()

        # Customer NUIT field
        if not frappe.db.exists("Custom Field", {"fieldname": "nuit", "dt": "Customer"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Customer"
            custom_field.fieldname = "nuit"
            custom_field.label = "NUIT"
            custom_field.fieldtype = "Data"
            custom_field.insert_after = "tax_id"
            custom_field.in_standard_filter = 1
            custom_field.in_list_view = 1
            # Not required; validation handled client/server-side
            custom_field.reqd = 0
            custom_field.description = "Número Único de Identificação Tributária"
            custom_field.insert()
    
        # Supplier NUIT field
        if not frappe.db.exists("Custom Field", {"fieldname": "nuit", "dt": "Supplier"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Supplier"
            custom_field.fieldname = "nuit"
            custom_field.label = "NUIT"
            custom_field.fieldtype = "Data"
            custom_field.insert_after = "tax_id"
            custom_field.in_standard_filter = 1
            custom_field.in_list_view = 1
            custom_field.reqd = 0
            custom_field.description = "Número Único de Identificação Tributária"
            custom_field.insert()
        
        # Sales Invoice fiscal fields
        if not frappe.db.exists("Custom Field", {"fieldname": "fiscal_series", "dt": "Sales Invoice"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Sales Invoice"
            custom_field.fieldname = "fiscal_series"
            custom_field.label = "Fiscal Series"
            custom_field.fieldtype = "Data"
            custom_field.insert_after = "naming_series"
            # Optional; numbering enforcement removed
            custom_field.reqd = 0
            custom_field.description = "Série fiscal da fatura"
            custom_field.insert()
        
        if not frappe.db.exists("Custom Field", {"fieldname": "fiscal_number", "dt": "Sales Invoice"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Sales Invoice"
            custom_field.fieldname = "fiscal_number"
            custom_field.label = "Fiscal Number"
            custom_field.fieldtype = "Data"
            custom_field.insert_after = "fiscal_series"
            custom_field.read_only = 1
            custom_field.description = "Número fiscal sequencial"
            custom_field.insert()
        
        # Auto-submit SAF-T to AT (Company setting)
        if not frappe.db.exists("Custom Field", {"fieldname": "auto_submit_saf_t_to_at", "dt": "Company"}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.dt = "Company"
            custom_field.fieldname = "auto_submit_saf_t_to_at"
            custom_field.label = "Auto-submit SAF-T to AT"
            custom_field.fieldtype = "Check"
            custom_field.insert_after = "tax_id"
            custom_field.description = "Automatically transmit monthly SAF-T files to the Tax Authority (uses configured or default endpoint)."
            custom_field.insert()

        # Ensure Integration Request has request_id field for idempotency if available
        try:
            if frappe.db.table_exists("tabIntegration Request") and not frappe.db.has_column("Integration Request", "request_id"):
                # Create custom field 'request_id'
                if not frappe.db.exists("Custom Field", {"fieldname": "request_id", "dt": "Integration Request"}):
                    cf = frappe.new_doc("Custom Field")
                    cf.dt = "Integration Request"
                    cf.fieldname = "request_id"
                    cf.label = "Request ID"
                    cf.fieldtype = "Data"
                    cf.insert_after = "service_call"
                    cf.description = "Idempotency key for requests"
                    cf.insert()
        except Exception:
            pass

        # Ensure existing NUIT fields are not required
        try:
            for dt in ("Customer", "Supplier"):
                cf = frappe.get_all("Custom Field", filters={"dt": dt, "fieldname": "nuit"}, pluck="name")
                for name in cf:
                    try:
                        frappe.db.set_value("Custom Field", name, "reqd", 0)
                    except Exception:
                        pass
        except Exception:
            pass

        # Backfill Company.nuit from Company.tax_id if missing
        try:
            company_doc = frappe.get_doc("Company", company)
            if not getattr(company_doc, "nuit", None) and getattr(company_doc, "tax_id", None):
                try:
                    frappe.db.set_value("Company", company_doc.name, "nuit", company_doc.tax_id)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception as e:
        frappe.log_error(f"Failed to setup custom fields: {str(e)}")
        frappe.throw(f"Custom fields setup failed: {str(e)}")

# Print format setup removed; using default UI print formats

def setup_company_settings(company):
    """
    Setup company-specific settings for Mozambique
    
    Args:
        company (str): Company name
    """
    
    try:
        company_doc = frappe.get_doc("Company", company)
        
        # Set default country to Mozambique
        if hasattr(company_doc, "country") and not company_doc.country:
            company_doc.country = "Mozambique"
        
        # Set default currency to MZN
        if hasattr(company_doc, "default_currency") and not company_doc.default_currency:
            company_doc.default_currency = "MZN"
        
        company_doc.save()
    except Exception as e:
        frappe.log_error(f"Failed to setup company settings: {str(e)}")
        # Do not block full setup if non-critical field missing in this ERPNext version
        return

def get_setup_status(company):
    """
    Get the setup status for Mozambique compliance
    
    Args:
        company (str): Company name
        
    Returns:
        dict: Setup status
    """
    
    status = {
        "chart_of_accounts": False,
        "vat_templates": False,
        "hr_payroll": False,
        "custom_fields": False,
        "print_formats": False,
        "company_settings": False
    }
    
    # Check Chart of Accounts
    accounts = frappe.get_all("Account", filters={"company": company}, limit=1)
    status["chart_of_accounts"] = len(accounts) > 0
    
    # Check VAT Templates
    vat_templates = frappe.get_all("Item Tax Template", filters={"company": company}, limit=1)
    status["vat_templates"] = len(vat_templates) > 0
    
    # Check HR & Payroll (HRMS may not be installed)
    try:
        salary_components = frappe.get_all("Salary Component", filters={"company": company}, limit=1)
        status["hr_payroll"] = len(salary_components) > 0
    except Exception:
        status["hr_payroll"] = False
    
    # Check Custom Fields
    custom_fields = frappe.get_all("Custom Field", filters={"dt": "Customer", "fieldname": "nuit"}, limit=1)
    status["custom_fields"] = len(custom_fields) > 0
    
    # Print Formats: não exigido (usaremos UI padrão)
    status["print_formats"] = True
    
    # Check Company Settings
    company_doc = frappe.get_doc("Company", company)
    status["company_settings"] = company_doc.country == "Mozambique" and company_doc.default_currency == "MZN"
    
    return status

@frappe.whitelist()
def get_first_company_setup_status():
    """Return setup status for the first Company on the site.

    Useful for non-interactive bench execute checks from scripts.
    """
    companies = frappe.get_all("Company", pluck="name", limit=1)
    if not companies:
        return {"company": None, "status": None}
    company = companies[0]
    return {"company": company, "status": get_setup_status(company)}

def run_setup():
    """
    Run setup for the current company
    """
    
    company = frappe.defaults.get_user_default("Company")
    
    if not company:
        frappe.throw(_("Please select a company first"))
    
    setup_mozambique_compliance(company)

def setup_all_companies():
    """
    Run Mozambique compliance setup for all companies on the current site
    
    Returns:
        list[str]: List of processed company names
    """
    try:
        companies = frappe.get_all("Company", pluck="name")
        for company_name in companies:
            setup_mozambique_compliance(company_name)
        return companies
    except Exception as e:
        frappe.log_error(f"setup_all_companies failed: {str(e)}")
        raise

def after_install():
    """Hook: run after the app is installed on a site."""
    ensure_workspace()
    ensure_hr_workspaces()

def after_migrate():
    """Hook: run after migrations to re-ensure workspace and idempotent setup bits."""
    ensure_workspace()
    ensure_hr_workspaces()

def ensure_hr_workspaces():
    """Ensure generic HR workspaces exist (labels vary by version)."""
    try:
        labels = ["HR and Payroll", "HR"]
        for label in labels:
            if not frappe.db.exists("Workspace", {"label": label}):
                ws = frappe.new_doc("Workspace")
                ws.label = label
                ws.public = 1
                ws.module = "HR"
                # Add minimal useful links if missing app content
                try:
                    ws.append("links", {
                        "type": "Link",
                        "label": "Employee",
                        "link_type": "DocType",
                        "link_to": "Employee",
                    })
                except Exception:
                    pass
                ws.insert()
    except Exception as e:
        frappe.log_error(f"Failed to ensure HR workspaces: {str(e)}")

# Debug helpers (safe to keep; no side-effects)
# Debug helpers removed for production cleanliness
