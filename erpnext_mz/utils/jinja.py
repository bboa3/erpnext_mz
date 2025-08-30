import frappe


def get_qr_image(doctype: str, name: str) -> str:
    """
    Return base64 PNG for the document's QR code, generating on demand if needed.
    Safe to call from Jinja print formats.
    """
    try:
        result = frappe.get_attr("erpnext_mz.qr_code.qr_generator.get_document_qr_code")(doctype, name)
        if isinstance(result, dict) and "qr_code_image" in result:
            return result.get("qr_code_image", "")
        return ""
    except Exception as e:
        frappe.log_error(f"Error getting QR image for {doctype} {name}: {str(e)}")
        return ""


def get_validation_url(doctype: str, name: str) -> str:
    """
    Return the hashed validation URL for a document.
    """
    try:
        return frappe.get_attr("erpnext_mz.qr_code.qr_generator.build_validation_url")(doctype, name)
    except Exception as e:
        frappe.log_error(f"Error getting validation URL for {doctype} {name}: {str(e)}")
        return ""


