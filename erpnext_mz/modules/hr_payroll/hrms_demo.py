# -*- coding: utf-8 -*-
"""
Minimal HRMS demo data creator to enable payroll doctypes and test SAF-T payroll export.

This avoids complex flows and only creates the minimum viable records.
"""

from __future__ import annotations

import frappe


def create_demo_payroll_data(company: str) -> dict:
    """
    Create minimal HRMS demo data for a company.

    Returns a summary of created/ensured records.
    """
    summary = {
        "employee": None,
        "salary_components": [],
        "salary_structure": None,
        "salary_structure_assignment": None,
        "payroll_entry": None,
    }

    # Ensure Employee
    employee_name = frappe.db.get_value("Employee", {"company": company}, "name")
    if not employee_name:
        employee = frappe.new_doc("Employee")
        employee.employee_name = "Demo Employee"
        employee.first_name = "Demo"
        employee.last_name = "Employee"
        employee.company = company
        employee.gender = "Male"
        employee.date_of_birth = "1990-01-01"
        employee.date_of_joining = "2024-01-01"
        try:
            # Optional fields that may be mandatory depending on installation
            if hasattr(employee, "status") and not employee.status:
                employee.status = "Active"
        except Exception:
            pass
        employee.insert()
        employee_name = employee.name
    summary["employee"] = employee_name

    # Ensure Salary Components
    def ensure_component(component: str, comp_type: str) -> None:
        # Some setups use name as primary key of component label; check by both name and field
        if frappe.db.exists("Salary Component", component) or frappe.db.exists(
            "Salary Component", {"salary_component": component}
        ):
            return
        sc = frappe.new_doc("Salary Component")
        sc.salary_component = component
        sc.type = comp_type
        try:
            sc.company = company
        except Exception:
            pass
        sc.insert()
        summary["salary_components"].append(component)

    ensure_component("Basic", "Earning")
    ensure_component("INSS - Empregador", "Deduction")

    # Ensure Salary Structure with a basic earning row
    if not frappe.db.exists("Salary Structure", {"name": "Demo Structure"}):
        ss = frappe.new_doc("Salary Structure")
        ss.name = "Demo Structure"
        ss.company = company
        ss.payroll_frequency = "Monthly"
        ss.append("earnings", {"salary_component": "Basic", "amount": 1000})
        ss.insert()
        summary["salary_structure"] = ss.name
    else:
        summary["salary_structure"] = "Demo Structure"

    # Ensure Salary Structure Assignment
    if employee_name and not frappe.db.exists("Salary Structure Assignment", {"employee": employee_name}):
        ssa = frappe.new_doc("Salary Structure Assignment")
        ssa.employee = employee_name
        ssa.company = company
        ssa.salary_structure = "Demo Structure"
        ssa.from_date = "2025-01-01"
        ssa.base = 1000
        ssa.insert()
        summary["salary_structure_assignment"] = ssa.name

    # Create a simple Payroll Entry (draft or submit if possible)
    try:
        pe = frappe.new_doc("Payroll Entry")
        pe.company = company
        pe.payroll_frequency = "Monthly"
        pe.posting_date = frappe.utils.today()
        pe.start_date = frappe.utils.add_days(frappe.utils.today(), -30)
        pe.end_date = frappe.utils.today()
        pe.insert()
        try:
            pe.submit()
        except Exception:
            # Keep as draft if workflow prevents submit in this environment
            pass
        summary["payroll_entry"] = pe.name
    except Exception:
        # If doctype/workflow constraints fail, still return summary for created masters
        pass

    return summary


