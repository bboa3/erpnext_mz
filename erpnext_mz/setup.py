# -*- coding: utf-8 -*-
"""
Setup Script for ERPNext Mozambique Custom App

This script sets up all Mozambique compliance features:
- Chart of Accounts
- VAT templates
- HR & Payroll components
- Custom fields
- Print formats
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
        frappe.msgprint(_("Starting Mozambique compliance setup for company: {0}").format(company))
        
        # 1. Setup Chart of Accounts
        frappe.msgprint(_("Setting up Chart of Accounts..."))
        from .modules.accounting.chart_of_accounts import setup_mozambique_chart_of_accounts
        setup_mozambique_chart_of_accounts(company)
        
        # 2. Setup VAT Templates
        frappe.msgprint(_("Setting up VAT templates..."))
        from .modules.accounting.vat_templates import setup_mozambique_vat_templates
        setup_mozambique_vat_templates(company)
        
        # 3. Setup HR & Payroll Components
        frappe.msgprint(_("Setting up HR & Payroll components..."))
        from .modules.hr_payroll.inss_irps import create_inss_salary_component, create_irps_salary_component
        create_inss_salary_component(company)
        create_irps_salary_component(company)
        
        # 3.1 Setup Benefits in Kind
        frappe.msgprint(_("Setting up Benefits in Kind..."))
        from .modules.hr_payroll.benefits_in_kind import create_benefits_custom_fields
        create_benefits_custom_fields()
        
        # 4. Setup Custom Fields
        frappe.msgprint(_("Setting up custom fields..."))
        setup_custom_fields(company)
        
        # 5. Setup Print Formats
        frappe.msgprint(_("Setting up print formats..."))
        setup_print_formats(company)
        
        # 6. Setup Company Settings
        frappe.msgprint(_("Setting up company settings..."))
        setup_company_settings(company)
        
        frappe.msgprint(_("Mozambique compliance setup completed successfully!"))
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
        if not frappe.db.exists("Workspace", {"label": "ERPNext Mozambique"}):
            ws = frappe.new_doc("Workspace")
            ws.label = "ERPNext Mozambique"
            ws.title = "ERPNext Mozambique"
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
            # Add basic cards/links (best-effort; skip if validation blocks)
            try:
                ws.reload()
                ws.append("links", {
                    "type": "Card Break",
                    "label": "Compliance",
                })
                ws.append("links", {
                    "type": "Link",
                    "label": "Integration Requests (AT)",
                    "link_type": "DocType",
                    "link_to": "Integration Request",
                })
                ws.append("links", {
                    "type": "Link",
                    "label": "Files (SAF-T)",
                    "link_type": "DocType",
                    "link_to": "File",
                })
                ws.append("links", {
                    "type": "Card Break",
                    "label": "Setup",
                })
                ws.append("links", {
                    "type": "Link",
                    "label": "Item Tax Templates",
                    "link_type": "DocType",
                    "link_to": "Item Tax Template",
                })
                ws.append("links", {
                    "type": "Link",
                    "label": "Tax Categories",
                    "link_type": "DocType",
                    "link_to": "Tax Category",
                })
                ws.flags.ignore_permissions = True
                ws.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                pass
        else:
            # Ensure existing workspace is public and bound to our module
            try:
                ws = frappe.get_doc("Workspace", {"label": "ERPNext Mozambique"})
                if not getattr(ws, "public", 0):
                    frappe.db.set_value("Workspace", ws.name, "public", 1)
                    frappe.db.commit()
                if getattr(ws, "module", "") != "ERPNext Mozambique":
                    frappe.db.set_value("Workspace", ws.name, "module", "ERPNext Mozambique")
                    frappe.db.commit()
                if not getattr(ws, "title", None):
                    frappe.db.set_value("Workspace", ws.name, "title", ws.label or "ERPNext Mozambique")
                    frappe.db.commit()
            except Exception:
                pass
        # Ensure HR workspaces exist to prevent 'Module not found' errors
        ensure_hr_workspaces()
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
        # Also ensure HR module exists to avoid 'Module HR not found' errors on Desk
        try:
            if not frappe.db.exists("Module Def", "HR"):
                md_hr = frappe.new_doc("Module Def")
                md_hr.module_name = "HR"
                try:
                    # Prefer hrms app if installed
                    if "hrms" in frappe.get_installed_apps():
                        md_hr.app_name = "hrms"
                    else:
                        md_hr.app_name = "erpnext"
                except Exception:
                    pass
                md_hr.insert()
            # Ensure alternate label used by some versions
            if not frappe.db.exists("Module Def", "HR and Payroll"):
                md_hrp = frappe.new_doc("Module Def")
                md_hrp.module_name = "HR and Payroll"
                try:
                    if "hrms" in frappe.get_installed_apps():
                        md_hrp.app_name = "hrms"
                    else:
                        md_hrp.app_name = "erpnext"
                except Exception:
                    pass
                md_hrp.insert()
        except Exception:
            # Ignore if Module Def is protected by core app
            pass
    except Exception as e:
        frappe.log_error(f"Failed to ensure Module Def: {str(e)}")

def setup_custom_fields(company):
    """
    Setup custom fields for Mozambique compliance
    
    Args:
        company (str): Company name
    """
    
    try:
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
            custom_field.reqd = 1
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
            custom_field.reqd = 1
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
            custom_field.reqd = 1
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
    except Exception as e:
        frappe.log_error(f"Failed to setup custom fields: {str(e)}")
        frappe.throw(f"Custom fields setup failed: {str(e)}")

def setup_print_formats(company):
    """
    Setup print formats for Mozambique compliance
    
    Args:
        company (str): Company name
    """
    
    try:
        # Mozambique Standard Invoice Print Format
        if not frappe.db.exists("Print Format", {"name": "Mozambique Standard", "doc_type": "Sales Invoice"}):
            print_format = frappe.new_doc("Print Format")
            print_format.name = "Mozambique Standard"
            print_format.doc_type = "Sales Invoice"
            print_format.standard = 0
            print_format.custom_format = 1
            print_format.print_format_type = "Jinja"
            # Builder data must be valid JSON even if unused
            print_format.format_data = "[]"
            # HTML body of the print format
            print_format.html = """
<div class=\"mozambique-invoice\"> 
  <div class=\"header\">
    <h1>FATURA</h1>
    <div class=\"fiscal-info\">
      <p><strong>Série:</strong> {{ doc.fiscal_series }}</p>
      <p><strong>Número Fiscal:</strong> {{ doc.fiscal_number }}</p>
    </div>
  </div>
  <div class=\"company-details\">
    <h2>{{ doc.company }}</h2>
  </div>
  <div class=\"customer-details\">
    <h3>Cliente:</h3>
    <p>{{ doc.customer_name }}</p>
  </div>
  <div class=\"invoice-details\">
    <p><strong>Data:</strong> {{ doc.posting_date }}</p>
    <p><strong>Vencimento:</strong> {{ doc.due_date }}</p>
  </div>
  <table class=\"items-table\">
    <thead>
      <tr>
        <th>Item</th>
        <th>Descrição</th>
        <th>Qtd</th>
        <th>Preço</th>
        <th>Total</th>
      </tr>
    </thead>
    <tbody>
      {% for item in doc.items %}
      <tr>
        <td>{{ item.item_code }}</td>
        <td>{{ item.item_name }}</td>
        <td>{{ item.qty }}</td>
        <td>{{ item.rate }}</td>
        <td>{{ item.amount }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <div class=\"totals\">
    <p><strong>Subtotal:</strong> {{ doc.net_total }}</p>
    <p><strong>IVA:</strong> {{ doc.total_taxes_and_charges }}</p>
    <p><strong>Total:</strong> {{ doc.grand_total }}</p>
  </div>
</div>
            """

            print_format.insert()
            frappe.msgprint(_("✅ Print format 'Mozambique Standard' created for {0}").format(company))
        else:
            frappe.msgprint(_("ℹ️ Print format 'Mozambique Standard' already exists for {0}").format(company))
    except Exception as e:
        frappe.log_error(f"Failed to setup print formats: {str(e)}")
        frappe.throw(f"Print formats setup failed: {str(e)}")

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
    
    # Check Print Formats
    print_formats = frappe.get_all("Print Format", filters={"name": "Mozambique Standard"}, limit=1)
    status["print_formats"] = len(print_formats) > 0
    
    # Check Company Settings
    company_doc = frappe.get_doc("Company", company)
    status["company_settings"] = company_doc.country == "Mozambique" and company_doc.default_currency == "MZN"
    
    return status

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
def debug_item_tax_template_detail_fields():
    import json
    meta = frappe.get_meta("Item Tax Template Detail")
    fields = [
        {
            "fieldname": df.fieldname,
            "fieldtype": df.fieldtype,
            "options": getattr(df, "options", ""),
        }
        for df in meta.fields
    ]
    print(json.dumps(fields, indent=2))

@frappe.whitelist()
def debug_workspace_status():
	try:
		ws = frappe.get_all("Workspace", filters={"label": "ERPNext Mozambique"}, fields=["name", "public", "module", "label"])
		md = frappe.get_all("Module Def", filters={"module_name": ["in", ["ERPNext Mozambique", "HR", "HR and Payroll"]]}, fields=["module_name"])
		return {"workspace": ws, "module_defs": md}
	except Exception as e:
		return {"error": str(e)}
