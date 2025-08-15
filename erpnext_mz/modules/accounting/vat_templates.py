# -*- coding: utf-8 -*-
"""
VAT Templates for Mozambique

This module provides VAT templates for Mozambique tax rates:
- VAT 16% (standard rate)
- VAT 5% (reduced rate for health/education)
- VAT 0% (exports and exempt goods/services)
"""

import frappe
from frappe import _

def setup_mozambique_vat_templates(company):
    """
    Setup Mozambique VAT templates for a company
    
    Args:
        company (str): Company name
    """
    
    # VAT 16% - Standard Rate
    create_vat_template(
        "IVA 16% - Padrão",
        "16",
        "VAT",
        "VAT",
        company,
        "IVA 16% - Taxa padrão para produtos e serviços"
    )
    
    # VAT 5% - Reduced Rate
    create_vat_template(
        "IVA 5% - Taxa Reduzida",
        "5",
        "VAT",
        "VAT",
        company,
        "IVA 5% - Taxa reduzida para saúde, educação e outros setores específicos"
    )
    
    # VAT 0% - Zero Rate
    create_vat_template(
        "IVA 0% - Isento",
        "0",
        "VAT",
        "VAT",
        company,
        "IVA 0% - Exportações e bens/serviços isentos"
    )
    
    # Create Tax Categories
    create_tax_categories(company)
    
    frappe.msgprint(_("Mozambique VAT templates created successfully"))

def create_vat_template(name, rate, tax_type, account_type, company, description):
    """
    Create a VAT template if it doesn't exist
    
    Args:
        name (str): Template name
        rate (str): Tax rate percentage
        tax_type (str): Type of tax
        account_type (str): Account type
        company (str): Company name
        description (str): Template description
    """
    
    # Check if template already exists (match by title + company)
    if frappe.get_all("Item Tax Template", filters={"title": name, "company": company}, limit=1):
        return
    
    # Create the tax template
    # Ensure tax account exists for the company
    account_name = None
    if rate == "16":
        account_name = "VAT 16% - Output"
    elif rate == "5":
        account_name = "VAT 5% - Output"
    else:
        account_name = "VAT 0% - Output"

    if not frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        # Create under a sensible parent: try "Duties and Taxes" or fallback to first Liability group
        parent = frappe.db.get_value("Account", {"company": company, "account_name": "Duties and Taxes"}, "name")
        if not parent:
            parent = frappe.db.get_value("Account", {"company": company, "root_type": "Liability", "is_group": 1}, "name")

        acc = frappe.new_doc("Account")
        acc.account_name = account_name
        acc.company = company
        acc.is_group = 0
        acc.root_type = "Liability"
        acc.account_type = "Tax"
        if parent:
            acc.parent_account = parent
        acc.insert()

    account = frappe.db.get_value("Account", {"account_name": account_name, "company": company}, "name")

    template = frappe.new_doc("Item Tax Template")
    template.title = name
    template.company = company
    template.taxes = []

    template.append("taxes", {
        "tax_type": account,
        "tax_rate": float(rate),
        "description": description,
    })

    template.insert()
    
    frappe.msgprint(_("VAT template {0} created successfully").format(name))

def create_tax_categories(company):
    """
    Create tax categories for Mozambique
    
    Args:
        company (str): Company name
    """
    
    categories = [
        {
            "name": "Produtos Padrão",
            "description": "Produtos com IVA 16%",
            "is_default": 1
        },
        {
            "name": "Saúde e Educação",
            "description": "Serviços com IVA 5%",
            "is_default": 0
        },
        {
            "name": "Exportações",
            "description": "Produtos para exportação com IVA 0%",
            "is_default": 0
        },
        {
            "name": "Isentos",
            "description": "Bens e serviços isentos de IVA",
            "is_default": 0
        }
    ]
    
    for category_data in categories:
        create_tax_category(category_data, company)

def create_tax_category(category_data, company):
    """
    Create a tax category if it doesn't exist
    
    Args:
        category_data (dict): Category data
        company (str): Company name
    """
    
    category_name = category_data["name"]
    
    # Check if category already exists
    if frappe.db.exists("Tax Category", {"name": category_name}):
        return
    
    # Create the tax category
    category = frappe.new_doc("Tax Category")
    category.title = category_name
    category.description = category_data.get("description")
    category.is_default = category_data.get("is_default", 0)
    try:
        category.company = company  # set if field exists
    except Exception:
        pass
    category.insert()
    
    frappe.msgprint(_("Tax category {0} created successfully").format(category_name))

def get_vat_rate_for_item(item_code, company):
    """
    Get VAT rate for a specific item
    
    Args:
        item_code (str): Item code
        company (str): Company name
        
    Returns:
        float: VAT rate percentage
    """
    
    item = frappe.get_doc("Item", item_code)
    
    if not item:
        return 16.0  # Default to standard rate
    
    # Check if item has specific tax category (field may not exist on some versions)
    tax_category = getattr(item, 'tax_category', None)
    if tax_category:
        if "5%" in tax_category:
            return 5.0
        elif "0%" in tax_category or "Isento" in tax_category:
            return 0.0
    
    # Default to standard rate
    return 16.0

def calculate_vat_amount(base_amount, vat_rate):
    """
    Calculate VAT amount
    
    Args:
        base_amount (float): Base amount before VAT
        vat_rate (float): VAT rate percentage
        
    Returns:
        float: VAT amount
    """
    
    return (base_amount * vat_rate) / 100

def get_mozambique_vat_templates(company):
    """
    Get all Mozambique VAT templates for a company
    
    Args:
        company (str): Company name
        
    Returns:
        list: List of VAT template names
    """
    
    templates = frappe.get_all("Item Tax Template",
                              filters={"company": company},
                              fields=["name", "description"])
    return templates
