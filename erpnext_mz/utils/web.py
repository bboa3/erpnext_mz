#!/usr/bin/env python3
"""
Web-related utilities for ERPNext Mozambique.

This module handles:
- Guest user language enforcement
- Web page language settings
- Cookie management for language preferences
"""

import frappe


def enforce_guest_language():
    """
    Ensure guest pages use the site's default language by setting
    the 'preferred_language' cookie to the site's default (pt-MZ) if missing.
    
    This function is called via before_request hook to ensure all guest
    users see the site in the correct language (Portuguese).
    """
    try:
        # Only apply to guest users
        if frappe.session.user != "Guest":
            return

        # Get the desired language from site settings
        desired = (
            frappe.db.get_default("lang")
            or frappe.db.get_single_value("System Settings", "language")
            or "pt-MZ"
        )

        # Check if the desired language is enabled
        enabled = set(frappe.translate.get_all_languages())
        if desired not in enabled and "-" in desired:
            # If pt-MZ is not available, fall back to pt
            parent = desired.split("-", 1)[0]
            if parent in enabled:
                desired = parent

        # Get current language preference from cookie
        current = frappe.request.cookies.get("preferred_language") if hasattr(frappe, "request") else None
        
        # Set the cookie if it's different or missing
        if current != desired and hasattr(frappe.local, "cookie_manager"):
            frappe.local.cookie_manager.set_cookie("preferred_language", desired)
            
    except Exception:
        frappe.log_error(title="enforce_guest_language failed", message=frappe.get_traceback())
