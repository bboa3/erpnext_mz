# -*- coding: utf-8 -*-
"""
Scheduled Tasks for ERPNext Mozambique Custom App

This module contains scheduled tasks for compliance monitoring and reporting.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, add_days
logger = frappe.logger("erpnext_mz.tasks")

def daily_compliance_check():
    """
    Daily compliance check task
    
    This task runs daily to check compliance status
    """
    
    try:
        # Get all companies
        companies = frappe.get_all("Company", fields=["name"])
        
        for company in companies:
            company_name = company.name
            # Run compliance checks for all companies
            check_invoice_compliance(company_name)
            check_payroll_compliance(company_name)
            cleanup_old_integration_requests(company_name)
            
    except Exception as e:
        frappe.log_error(f"Daily compliance check failed: {str(e)}")

def monthly_saf_t_generation():
    """
    Monthly SAF-T generation task
    
    This task runs monthly to generate SAF-T files
    """
    
    try:
        # Get current month and year
        current_date = now_datetime()
        year = current_date.year
        month = current_date.month
        
        # Get all companies
        companies = frappe.get_all("Company", fields=["name"])
        
        for company in companies:
            company_name = company.name
            # Generate SAF-T files for all companies
            from .modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
            try:
                result = generate_monthly_saf_t(company_name, year, month)
                logger.info("SAF-T generated for %s period %s", company_name, result.get("period"))

                # Auto-submit to AT if enabled on Company
                company_doc = frappe.get_doc("Company", company_name)
                if getattr(company_doc, "auto_submit_saf_t_to_at", False):
                    from .modules.tax_compliance.at_integration import ATIntegration
                    at = ATIntegration(company_name)
                    # Submit sales SAF-T if exists
                    if result.get("sales_checksum") and result.get("sales_xml"):
                        saf_t_data = {
                            "period": result["period"],
                            "xml_content": result["sales_xml"],
                            "checksum": result["sales_checksum"],
                        }
                        at.transmit_saf_t(saf_t_data, "sales")
                    # Submit payroll SAF-T if exists
                    if result.get("payroll_checksum") and result.get("payroll_xml"):
                        saf_t_data = {
                            "period": result["period"],
                            "xml_content": result["payroll_xml"],
                            "checksum": result["payroll_checksum"],
                        }
                        at.transmit_saf_t(saf_t_data, "payroll")
            except Exception as e:
                logger.error("SAF-T generation failed for %s: %s", company_name, str(e))
                
    except Exception as e:
        logger.error("Monthly SAF-T generation failed: %s", str(e))

def check_invoice_compliance(company):
    """
    Check invoice compliance for a company
    
    Args:
        company (str): Company name
    """
    
    # Check for invoices without fiscal series
    invoices_without_series = frappe.get_all(
        "Sales Invoice",
        filters={
            "company": company,
            "posting_date": [">=", add_days(getdate(), -7)],
            "docstatus": 1,
            "fiscal_series": ["in", [None, ""]],
        },
        fields=["name", "posting_date"],
    )
    
    if invoices_without_series:
        logger.warning("%s invoices without fiscal series (company=%s)", len(invoices_without_series), company)

def check_payroll_compliance(company):
    """
    Check payroll compliance for a company
    
    Args:
        company (str): Company name
    """
    
    # Check for payroll entries without proper components
    payroll_entries = frappe.get_all("Payroll Entry",
                                    filters={
                                        "company": company,
                                        "posting_date": [">=", add_days(getdate(), -7)],
                                        "docstatus": 1
                                    },
                                    fields=["name", "posting_date"])
    
    for payroll in payroll_entries:
        # Basic existence check on Salary Slip records linked to Payroll Entry for the period
        try:
            slips = frappe.get_all(
                "Salary Slip",
                filters={"payroll_entry": payroll.name},
                limit=1,
            )
            if not slips:
                logger.warning(
                    "Payroll %s without generated salary slips (company=%s)", payroll.name, company
                )
        except Exception:
            # HRMS might be absent; skip
            pass


def cleanup_old_integration_requests(company: str) -> None:
    """Cleanup job for stale/failed Integration Request records older than 90 days.

    We only delete Failed requests for our service label to keep DB lean.
    """
    try:
        old_failed = frappe.get_all(
            "Integration Request",
            filters={
                "reference_doctype": "Company",
                "reference_docname": company,
                "integration_request_service": "AT API",
                "status": "Failed",
                "modified": ["<", add_days(getdate(), -90)],
            },
            pluck="name",
            limit=200,
        )
        if old_failed:
            for name in old_failed:
                try:
                    frappe.delete_doc("Integration Request", name, ignore_permissions=True)
                except Exception:
                    continue
            logger.info("Cleaned up %s old failed Integration Requests for %s", len(old_failed), company)
    except Exception as e:
        logger.error("Cleanup of Integration Requests failed for %s: %s", company, str(e))
