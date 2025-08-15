# -*- coding: utf-8 -*-
"""
Fiscal utilities for Mozambique

Currently implements fiscal numbering assignment for Sales Invoices:
- Sequential per Company Abbreviation + Fiscal Series

This does not alter the document name; it fills the custom field `fiscal_number`.
"""

import re
import frappe
from frappe.utils import cstr
from frappe.model.naming import make_autoname


def sanitize_series_part(value: str) -> str:
    """Sanitize parts for series keys: remove spaces and non-word chars except dash/underscore."""
    value = cstr(value or "").strip()
    if not value:
        return "GEN"
    return re.sub(r"[^A-Za-z0-9_-]+", "", value)


def assign_fiscal_number(doc, method):
    """Assign a sequential fiscal number before submit if missing.

    Uses pattern: {Company Abbreviation}-{Fiscal Series}-.#####
    """
    if getattr(doc, "fiscal_number", None):
        return

    # Determine company abbreviation
    try:
        company = frappe.get_doc("Company", doc.company)
        abbr = getattr(company, "abbr", None) or sanitize_series_part(company.name[:3].upper())
    except Exception:
        abbr = "CMP"

    # Ensure fiscal_series is set (fallback to naming_series if available)
    if not getattr(doc, "fiscal_series", None):
        series = getattr(doc, "naming_series", None)
        if series:
            doc.fiscal_series = series
        else:
            doc.fiscal_series = "DEFAULT"

    series_key = f"{sanitize_series_part(abbr)}-{sanitize_series_part(doc.fiscal_series)}-.#####"
    doc.fiscal_number = make_autoname(series_key)


