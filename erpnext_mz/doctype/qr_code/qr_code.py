# Copyright (c) 2024, MozEconomia, SA and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QRCode(Document):
    """QR Code document for storing generated QR codes and validation data."""
    
    def validate(self):
        """Validate QR Code document."""
        if not self.document_type or not self.document_name:
            frappe.throw("Document Type and Document Name are required")
        
        # Check if document exists
        if not frappe.db.exists(self.document_type, self.document_name):
            frappe.throw(f"Document {self.document_name} of type {self.document_type} does not exist")
    
    def before_save(self):
        """Set generated_at if not set."""
        if not self.generated_at:
            from datetime import datetime
            self.generated_at = datetime.now()
