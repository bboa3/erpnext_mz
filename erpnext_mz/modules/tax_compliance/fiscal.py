# -*- coding: utf-8 -*-
"""
Fiscal utilities for Mozambique

Fiscal numbering enforcement has been removed in favor of ERPNext defaults.
"""

import frappe
import re


# Removed legacy helpers related to fiscal numbering


def validate_nuit(doc, method):
    """Validate NUIT on Customer, Supplier, or Company.

    Rules (simple):
    - Digits only
    - Length exactly 9
    - Optional: allow empty for drafts when not required by form
    """
    import re as _re

    doctype = getattr(doc, "doctype", "")

    # Determine field name and value
    nuit_field = "nuit"
    if doctype == "Company":
        value = getattr(doc, "nuit", None) or getattr(doc, "tax_id", None)
    else:
        value = getattr(doc, "nuit", None)

    # If field is absent entirely, do nothing
    if value is None:
        return

    value_str = str(value).strip()
    if not value_str:
        return  # allow empty; make it required via Custom Field if needed

    if not _re.fullmatch(r"\d{9}", value_str):
        frappe.throw(
            f"NUIT inválido em {doctype}: deve conter exatamente 9 dígitos. Valor: '{value_str}'"
        )

