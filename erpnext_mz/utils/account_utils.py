# Copyright (c) 2025, ERPNext MZ and contributors
# For license information, please see license.txt

import frappe

def get_account_by_number(company_name: str, account_number: str) -> str | None:
    """Return the Account name for a given company and account_number, or None.

    The Account DocType stores an "account_number" field which is unique per company
    in a well-formed chart. This helper fetches the document name by that number.
    """
    try:
        return frappe.db.get_value(
            "Account", {"company": company_name, "account_number": account_number}, "name"
        )
    except Exception as e:
        frappe.log_error(f"Error fetching account by number {account_number}: {str(e)}", "Account Lookup Error")
        return None


def require_account_by_number(company_name: str, account_number: str, purpose: str | None = None) -> str:
    """Fetch an account by number and raise a clear error if not found.

    Args:
        company_name: Company
        account_number: e.g. "21.02.01"
        purpose: Optional context for error messages
    Returns:
        Account document name
    Raises:
        frappe.ValidationError if account is not found
    """
    name = get_account_by_number(company_name, account_number)
    if not name:
        msg = f"Missing required account {account_number} for company {company_name}"
        if purpose:
            msg = f"{msg} ({purpose})"
        frappe.throw(msg)
    return name


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




        