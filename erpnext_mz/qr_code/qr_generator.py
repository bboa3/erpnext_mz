"""
QR Code Generator for ERPNext MZ
Generates QR codes for document validation and embeds them into print formats.
"""

import frappe
import pyqrcode
import io
import base64
import json
from datetime import datetime
from frappe.utils import get_url
import hmac
import hashlib
from urllib.parse import quote_plus


def generate_document_qr_code(doc, method=None):
    """
    Generate QR code for a document after submission.
    This function is called by document hooks.
    
    Args:
        doc: The document object
        method: The method that triggered this hook (e.g., 'on_submit')
    """
    try:
        # Generate QR code data
        qr_data = create_validation_data(doc)
        
        # Generate QR code image
        qr_code_image = generate_qr_code_image(qr_data)
        
        # Save QR code to document
        save_qr_code_to_document(doc, qr_code_image, qr_data)
        
    except Exception as e:
        frappe.log_error(f"Error generating QR code for {doc.doctype} {doc.name}: {str(e)}")


def _generate_validation_hash(document_type: str, document_name: str) -> str:
    """
    Generate an HMAC-based hash for validation links.
    Uses the site's encryption_key as secret.
    """
    secret = (frappe.local.conf.get("encryption_key") or "").encode("utf-8")
    message = f"{document_type}|{document_name}".encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    # keep it short for QR readability
    return signature[:16]


def build_validation_url(document_type: str, document_name: str) -> str:
    """
    Build a full absolute validation URL including a secure hash.
    """
    hash_sig = _generate_validation_hash(document_type, document_name)

    path = f"/qr_validation?doctype={quote_plus(document_type)}&name={quote_plus(document_name)}&hash={hash_sig}"
    return f"{get_url()}{path}"


def create_validation_data(doc):
    """
    Create validation data for QR code.
    
    Args:
        doc: The document object
        
    Returns:
        dict: Validation data
    """
    # Get company information
    company = frappe.get_doc("Company", doc.company)

    # Convert dates to strings for JSON serialization
    document_date = doc.posting_date or getattr(doc, "transaction_date", None)
    if document_date:
        document_date = str(document_date)

    # Determine an appropriate monetary amount across diverse DocTypes
    amount_value = None
    for field_name in [
        "grand_total",
        "total",
        "net_total",
        "base_grand_total",
        "outstanding_amount",
        "paid_amount",
        "received_amount",
        "total_amount",
        "amount",
    ]:
        if hasattr(doc, field_name):
            try:
                raw_val = getattr(doc, field_name) or 0
                numeric_val = float(raw_val)
                # pick the first non-zero value; if all zero, last fallback will set 0.0
                if numeric_val:
                    amount_value = numeric_val
                    break
                if amount_value is None:
                    amount_value = numeric_val
            except Exception:
                # ignore non-numeric fields
                pass
    if amount_value is None:
        amount_value = 0.0

    # Determine the most suitable currency for the document
    currency_value = None
    for currency_field in [
        "currency",
        "party_account_currency",
        "price_list_currency",
        "paid_to_account_currency",
        "paid_from_account_currency",
        "company_currency",
    ]:
        if hasattr(doc, currency_field):
            val = getattr(doc, currency_field)
            if val:
                currency_value = val
                break
    if not currency_value:
        currency_value = getattr(company, "default_currency", None)

    # Create validation data including public validation URL
    validation_url = build_validation_url(doc.doctype, doc.name)
    validation_data = {
        "doc": doc.name,
        "type": doc.doctype,
        "company": doc.company,
        "date": document_date,
        "amount": amount_value,
        "currency": currency_value,
        "tax_id": getattr(company, "tax_id", None),
        "ts": datetime.now().isoformat(),
        "validation_url": validation_url,
    }

    return validation_data


def generate_qr_code_image(data):
    """
    Generate QR code image from data.
    
    Args:
        data: Data to encode in QR code
        
    Returns:
        str: Base64 encoded QR code image
    """
    # Determine payload string for QR code: prefer URL string if provided
    if isinstance(data, dict) and data.get("validation_url"):
        payload = data.get("validation_url")
    else:
        payload = json.dumps(data, ensure_ascii=False)

    # Generate QR code with auto version (let pyqrcode determine the version)
    qr = pyqrcode.create(payload, error='M')
    
    # Create buffer for image
    buffer = io.BytesIO()
    
    # Save as PNG with smaller scale to reduce size
    qr.png(buffer, scale=4)
    
    # Get base64 encoded image
    buffer.seek(0)
    image_data = buffer.getvalue()
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    return base64_image


def save_qr_code_to_document(doc, qr_code_image, validation_data):
    """
    Save QR code to document.
    
    Args:
        doc: The document object
        qr_code_image: Base64 encoded QR code image
        validation_data: The validation data used to generate the QR code
    """
    try:
        # Create QR Code record
        qr_doc = frappe.new_doc("QR Code")
        qr_doc.document_type = doc.doctype
        qr_doc.document_name = doc.name
        qr_doc.qr_code_image = qr_code_image
        qr_doc.validation_data = json.dumps(validation_data, ensure_ascii=False)
        qr_doc.generated_at = datetime.now()
        qr_doc.insert(ignore_permissions=True)
        
        frappe.logger().info(f"QR Code generated and saved for {doc.doctype} {doc.name}")
        
    except Exception as e:
        frappe.log_error(f"Could not save QR code for {doc.doctype} {doc.name}: {str(e)}")


@frappe.whitelist()
def get_document_qr_code(document_type, document_name):
    """
    Get QR code for a document.
    
    Args:
        document_type: Type of document
        document_name: Name of document
        
    Returns:
        dict: QR code data
    """
    try:
        # Try to get from QR Code DocType first
        qr_codes = frappe.get_all("QR Code", 
                                 filters={
                                     "document_type": document_type,
                                     "document_name": document_name
                                 },
                                 order_by="generated_at desc",
                                 limit=1)
        
        if qr_codes:
            qr_doc = frappe.get_doc("QR Code", qr_codes[0].name)
            return {
                "qr_code_image": qr_doc.qr_code_image,
                "generated_at": str(qr_doc.generated_at),
                "validation_data": json.loads(qr_doc.validation_data)
            }
        
        # Fallback: generate QR code on demand
        doc = frappe.get_doc(document_type, document_name)
        validation_data = create_validation_data(doc)
        qr_code_image = generate_qr_code_image(validation_data)
        
        return {
            "qr_code_image": qr_code_image,
            "generated_at": datetime.now().isoformat(),
            "validation_data": validation_data
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting QR code for {document_type} {document_name}: {str(e)}")
        return {"error": str(e)}
