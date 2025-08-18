# -*- coding: utf-8 -*-
"""
Permissions for ERPNext Mozambique Custom App

This module handles custom permissions for Mozambique compliance features.
"""

import frappe
from frappe import _

def has_sales_invoice_permission(doc=None, ptype=None, user=None):
    """
    Check if user has permission for Sales Invoice operations
    
    Args:
        user (str): User name
        ptype (str): Permission type (read, write, create, delete)
        share (int): Share permission
        flags (dict): Additional flags
        
    Returns:
        bool: True if user has permission
    """
    
    # Basic permission check
    if not user:
        user = frappe.session.user
    
    # Admin users have all permissions
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Check specific permissions based on type
    if ptype == "read":
        return True  # All users can read invoices
    
    elif ptype in ["write", "create"]:
        # Users with Sales User role can create/edit
        if "Sales User" in frappe.get_roles(user):
            return True
    
    elif ptype == "delete":
        # Only System Manager can delete
        if "System Manager" in frappe.get_roles(user):
            return True
    
    return False

def has_payroll_permission(doc=None, ptype=None, user=None):
    """
    Check if user has permission for Payroll Entry operations
    
    Args:
        user (str): User name
        ptype (str): Permission type (read, write, create, delete)
        share (int): Share permission
        flags (dict): Additional flags
        
    Returns:
        bool: True if user has permission
    """
    
    # Basic permission check
    if not user:
        user = frappe.session.user
    
    # Admin users have all permissions
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Check specific permissions based on type
    if ptype == "read":
        return True  # All users can read payroll
    
    elif ptype in ["write", "create"]:
        # Users with HR User role can create/edit
        if "HR User" in frappe.get_roles(user):
            return True
    
    elif ptype == "delete":
        # Only System Manager can delete
        if "System Manager" in frappe.get_roles(user):
            return True
    
    return False

def has_saf_t_permission(doc=None, ptype=None, user=None):
    """
    Check if user has permission for SAF-T operations
    
    Args:
        user (str): User name
        ptype (str): Permission type (read, write, create, delete)
        share (int): Share permission
        flags (dict): Additional flags
        
    Returns:
        bool: True if user has permission
    """
    
    # Basic permission check
    if not user:
        user = frappe.session.user
    
    # Admin users have all permissions
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Check specific permissions based on type
    if ptype == "read":
        # Users with Accounts User role can read SAF-T
        if "Accounts User" in frappe.get_roles(user):
            return True
    
    elif ptype in ["write", "create"]:
        # Users with Accounts Manager role can create/edit
        if "Accounts Manager" in frappe.get_roles(user):
            return True
    
    elif ptype == "delete":
        # Only System Manager can delete
        if "System Manager" in frappe.get_roles(user):
            return True
    
    return False
