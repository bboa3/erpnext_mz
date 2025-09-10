# Copyright (c) 2025, ERPNext MZ and contributors
# For license information, please see license.txt

import frappe


def ensure_account(company_name: str, name: str, root_type: str, account_type: str | None = None, parent_account: str | None = None, account_number: str | None = None, is_group: bool = False):
    """
    Utility function to ensure an account exists, creating it if necessary.
    
    This function is used throughout ERPNext MZ to create accounts consistently
    with proper parent-child relationships and error handling.
    
    Args:
        company_name (str): Company name
        name (str): Account name
        root_type (str): Root type (Asset, Liability, Income, Expense, Equity)
        account_type (str, optional): Account type (Bank, Tax, etc.)
        parent_account (str, optional): Parent account name
        account_number (str, optional): Account number
        is_group (bool): Whether this is a group account (default: False)
    
    Returns:
        str: Account name if successful, None if failed
    
    Example:
        # Create a bank account
        account_name = ensure_account(
            company_name="Test Company",
            name="Test Bank Account",
            root_type="Asset",
            account_type="Bank",
            parent_account="Bank Accounts",
            account_number="11.01.01"
        )
        
        # Create a group account
        group_name = ensure_account(
            company_name="Test Company",
            name="New Group",
            root_type="Asset",
            is_group=True
        )
    """
    try:
        # Check if account already exists
        if frappe.db.exists("Account", {"company": company_name, "account_name": name}):
            return frappe.get_value("Account", {"company": company_name, "account_name": name}, "name")
        
        # Find parent account
        parent_acc = None
        if parent_account:
            parent_acc = frappe.db.exists("Account", {"company": company_name, "account_name": parent_account})
            if not parent_acc:
                # Create parent account as a group
                parent_doc = frappe.new_doc("Account")
                parent_doc.company = company_name
                parent_doc.account_name = parent_account
                parent_doc.root_type = root_type
                parent_doc.is_group = 1
                parent_doc.insert(ignore_permissions=True)
                parent_acc = parent_doc.name
                print(f"✅ Created parent account: {parent_account}")
            else:
                # Get the existing parent account name
                parent_acc = frappe.get_value("Account", {"company": company_name, "account_name": parent_account}, "name")
        
        # Create the account
        acc = frappe.new_doc("Account")
        acc.company = company_name
        acc.account_name = name
        acc.root_type = root_type
        acc.is_group = 1 if is_group else 0
        if account_type:
            acc.account_type = account_type
        if account_number:
            acc.account_number = account_number
        if parent_acc:
            acc.parent_account = parent_acc
        acc.insert(ignore_permissions=True)
        print(f"✅ Created account: {name}")
        return acc.name
    except Exception as e:
        frappe.log_error(f"Error creating account {name}: {str(e)}", "Account Creation Error")
        return None


def get_cost_center(company_name: str):
    """
    Utility function to find an existing cost center.
    
    Args:
        company_name (str): Company name
    
    Returns:
        str: Cost center name if found, None if not found
    """
    try:
        # First, try to get the company's default cost center
        company_cost_center = frappe.get_value("Company", company_name, "cost_center")
        if company_cost_center and frappe.db.exists("Cost Center", company_cost_center):
            return company_cost_center
        
        # Get company abbreviation
        company_abbr = frappe.get_value('Company', company_name, 'abbr')
        if not company_abbr:
            print(f"❌ Could not get company abbreviation for {company_name}")
            return None
        
        # Try common cost center names with exact name matching
        common_names = [
            f"Main - {company_abbr}",
            f"Principal - {company_abbr}",
            "Main",
            "Principal",
        ]
        
        for name in common_names:
            # Check if cost center exists with exact name match
            cost_center = frappe.db.get_value("Cost Center", 
                {"name": name, "company": company_name}, "name")
            if cost_center:
                print(f"✅ Found cost center: {cost_center}")
                return cost_center
        
        # Try to find any cost center for this company
        company_cost_centers = frappe.get_all("Cost Center", 
            filters={"company": company_name, "disabled": 0}, 
            fields=["name"], 
            limit=1)
        
        if company_cost_centers:
            print(f"✅ Found any cost center: {company_cost_centers[0].name}")
            return company_cost_centers[0].name
        
        print(f"❌ No cost center found for company {company_name}")
        return None
            
    except Exception as e:
        frappe.log_error(f"Error getting cost center for {company_name}: {str(e)}", "Cost Center Retrieval Error")
        print(f"❌ Error getting cost center: {str(e)}")
        return None




        