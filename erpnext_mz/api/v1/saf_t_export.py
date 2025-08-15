# -*- coding: utf-8 -*-
"""
SAF-T Export API for ERPNext Mozambique

This module provides API endpoints for SAF-T file export.
"""

import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=False)
def generate_saf_t(company, year, month):
    """
    Generate SAF-T files via API
    
    Args:
        company (str): Company name
        year (int): Year
        month (int): Month
        
    Returns:
        dict: API response with file information
    """
    
    try:
        # Validate inputs
        if not company:
            return build_response("error", "Company is required")
        
        if not year or not month:
            return build_response("error", "Year and month are required")
        
        # Check permissions
        if not frappe.has_permission("Company", doc=frappe.get_doc("Company", company)):
            return build_response("error", "Insufficient permissions")
        
        # Generate SAF-T files
        from ...modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
        
        result = generate_monthly_saf_t(company, int(year), int(month))
        
        return build_response("success", "SAF-T files generated successfully", result)
        
    except Exception as e:
        frappe.log_error(f"SAF-T API generation failed: {str(e)}")
        return build_response("error", f"Generation failed: {str(e)}")

@frappe.whitelist(allow_guest=False)
def get_saf_t_status(company, period):
    """
    Get SAF-T generation status
    
    Args:
        company (str): Company name
        period (str): Period (YYYY-MM)
        
    Returns:
        dict: API response with status
    """
    
    try:
        # Validate inputs
        if not company or not period:
            return build_response("error", "Company and period are required")
        
        # Check permissions
        if not frappe.has_permission("Company", doc=frappe.get_doc("Company", company)):
            return build_response("error", "Insufficient permissions")
        
        # Get SAF-T files for the period
        files = frappe.get_all("File",
                              filters={
                                  "attached_to_doctype": "Company",
                                  "attached_to_name": company,
                                  "file_name": ["like", f"SAFT_%_{period}_%"]
                              },
                              fields=["file_name", "creation", "file_size"])
        
        return build_response("success", "Status retrieved successfully", {"files": files})
        
    except Exception as e:
        frappe.log_error(f"SAF-T status API failed: {str(e)}")
        return build_response("error", f"Status retrieval failed: {str(e)}")

def build_response(status, message, data=None):
    """
    Build standardized API response
    
    Args:
        status (str): Response status
        message (str): Response message
        data (dict): Response data
        
    Returns:
        dict: Standardized response
    """
    
    response = {
        "status": status,
        "message": message,
        "timestamp": frappe.utils.now_datetime().isoformat()
    }
    
    if data:
        response["data"] = data
    
    return response
