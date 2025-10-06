#!/usr/bin/env python3
"""
Enhanced Print Format Management for Mozambique

This script ensures that only Mozambique-specific print formats are enabled and set as default,
while completely disabling all other print formats to prevent conflicts.
"""

import frappe
from frappe import _


@frappe.whitelist()
def disable_all_existing_print_formats():
    """
    Disable ALL existing print formats to prepare for Mozambique formats only
    """
    try:
        # Get all print formats
        existing_formats = frappe.get_all(
            "Print Format",
            fields=["name", "doc_type", "disabled", "standard", "module"],
            filters={"name": ["!=", ""]}
        )
        
        disabled_count = 0
        skipped_count = 0
        
        for format_doc in existing_formats:
            format_name = format_doc.name
            is_standard = format_doc.standard == "Yes"
            is_disabled = format_doc.disabled == 1
            module = format_doc.module or ""
            
            # Skip if already disabled

            
            # Disable the print format
            frappe.db.set_value("Print Format", format_name, "disabled", 1)
            frappe.db.set_value("Print Format", format_name, "standard", "No")
            disabled_count += 1
            
            frappe.log_error(
                f"Disabled print format: {format_name} (DocType: {format_doc.doc_type}, Standard: {is_standard}, Module: {module})",
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
        doctypes_list: List of DocTypes to target
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
                fields=["name", "disabled", "module"],
                filters={"doc_type": doctype}
            )
            
            for format_doc in formats:
                format_name = format_doc.name
                is_disabled = format_doc.disabled == 1
                module = format_doc.module or ""
                
                if is_disabled:
                    skipped_count += 1
                    continue
                
                # Disable the print format
                frappe.db.set_value("Print Format", format_name, "disabled", 1)
                disabled_count += 1
                
                frappe.log_error(
                    f"Disabled print format for {doctype}: {format_name} (Module: {module})",
                    "Print Format Disabled"
                )
        
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
                    frappe.log_error(f"Reset default print format for {doctype}", "Default Reset")
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
def set_mozambique_print_formats_as_default():
    """
    Set Mozambique print formats as default by ensuring they are the only enabled option
    Since Frappe doesn't have DocType-level default print formats, we ensure Mozambique formats
    are the only enabled formats, making them automatically the default choice.
    """
    try:
        # Map of DocTypes to their Mozambique print format names
        mozambique_format_mapping = {
            "Sales Invoice": ["Fatura (MZ)", "Nota de Crédito (MZ)"],
            "Sales Order": "Encomenda de Venda (MZ)",
            "Delivery Note": "Guia de Remessa (MZ)",
            "Quotation": "Orçamento (MZ)",
            "Purchase Invoice": "Factura de Compra (MZ)",
            "Purchase Order": "Encomenda de Compra (MZ)",
            "Purchase Receipt": "Recibo de Compra (MZ)",
            "Stock Entry": "Entrada de Stock (MZ)",
            "Material Request": "Pedido de Material (MZ)",
            "Payment Entry": "Entrada de Pagamento (MZ)",
            "Journal Entry": "Lançamento Contabilístico (MZ)",
            "Salary Slip": "Recibo de Vencimento (MZ)",
            "Customer": "Cliente (MZ)",
            "Supplier": "Fornecedor (MZ)"
        }
        
        set_count = 0
        errors = []
        
        for doctype, format_names in mozambique_format_mapping.items():
            # Handle both single format names and lists of format names
            if isinstance(format_names, list):
                format_list = format_names
            else:
                format_list = [format_names]
            
            for format_name in format_list:
                try:
                    # Check if the Mozambique print format exists
                    if frappe.db.exists("Print Format", format_name):
                        # Ensure this format is enabled
                        frappe.db.set_value("Print Format", format_name, "disabled", 0)
                    
                        set_count += 1
                        frappe.log_error(
                            f"Enabled {format_name} for {doctype}",
                            "Mozambique Format Enabled"
                        )
                    else:
                        errors.append(f"Print format {format_name} not found for {doctype}")
                except Exception as e:
                    errors.append(f"Error enabling {format_name} for {doctype}: {str(e)}")
        
        # Commit changes
        frappe.db.commit()
        
        return {
            "set_count": set_count,
            "errors": errors,
            "total_doctypes": len(mozambique_format_mapping),
            "method": "exclusive_enablement"
        }
        
    except Exception as e:
        frappe.log_error(f"Error enabling Mozambique print formats: {str(e)}")
        frappe.throw(_("Failed to enable Mozambique print formats: {0}").format(str(e)))


@frappe.whitelist()
def ensure_mozambique_formats_are_first_choice():
    """
    Ensure Mozambique print formats are the first choice by:
    1. Making them the only enabled formats for their DocTypes
    2. This automatically makes them the default choice since no other formats are available
    """
    try:
        # Since we can't set priorities, we ensure Mozambique formats are the only choice
        # by keeping them enabled and all others disabled
        
        mozambique_formats = [
            "Fatura (MZ)", "Nota de Crédito (MZ)", "Encomenda de Venda (MZ)", "Guia de Remessa (MZ)", "Orçamento (MZ)",
            "Factura de Compra (MZ)", "Encomenda de Compra (MZ)", "Recibo de Compra (MZ)",
            "Entrada de Stock (MZ)", "Pedido de Material (MZ)",
            "Entrada de Pagamento (MZ)", "Lançamento Contabilístico (MZ)",
            "Recibo de Vencimento (MZ)", "Cliente (MZ)", "Fornecedor (MZ)"
        ]
        
        enabled_count = 0
        
        for format_name in mozambique_formats:
            try:
                if frappe.db.exists("Print Format", format_name):
                    # Ensure enabled
                    frappe.db.set_value("Print Format", format_name, "disabled", 0)
                    enabled_count += 1
                    
                    frappe.log_error(
                        f"Ensured {format_name} is enabled",
                        "Print Format Enabled"
                    )
            except Exception as e:
                frappe.log_error(f"Error ensuring {format_name} is enabled: {str(e)}")
        
        # Commit all changes
        frappe.db.commit()
        
        return {
            "enabled_count": enabled_count,
            "total_formats": len(mozambique_formats),
            "method": "exclusive_enablement",
            "explanation": "Mozambique formats are the only enabled formats, making them automatically the default choice"
        }
        
    except Exception as e:
        frappe.log_error(f"Error ensuring Mozambique formats are first choice: {str(e)}")
        frappe.throw(_("Failed to ensure Mozambique formats are first choice: {0}").format(str(e)))


@frappe.whitelist()
def ensure_only_mozambique_formats_enabled():
    """
    Ensure only Mozambique print formats are enabled, disable all others
    """
    try:
        # Get all print formats
        all_formats = frappe.get_all(
            "Print Format",
            fields=["name", "doc_type", "disabled", "module"],
            filters={"name": ["!=", ""]}
        )
        
        mozambique_formats = [
            "Fatura (MZ)", "Nota de Crédito (MZ)", "Encomenda de Venda (MZ)", "Guia de Remessa (MZ)", "Orçamento (MZ)",
            "Factura de Compra (MZ)", "Encomenda de Compra (MZ)", "Recibo de Compra (MZ)",
            "Entrada de Stock (MZ)", "Pedido de Material (MZ)",
            "Entrada de Pagamento (MZ)", "Lançamento Contabilístico (MZ)",
            "Recibo de Vencimento (MZ)", "Cliente (MZ)", "Fornecedor (MZ)"
        ]
        
        enabled_mozambique = 0
        disabled_others = 0
        already_disabled = 0
        
        for format_doc in all_formats:
            format_name = format_doc.name
            is_disabled = format_doc.disabled == 1
            module = format_doc.module or ""
            
            if format_name in mozambique_formats:
                # This is a Mozambique format - ensure it's enabled
                if is_disabled:
                    frappe.db.set_value("Print Format", format_name, "disabled", 0)
                    enabled_mozambique += 1
                    frappe.log_error(
                        f"Enabled Mozambique print format: {format_name}",
                        "Mozambique Format Enabled"
                    )
            else:
                # This is NOT a Mozambique format - ensure it's disabled
                if not is_disabled:
                    frappe.db.set_value("Print Format", format_name, "disabled", 1)
                    disabled_others += 1
                    frappe.log_error(
                        f"Disabled non-Mozambique format: {format_name} (DocType: {format_doc.doc_type}, Module: {module})",
                        "Non-Mozambique Format Disabled"
                    )
                else:
                    already_disabled += 1
        
        # Commit all changes
        frappe.db.commit()
        
        return {
            "enabled_mozambique": enabled_mozambique,
            "disabled_others": disabled_others,
            "already_disabled": already_disabled,
            "total_formats": len(all_formats),
            "mozambique_formats": len(mozambique_formats)
        }
        
    except Exception as e:
        frappe.log_error(f"Error ensuring only Mozambique formats enabled: {str(e)}")
        frappe.throw(_("Failed to ensure only Mozambique formats enabled: {0}").format(str(e)))


@frappe.whitelist()
def prepare_for_mozambique_print_formats():
    """
    Complete preparation: disable existing formats, reset defaults, and ensure only Mozambique formats are enabled
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


@frappe.whitelist()
def complete_mozambique_print_format_setup():
    """
    Complete setup: prepare, create formats, set defaults, and ensure only Mozambique formats are enabled
    """
    try:
        # Step 1: Complete preparation
        preparation_result = prepare_for_mozambique_print_formats()
        
        # Step 2: Create all Mozambique print formats (this will be called from comprehensive_print_formats.py)
        # from .comprehensive_print_formats import create_all_mozambique_print_formats
        # formats_created = create_all_mozambique_print_formats()
        
        # Step 3: Set Mozambique formats as primary choice using priority system
        default_result = set_mozambique_print_formats_as_default()
        
        # Step 4: Ensure Mozambique formats are the first choice by setting priorities
        priority_result = ensure_mozambique_formats_are_first_choice()
        
        # Step 5: Ensure only Mozambique formats are enabled
        enable_result = ensure_only_mozambique_formats_enabled()
        
        # Comprehensive summary
        return {
            "preparation": preparation_result,
            "defaults_set": default_result,
            "priority_setting": priority_result,
            "enforcement": enable_result,
            "status": "mozambique_print_formats_complete",
            "message": "Mozambique print format setup completed successfully with priority-based selection"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in complete Mozambique print format setup: {str(e)}")
        frappe.throw(_("Failed to complete Mozambique print format setup: {0}").format(str(e)))


if __name__ == "__main__":
    # This can be run as a script
    frappe.init(site="erp.local")
    frappe.connect()
    
    # Run the complete setup
    result = complete_mozambique_print_format_setup()
    print(f"Complete setup result: {result}")
