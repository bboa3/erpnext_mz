# -*- coding: utf-8 -*-
"""
AT Integration API for ERPNext Mozambique

This module provides API endpoints for AT (Autoridade Tributária) integration.
"""

import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=False)
def transmit_invoice(invoice_name):
    """
    Transmit invoice to AT via API
    
    Args:
        invoice_name (str): Sales Invoice name
        
    Returns:
        dict: API response with transmission result
    """
    
    try:
        # Validate inputs
        if not invoice_name:
            return build_response("error", "Invoice name is required")
        
        # Check if invoice exists
        if not frappe.db.exists("Sales Invoice", invoice_name):
            return build_response("error", "Invoice not found")
        
        # Check permissions
        invoice = frappe.get_doc("Sales Invoice", invoice_name)
        if not frappe.has_permission("Sales Invoice", doc=invoice):
            return build_response("error", "Insufficient permissions")
        
        # Transmit to AT with idempotency guard
        from ...modules.tax_compliance.at_integration import ATIntegration
        
        at_integration = ATIntegration(invoice.company)
        # Pre-check Integration Request for Completed result
        try:
            filters = {
                "reference_doctype": "Company",
                "reference_docname": invoice.company,
                "integration_request_service": "AT API",
                "status": "Completed",
            }
            if frappe.db.has_column("Integration Request", "request_id"):
                filters["request_id"] = invoice_name
                existing = frappe.get_all("Integration Request", filters=filters, limit=1)
            else:
                existing = frappe.get_all(
                    "Integration Request",
                    filters=filters | {"data": ["like", f"%\"document_name\": \"{invoice_name}\"%"]},
                    limit=1,
                )
            if existing:
                return build_response("success", "Already transmitted", {"invoice": invoice_name})
        except Exception:
            pass

        result = at_integration.transmit_invoice(invoice_name)
        
        if result.get("success"):
            return build_response("success", "Invoice transmitted successfully", result)
        else:
            return build_response("error", f"Transmission failed: {result.get('message')}", result)
        
    except Exception as e:
        frappe.log_error(f"AT integration API failed: {str(e)}")
        return build_response("error", f"Transmission failed: {str(e)}")

@frappe.whitelist(allow_guest=False)
def transmit_saf_t(company, period, file_type):
    """
    Transmit SAF-T file to AT via API
    
    Args:
        company (str): Company name
        period (str): Period (YYYY-MM)
        file_type (str): 'sales' or 'payroll'
        
    Returns:
        dict: API response with transmission result
    """
    
    try:
        # Validate inputs
        if not company or not period or not file_type:
            return build_response("error", "Company, period, and file type are required")
        
        if file_type not in ['sales', 'payroll']:
            return build_response("error", "File type must be 'sales' or 'payroll'")
        
        # Check permissions
        if not frappe.has_permission("Company", doc=frappe.get_doc("Company", company)):
            return build_response("error", "Insufficient permissions")
        
        # Get SAF-T file (newest) and read its content for real checksum
        files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Company",
                "attached_to_name": company,
                "file_name": ["like", f"SAFT_{file_type}_{period}_%"],
            },
            fields=["name", "file_name", "file_url", "is_private"],
            order_by="creation desc",
            limit=1,
        )
        
        if not files:
            return build_response("error", f"SAF-T {file_type} file not found for period {period}")
        
        # Transmit to AT
        from ...modules.tax_compliance.at_integration import ATIntegration
        
        at_integration = ATIntegration(company)
        
        # Read file content from File doc
        file_doc = frappe.get_doc("File", files[0].name)
        xml_content = None
        try:
            # Prefer .get_content() if available
            xml_content = file_doc.get_content()  # returns bytes
            if isinstance(xml_content, bytes):
                xml_content = xml_content.decode("utf-8", errors="replace")
        except Exception:
            # Fallback: read from file_url on disk
            from frappe.utils import get_site_path
            import os
            path = file_doc.file_url or ""
            if path.startswith("/files/"):
                full_path = os.path.join(get_site_path(), "public" + path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        xml_content = f.read()
                except Exception:
                    xml_content = None
        if not xml_content:
            return build_response("error", "Unable to read SAF-T file content")

        # Compute checksum
        import hashlib
        checksum = hashlib.sha256(xml_content.encode("utf-8")).hexdigest()

        # Prepare SAF-T data
        saf_t_data = {
            "period": period,
            "xml_content": xml_content,
            "checksum": checksum,
        }
        
        result = at_integration.transmit_saf_t(saf_t_data, file_type)
        
        if result.get("success"):
            return build_response("success", f"SAF-T {file_type} transmitted successfully", result)
        else:
            return build_response("error", f"Transmission failed: {result.get('message')}", result)
        
    except Exception as e:
        frappe.log_error(f"AT SAF-T API failed: {str(e)}")
        return build_response("error", f"Transmission failed: {str(e)}")

@frappe.whitelist(allow_guest=False)
def get_transmission_status(company, period=None):
    """
    Get AT transmission status
    
    Args:
        company (str): Company name
        period (str): Optional period filter
        
    Returns:
        dict: API response with transmission status
    """
    
    try:
        # Validate inputs
        if not company:
            return build_response("error", "Company is required")
        
        # Check permissions
        if not frappe.has_permission("Company", doc=frappe.get_doc("Company", company)):
            return build_response("error", "Insufficient permissions")
        
        # Build filters
        filters = {"company": company}
        if period:
            filters["document_name"] = ["like", f"%{period}%"]
        
        # Get transmission logs from Integration Request
        logs = frappe.get_all(
            "Integration Request",
            filters={
                "reference_doctype": "Company",
                "reference_docname": company,
                "integration_request_service": "AT API",
                **({} if not period else {"modified": ["like", f"{period}%"]}),
            },
            fields=["name", "status", "modified", "data", "output"],
            order_by="modified desc",
            limit=100,
        )
        
        return build_response("success", "Status retrieved successfully", {"logs": logs})
        
    except Exception as e:
        frappe.log_error(f"AT status API failed: {str(e)}")
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
        "timestamp": frappe.utils.now_datetime().isoformat(),
    }
    if data is not None:
        response["data"] = data
    return response

@frappe.whitelist()
def configure_at_integration(company, api_endpoint, api_key, enabled=True):
    """
    Configure AT integration settings
    
    Args:
        company (str): Company name
        api_endpoint (str): AT API endpoint
        api_key (str): AT API key
        enabled (bool): Enable/disable integration
        
    Returns:
        dict: API response
    """
    
    try:
        # Validate inputs
        if not company or not api_endpoint or not api_key:
            return build_response("error", "Company, API endpoint, and API key are required")
        
        # Check permissions
        if not frappe.has_permission("Company", "write", company):
            return build_response("error", "Insufficient permissions")
        
        # Update company settings
        company_doc = frappe.get_doc("Company", company)
        
        # Create custom fields if they don't exist
        _create_at_custom_fields(company)
        
        # Update settings
        company_doc.at_api_endpoint = api_endpoint
        company_doc.at_api_key = api_key
        company_doc.at_integration_enabled = enabled
        company_doc.save()
        
        return build_response("success", "AT integration configured successfully")
        
    except Exception as e:
        frappe.log_error(f"AT configuration API failed: {str(e)}")
        return build_response("error", f"Configuration failed: {str(e)}")

def _create_at_custom_fields(company):
    """
    Create AT integration custom fields
    
    Args:
        company (str): Company name
    """
    
    # AT API endpoint field
    if not frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": "at_api_endpoint"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Company"
        custom_field.fieldname = "at_api_endpoint"
        custom_field.label = "AT API Endpoint"
        custom_field.fieldtype = "Data"
        # Insert position: after "tax_id" or fallback to top if not available
        custom_field.insert_after = "tax_id"
        custom_field.description = "AT API endpoint URL"
        custom_field.insert()
    
    # AT API key field
    if not frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": "at_api_key"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Company"
        custom_field.fieldname = "at_api_key"
        custom_field.label = "AT API Key"
        custom_field.fieldtype = "Password"
        custom_field.insert_after = "at_api_endpoint"
        custom_field.description = "AT API authentication key"
        custom_field.insert()
    
    # AT integration enabled field
    if not frappe.db.exists("Custom Field", {"dt": "Company", "fieldname": "at_integration_enabled"}):
        custom_field = frappe.new_doc("Custom Field")
        custom_field.dt = "Company"
        custom_field.fieldname = "at_integration_enabled"
        custom_field.label = "AT Integration Enabled"
        custom_field.fieldtype = "Check"
        custom_field.insert_after = "at_api_key"
        custom_field.description = "Enable AT integration for this company"
        custom_field.insert()
