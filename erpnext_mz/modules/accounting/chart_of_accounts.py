# -*- coding: utf-8 -*-
"""
Chart of Accounts for Mozambique (IFRS Compliant)

This module provides the standard chart of accounts structure
aligned with IFRS requirements for Mozambique.
"""

import frappe
from frappe import _

def setup_mozambique_chart_of_accounts(company):
    """
    Setup Mozambique Chart of Accounts for a company
    
    Args:
        company (str): Company name
    """
    
    # If the company already has a Chart of Accounts, skip to avoid conflicts
    existing = frappe.get_all("Account", filters={"company": company}, limit=1)
    if existing:
        frappe.msgprint(_(f"Chart of Accounts already exists for {company}, skipping creation"))
        return

    # Prefer JSON template import if present
    try:
        from frappe.utils import get_app_path
        import json as _json
        import os as _os
        template_path = _os.path.join(get_app_path("erpnext_mz"), "modules", "accounting", "coa_mz.json")
        if _os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                data = _json.load(f)
            _import_coa_from_json(data, company)
            return
    except Exception:
        pass

    # Root accounts structure
    root_accounts = [
        {
            "account_name": "Ativos",
            "parent_account": "",
            "is_group": 1,
            "account_type": "Asset",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Passivos",
            "parent_account": "",
            "is_group": 1,
            "account_type": "Liability",
            "root_type": "Liability",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Património",
            "parent_account": "",
            "is_group": 1,
            "account_type": "Equity",
            "root_type": "Equity",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Receitas",
            "parent_account": "",
            "is_group": 1,
            "account_type": "Income",
            "root_type": "Income",
            "report_type": "Profit and Loss"
        },
        {
            "account_name": "Custos",
            "parent_account": "",
            "is_group": 1,
            "account_type": "Expense",
            "root_type": "Expense",
            "report_type": "Profit and Loss"
        }
    ]
    
    # Asset accounts
    asset_accounts = [
        {
            "account_name": "Ativos Correntes",
            "parent_account": "Ativos",
            "is_group": 1,
            "account_type": "Asset",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Caixa e Equivalentes",
            "parent_account": "Ativos Correntes",
            "is_group": 1,
            "account_type": "Bank",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Contas a Receber",
            "parent_account": "Ativos Correntes",
            "is_group": 1,
            "account_type": "Receivable",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Inventários",
            "parent_account": "Ativos Correntes",
            "is_group": 1,
            "account_type": "Stock",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Ativos Não Correntes",
            "parent_account": "Ativos",
            "is_group": 1,
            "account_type": "Asset",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Imobilizado",
            "parent_account": "Ativos Não Correntes",
            "is_group": 1,
            "account_type": "Fixed Asset",
            "root_type": "Asset",
            "report_type": "Balance Sheet"
        }
    ]
    
    # Liability accounts
    liability_accounts = [
        {
            "account_name": "Passivos Correntes",
            "parent_account": "Passivos",
            "is_group": 1,
            "account_type": "Liability",
            "root_type": "Liability",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Contas a Pagar",
            "parent_account": "Passivos Correntes",
            "is_group": 1,
            "account_type": "Payable",
            "root_type": "Liability",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "IVA a Pagar",
            "parent_account": "Passivos Correntes",
            "is_group": 0,
            "account_type": "Tax",
            "root_type": "Liability",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "INSS a Pagar",
            "parent_account": "Passivos Correntes",
            "is_group": 0,
            "account_type": "Tax",
            "root_type": "Liability",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "IRPS a Pagar",
            "parent_account": "Passivos Correntes",
            "is_group": 0,
            "account_type": "Tax",
            "root_type": "Liability",
            "report_type": "Balance Sheet"
        }
    ]
    
    # Equity accounts
    equity_accounts = [
        {
            "account_name": "Capital Social",
            "parent_account": "Património",
            "is_group": 0,
            "account_type": "Equity",
            "root_type": "Equity",
            "report_type": "Balance Sheet"
        },
        {
            "account_name": "Lucros Retidos",
            "parent_account": "Património",
            "is_group": 0,
            "account_type": "Equity",
            "root_type": "Equity",
            "report_type": "Balance Sheet"
        }
    ]
    
    # Income accounts
    income_accounts = [
        {
            "account_name": "Vendas",
            "parent_account": "Receitas",
            "is_group": 1,
            "account_type": "Income",
            "root_type": "Income",
            "report_type": "Profit and Loss"
        },
        {
            "account_name": "Vendas de Produtos",
            "parent_account": "Vendas",
            "is_group": 0,
            "account_type": "Income",
            "root_type": "Income",
            "report_type": "Profit and Loss"
        },
        {
            "account_name": "Vendas de Serviços",
            "parent_account": "Vendas",
            "is_group": 0,
            "account_type": "Income",
            "root_type": "Income",
            "report_type": "Profit and Loss"
        }
    ]
    
    # Expense accounts
    expense_accounts = [
        {
            "account_name": "Custos dos Produtos Vendidos",
            "parent_account": "Custos",
            "is_group": 1,
            "account_type": "Expense",
            "root_type": "Expense",
            "report_type": "Profit and Loss"
        },
        {
            "account_name": "Despesas Operacionais",
            "parent_account": "Custos",
            "is_group": 1,
            "account_type": "Expense",
            "root_type": "Expense",
            "report_type": "Profit and Loss"
        },
        {
            "account_name": "Despesas de Pessoal",
            "parent_account": "Despesas Operacionais",
            "is_group": 1,
            "account_type": "Expense",
            "root_type": "Expense",
            "report_type": "Profit and Loss"
        }
    ]
    
    # Create all accounts
    all_accounts = (root_accounts + asset_accounts + liability_accounts + 
                   equity_accounts + income_accounts + expense_accounts)
    
    # Create root accounts first
    for account_data in root_accounts:
        create_account(account_data, company)

    # Then create grouped accounts in logical order
    for group in (asset_accounts, liability_accounts, equity_accounts, income_accounts, expense_accounts):
        for account_data in group:
            create_account(account_data, company)

def create_account(account_data, company):
    """
    Create an account if it doesn't exist
    
    Args:
        account_data (dict): Account data
        company (str): Company name
    """
    account_name = account_data["account_name"]
    
    # Check if account already exists
    if frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        return
    
    # Create the account
    account = frappe.new_doc("Account")
    account.update(account_data)
    account.company = company
    # Resolve parent account to full account path if provided
    if account.parent_account:
        parent = frappe.db.get_value("Account", {"account_name": account.parent_account, "company": company}, "name")
        if parent:
            account.parent_account = parent
    account.insert()
    
    frappe.msgprint(_("Account {0} created successfully").format(account_name))

def _import_coa_from_json(data, company):
    """Import Chart of Accounts from JSON structure similar to ERPNext templates."""
    inserted = set()
    # Insert roots first
    for row in data:
        if not row.get("parent_account"):
            create_account(row, company)
            inserted.add(row.get("account_name"))
    # Then children in multiple passes
    for _ in range(3):
        for row in data:
            name = row.get("account_name")
            if name in inserted:
                continue
            parent = row.get("parent_account")
            if not parent or frappe.db.exists("Account", {"account_name": parent, "company": company}):
                create_account(row, company)
                inserted.add(name)

def get_mozambique_accounts(company):
    """
    Get all Mozambique accounts for a company
    
    Args:
        company (str): Company name
        
    Returns:
        list: List of account names
    """
    accounts = frappe.get_all("Account", 
                             filters={"company": company},
                             fields=["account_name", "parent_account", "is_group"])
    return accounts
