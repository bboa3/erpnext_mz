# -*- coding: utf-8 -*-
"""
AT (Autoridade Tributária) Integration for Mozambique

This module handles integration with Mozambique's tax authority:
- Invoice transmission
- SAF-T submission
- Status tracking
- Error handling
"""

import frappe
from frappe import _
import requests
import json
from frappe.utils import now_datetime
import hashlib

class ATIntegration:
    """
    AT Integration class for Mozambique compliance
    """
    
    def __init__(self, company):
        """
        Initialize AT integration
        
        Args:
            company (str): Company name
        """
        self.company = company
        self.company_doc = frappe.get_doc("Company", company)
        self.at_settings = self._get_at_settings()
    
    def _get_at_settings(self):
        """
        Get AT integration settings for the company
        
        Returns:
            dict: AT settings
        """
        
        # Prefer dedicated AT Settings doctype, but gracefully handle absence
        try:
            if frappe.db.table_exists("tabAT Settings"):
                at_settings = frappe.get_all(
                    "AT Settings",
                    filters={"company": self.company},
                    fields=["enabled", "auto_submit", "api_endpoint", "api_key"],
                    limit=1,
                )
                if at_settings:
                    s = at_settings[0]
                    return {
                        "api_endpoint": s.api_endpoint or "",
                        "api_key": s.api_key or "",
                        "certification_number": "",
                        "enabled": bool(s.enabled),
                        "auto_submit": bool(s.auto_submit),
                    }
        except Exception:
            # Fall through to legacy fields
            pass
        # Fallback to Company custom fields if present (legacy)
        return {
            "api_endpoint": getattr(self.company_doc, 'at_api_endpoint', ''),
            "api_key": getattr(self.company_doc, 'at_api_key', ''),
            "certification_number": "",
            "enabled": getattr(self.company_doc, 'at_integration_enabled', False),
            "auto_submit": getattr(self.company_doc, 'auto_submit_saf_t_to_at', False),
        }
    
    def transmit_invoice(self, invoice_name):
        """
        Transmit invoice to AT
        
        Args:
            invoice_name (str): Sales Invoice name
            
        Returns:
            dict: Transmission result
        """
        
        if not self.at_settings or not self.at_settings.get("enabled"):
            return {
                "success": False,
                "message": "AT integration not enabled for this company"
            }
        
        try:
            # Get invoice data
            invoice = frappe.get_doc("Sales Invoice", invoice_name)
            
            # Prepare payload
            payload = self._prepare_invoice_payload(invoice)
            
            # Transmit to AT
            response = self._send_to_at(payload, "invoice")
            
            # Log transmission
            self._log_transmission(invoice_name, "invoice", payload, response)
            
            return response
            
        except Exception as e:
            frappe.log_error(f"AT invoice transmission failed: {str(e)}")
            return {
                "success": False,
                "message": f"Transmission failed: {str(e)}"
            }
    
    def transmit_saf_t(self, saf_t_data, file_type):
        """
        Transmit SAF-T file to AT
        
        Args:
            saf_t_data (dict): SAF-T data
            file_type (str): 'sales' or 'payroll'
            
        Returns:
            dict: Transmission result
        """
        
        if not self.at_settings or not self.at_settings.get("enabled"):
            return {
                "success": False,
                "message": "AT integration not enabled for this company"
            }
        
        try:
            # Prepare SAF-T payload
            payload = self._prepare_saf_t_payload(saf_t_data, file_type)

            # Build idempotent request id for this period/type
            period = saf_t_data.get("period", "")
            request_id = f"SAF-T_{file_type}-{period}"

            # Return early if a successful submission already exists
            existing = frappe.get_all(
                "Integration Request",
                filters={
                    "integration_request_service": "AT API",
                    "reference_doctype": "Company",
                    "reference_docname": self.company,
                    "request_id": request_id,
                    "status": "Completed",
                },
                limit=1,
            )
            if existing:
                return {
                    "success": True,
                    "message": "SAF-T already transmitted for this period",
                    "request_id": request_id,
                    "status_code": 200,
                }
            
            # Transmit to AT
            response = self._send_to_at(payload, "saf_t")
            
            # Log transmission
            # Use request_id as document name in logs for idempotency
            self._log_transmission(request_id, "saf_t", payload, response)
            
            return response
            
        except Exception as e:
            frappe.log_error(f"AT SAF-T transmission failed: {str(e)}")
            return {
                "success": False,
                "message": f"Transmission failed: {str(e)}"
            }
    
    def _prepare_invoice_payload(self, invoice):
        """
        Prepare invoice payload for AT
        
        Args:
            invoice: Sales Invoice document
            
        Returns:
            dict: Prepared payload
        """
        
        # Basic invoice data
        from frappe.utils import getdate
        company_nuit = self._get_company_nuit()
        payload = {
            "invoice_number": invoice.name,
            "fiscal_series": getattr(invoice, 'fiscal_series', ''),
            "fiscal_number": getattr(invoice, 'fiscal_number', ''),
            "posting_date": getdate(invoice.posting_date).strftime("%Y-%m-%d"),
            "due_date": getdate(invoice.due_date).strftime("%Y-%m-%d"),
            "customer_nuit": self._get_customer_nuit(invoice.customer),
            "total_amount": float(invoice.grand_total),
            "vat_amount": float(invoice.total_taxes_and_charges),
            "net_amount": float(invoice.net_total),
            "company_nuit": company_nuit,
            # No certification number required in system metadata
            "certification_number": "",
            "timestamp": now_datetime().isoformat()
        }
        
        # Add items
        payload["items"] = []
        for item in invoice.items:
            item_data = {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "rate": float(item.rate),
                "amount": float(item.amount),
                "vat_rate": self._get_item_vat_rate(item.item_code)
            }
            payload["items"].append(item_data)
        
        # Generate checksum
        payload["checksum"] = self._generate_checksum(payload)
        
        return payload
    
    def _prepare_saf_t_payload(self, saf_t_data, file_type):
        """
        Prepare SAF-T payload for AT
        
        Args:
            saf_t_data (dict): SAF-T data
            file_type (str): 'sales' or 'payroll'
            
        Returns:
            dict: Prepared payload
        """
        
        payload = {
            "file_type": file_type,
            "period": saf_t_data.get("period", ""),
            "company_nuit": self._get_company_nuit(),
            "certification_number": self.at_settings.get("certification_number", ""),
            "file_content": saf_t_data.get("xml_content", ""),
            "file_checksum": saf_t_data.get("checksum", ""),
            "timestamp": now_datetime().isoformat()
        }
        
        return payload
    
    def _send_to_at(self, payload, transmission_type):
        """
        Send payload to AT API
        
        Args:
            payload (dict): Data to send
            transmission_type (str): Type of transmission
            
        Returns:
            dict: API response
        """
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.at_settings.get('api_key', '')}",
                "X-Company-NUIT": getattr(self.company_doc, 'nuit', ''),
                "X-Transmission-Type": transmission_type
            }
            
            endpoint = self.at_settings.get("api_endpoint") or "https://example.invalid/at-mz"
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                parsed = None
                try:
                    parsed = response.json()
                except Exception:
                    parsed = {"raw": response.text}
                return {
                    "success": True,
                    "message": "Transmission successful",
                    "response": parsed,
                    "status_code": response.status_code,
                }
            else:
                return {
                    "success": False,
                    "message": f"AT API error: {response.status_code}",
                    "response": response.text,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Network error: {str(e)}",
                "status_code": None
            }
    
    def _get_customer_nuit(self, customer):
        """
        Get customer NUIT
        
        Args:
            customer (str): Customer name
            
        Returns:
            str: Customer NUIT
        """
        
        customer_doc = frappe.get_doc("Customer", customer)
        nuit = getattr(customer_doc, 'nuit', '') or ''
        if not nuit:
            try:
                nuit = getattr(customer_doc, 'tax_id', '') or ''
            except Exception:
                nuit = ''
        return nuit
    
    def _get_item_vat_rate(self, item_code):
        """
        Get item VAT rate
        
        Args:
            item_code (str): Item code
            
        Returns:
            float: VAT rate
        """
        
        from ..accounting.vat_templates import get_vat_rate_for_item
        return get_vat_rate_for_item(item_code, self.company)
    
    def _generate_checksum(self, data):
        """
        Generate checksum for data
        
        Args:
            data (dict): Data to checksum
            
        Returns:
            str: SHA-256 checksum
        """
        
        # Convert to JSON string and generate checksum
        json_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_string.encode('utf-8')).hexdigest()
    
    def _log_transmission(self, document_name, transmission_type, payload, response):
        """
        Log transmission attempt
        
        Args:
            document_name (str): Document name
            transmission_type (str): Type of transmission
            payload (dict): Sent payload
            response (dict): AT response
        """
        
        # Log using Integration Request for standardization
        try:
            log = frappe.new_doc("Integration Request")
            # v15 uses 'integration_request_service' and 'is_remote_request'
            log.integration_request_service = "AT API"
            try:
                log.is_remote_request = 1
            except Exception:
                pass
            log.status = "Completed" if response.get("success") else "Failed"
            log.reference_doctype = "Company"
            log.reference_docname = self.company
            # Set request_id for idempotency tracking
            try:
                # For invoices this should be the Sales Invoice name
                # For SAF-T we use the provided document_name
                log.request_id = document_name
            except Exception:
                pass
            log.data = json.dumps({
                "document_name": document_name,
                "transmission_type": transmission_type,
                "payload": payload,
            })
            log.output = json.dumps(response)
            log.flags.ignore_permissions = True
            log.save(ignore_permissions=True)
        except Exception:
            frappe.log_error("Failed to create Integration Request log for AT transmission")

    def _get_company_nuit(self) -> str:
        """Return Company NUIT with fallback to tax_id if NUIT missing."""
        nuit = getattr(self.company_doc, 'nuit', '') or ''
        if not nuit:
            try:
                nuit = getattr(self.company_doc, 'tax_id', '') or ''
            except Exception:
                nuit = ''
        return nuit

def transmit_to_at(doc, method):
    """
    Hook function to transmit invoice to AT on submit
    
    Args:
        doc: Document object
        method: Document method
    """
    
    if method == "on_submit":
        # Enqueue async transmission for idempotency and resilience
        frappe.enqueue(
            "erpnext_mz.modules.tax_compliance.at_integration._enqueue_transmit",
            queue="long",
            job_name=f"Transmit-{doc.doctype}-{doc.name}",
            timeout=600,
            docname=doc.name,
            company=doc.company,
            now=False,
        )

def handle_cancellation(doc, method):
    """
    Hook function to handle invoice cancellation
    
    Args:
        doc: Document object
        method: Document method
    """
    
    if method == "on_cancel":
        # Log cancellation intent in Integration Request for traceability
        try:
            log = frappe.new_doc("Integration Request")
            log.integration_request_service = "AT API"
            try:
                log.is_remote_request = 1
            except Exception:
                pass
            log.status = "Completed"
            log.reference_doctype = "Company"
            log.reference_docname = doc.company
            try:
                log.request_id = f"CANCEL-{doc.doctype}-{doc.name}"
            except Exception:
                pass
            log.data = json.dumps({
                "document_name": doc.name,
                "transmission_type": "cancel_invoice",
                "payload": {"invoice": doc.name, "action": "cancel"},
            })
            log.output = json.dumps({"message": "Cancellation recorded; implement AT void call if required"})
            log.flags.ignore_permissions = True
            log.save(ignore_permissions=True)
        except Exception:
            frappe.log_error("Failed to log AT cancellation event")

def _enqueue_transmit(docname: str, company: str):
    """Background job to transmit an invoice idempotently."""
    at_integration = ATIntegration(company)
    # Idempotency: if an Integration Request already exists and succeeded, skip
    filters = {
        "reference_doctype": "Company",
        "reference_docname": company,
        "integration_request_service": "AT API",
        "status": "Completed",
    }
    try:
        if frappe.db.has_column("Integration Request", "request_id"):
            filters["request_id"] = docname
            already = frappe.get_all("Integration Request", filters=filters, limit=1)
        else:
            already = frappe.get_all(
                "Integration Request",
                filters=filters | {"data": ["like", f"%\"document_name\": \"{docname}\"%"]},
                limit=1,
            )
    except Exception:
        already = []
    if already:
        return
    result = at_integration.transmit_invoice(docname)
    return result
