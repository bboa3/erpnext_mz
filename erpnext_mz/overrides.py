# -*- coding: utf-8 -*-
"""
Overrides for ERPNext Mozambique Custom App

This module contains method overrides for ERPNext core functionality.
"""

import frappe
from frappe import _

def include_sales_invoice_fiscal_fields(fields: list[str] | None) -> list[str] | None:
    """
    Safe helper to include fiscal fields in Sales Invoice queries.
    Use explicitly where needed instead of overriding core methods.
    """
    if fields is None:
        return None
    if "fiscal_series" not in fields:
        fields.append("fiscal_series")
    if "fiscal_number" not in fields:
        fields.append("fiscal_number")
    return fields
