import frappe
import hmac
import hashlib
from typing import Dict


def _expected_hash(doctype: str, name: str) -> str:
    """
    Generate expected hash for validation (same as in qr_generator).
    """
    secret = (frappe.local.conf.get("encryption_key") or "").encode("utf-8")
    message = f"{doctype}|{name}".encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return signature[:16]


@frappe.whitelist(allow_guest=True)
def validate_document(doctype: str, name: str, hash: str = "") -> Dict:
    """
    Public endpoint to validate a document using an HMAC hash embedded in the QR code.
    Returns minimal but useful document info.
    """
    try:
        if not doctype or not name:
            return {"valid": False, "message": "Parâmetros inválidos"}

        expected = _expected_hash(doctype, name)
        if not hash or hash != expected:
            return {"valid": False, "message": "Assinatura inválida"}

        if not frappe.db.exists(doctype, name):
            return {"valid": False, "message": "Documento não encontrado"}

        doc = frappe.get_doc(doctype, name)

        # basic info for validator page
        info = {
            "type": doc.doctype,
            "name": doc.name,
            "company": getattr(doc, "company", None),
            "date": str(getattr(doc, "posting_date", None) or getattr(doc, "transaction_date", None) or ""),
            "amount": float(getattr(doc, "grand_total", 0) or getattr(doc, "total", 0) or 0),
            "currency": getattr(doc, "currency", None),
            "status": getattr(doc, "status", None),
        }

        # optional extras
        tax_id = None
        if getattr(doc, "company", None):
            tax_id = frappe.db.get_value("Company", doc.company, "tax_id")
        if tax_id:
            info["tax_id"] = tax_id

        if getattr(doc, "customer_name", None):
            info["customer"] = doc.customer_name

        return {"valid": True, "document_info": info}
    except Exception as e:
        frappe.log_error(f"validate_document API error: {e}")
        return {"valid": False, "message": f"Erro: {e}"}


