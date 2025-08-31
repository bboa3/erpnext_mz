#!/usr/bin/env python3
"""
Disable Existing Print Formats Script

This script disables all existing print formats before creating new Mozambique-specific ones.
This ensures clean deployment without conflicts between old and new formats.
"""

import frappe
from frappe import _


@frappe.whitelist()
def disable_all_existing_print_formats():
    """
    Disable all existing print formats to prepare for new Mozambique formats
    """
    try:
        # Get all print formats
        existing_formats = frappe.get_all(
            "Print Format",
            fields=["name", "doc_type", "disabled", "standard"],
            filters={"name": ["!=", ""]}
        )
        
        disabled_count = 0
        skipped_count = 0
        
        for format_doc in existing_formats:
            format_name = format_doc.name
            is_standard = format_doc.standard == "Yes"
            is_disabled = format_doc.disabled == 1
            
            # Skip if already disabled
            if is_disabled:
                skipped_count += 1
                continue
            
            # Disable the print format
            frappe.db.set_value("Print Format", format_name, "disabled", 1)
            disabled_count += 1
            
            frappe.log_error(
                f"Disabled print format: {format_name} (DocType: {format_doc.doc_type}, Standard: {is_standard})",
                "Print Format Disabled"
            )
        
        # Commit all changes
        frappe.db.commit()
        
        # Log summary
        summary = f"Disabled {disabled_count} print formats, skipped {skipped_count} already disabled"
        frappe.log_error(summary, "Print Format Disable Summary")
        
        return {
            "disabled": disabled_count,
            "skipped": skipped_count,
            "total": len(existing_formats)
        }
        
    except Exception as e:
        frappe.log_error(f"Error disabling print formats: {str(e)}")
        frappe.throw(_("Failed to disable print formats: {0}").format(str(e)))


@frappe.whitelist()
def disable_print_formats_by_doctype(doctypes_list=None):
    """
    Disable print formats for specific DocTypes only
    
    Args:
        doctypes_list: List of DocTypes to target (e.g., ["Sales Invoice", "Purchase Invoice"])
    """
    try:
        if not doctypes_list:
            doctypes_list = [
                "Sales Invoice", "Sales Order", "Delivery Note", "Quotation",
                "Purchase Invoice", "Purchase Order", "Purchase Receipt",
                "Stock Entry", "Material Request",
                "Payment Entry", "Journal Entry",
                "Salary Slip", "Customer", "Supplier"
            ]
        
        disabled_count = 0
        skipped_count = 0
        
        for doctype in doctypes_list:
            # Get print formats for this DocType
            formats = frappe.get_all(
                "Print Format",
                fields=["name", "disabled"],
                filters={"doc_type": doctype}
            )
            
            for format_doc in formats:
                format_name = format_doc.name
                is_disabled = format_doc.disabled == 1
                
                if is_disabled:
                    skipped_count += 1
                    continue
                
                # Disable the print format
                frappe.db.set_value("Print Format", format_name, "disabled", 1)
                disabled_count += 1
        
        # Commit all changes
        frappe.db.commit()
        
        return {
            "disabled": disabled_count,
            "skipped": skipped_count,
            "doctypes": doctypes_list
        }
        
    except Exception as e:
        frappe.log_error(f"Error disabling print formats by DocType: {str(e)}")
        frappe.throw(_("Failed to disable print formats: {0}").format(str(e)))


@frappe.whitelist()
def reset_print_format_defaults():
    """
    Reset default print format settings on DocTypes
    """
    try:
        # List of DocTypes that might have default print formats set
        doctypes_with_defaults = [
            "Sales Invoice", "Sales Order", "Delivery Note", "Quotation",
            "Purchase Invoice", "Purchase Order", "Purchase Receipt",
            "Stock Entry", "Material Request",
            "Payment Entry", "Journal Entry",
            "Salary Slip", "Customer", "Supplier"
        ]
        
        reset_count = 0
        
        for doctype in doctypes_with_defaults:
            # Check if DocType has default print format setting
            try:
                # Try to get the DocType's default print format
                default_format = frappe.get_meta(doctype).get_field("default_print_format")
                if default_format:
                    # Clear the default print format
                    frappe.db.set_value("DocType", doctype, "default_print_format", "")
                    reset_count += 1
            except:
                # DocType might not have this field, continue
                continue
        
        # Commit changes
        frappe.db.commit()
        
        return {"reset_count": reset_count}
        
    except Exception as e:
        frappe.log_error(f"Error resetting print format defaults: {str(e)}")
        frappe.throw(_("Failed to reset print format defaults: {0}").format(str(e)))


@frappe.whitelist()
def prepare_for_mozambique_print_formats():
    """
    Complete preparation: disable existing formats and reset defaults
    """
    try:
        # Step 1: Disable all existing print formats
        disable_result = disable_all_existing_print_formats()
        
        # Step 2: Reset default print format settings
        reset_result = reset_print_format_defaults()
        
        # Summary
        total_disabled = disable_result.get("disabled", 0)
        total_skipped = disable_result.get("skipped", 0)
        total_reset = reset_result.get("reset_count", 0)
        
        return {
            "disabled": total_disabled,
            "skipped": total_skipped,
            "reset_defaults": total_reset,
            "status": "ready_for_mozambique_formats"
        }
        
    except Exception as e:
        frappe.log_error(f"Error preparing for Mozambique print formats: {str(e)}")
        frappe.throw(_("Failed to prepare for Mozambique print formats: {0}").format(str(e)))


if __name__ == "__main__":
    # This can be run as a script
    frappe.init(site="erp.local")
    frappe.connect()
    
    # Run the preparation
    result = prepare_for_mozambique_print_formats()
    print(f"Preparation result: {result}")
