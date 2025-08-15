# -*- coding: utf-8 -*-
"""
INSS and IRPS Calculations for Mozambique

This module handles:
- INSS calculations (4% employer, 3% employee)
- IRPS progressive tax brackets
- Tax calculations and reporting
"""

import frappe
from frappe import _

# INSS rates for Mozambique
INSS_EMPLOYER_RATE = 4.0  # 4%
INSS_EMPLOYEE_RATE = 3.0  # 3%

# IRPS progressive tax brackets (2025 rates)
IRPS_BRACKETS = [
    {
        "min_amount": 0,
        "max_amount": 50000,  # 50,000 MZN
        "rate": 10.0,
        "description": "Primeira faixa - 10%"
    },
    {
        "min_amount": 50000,
        "max_amount": 100000,  # 100,000 MZN
        "rate": 15.0,
        "description": "Segunda faixa - 15%"
    },
    {
        "min_amount": 100000,
        "max_amount": 200000,  # 200,000 MZN
        "rate": 20.0,
        "description": "Terceira faixa - 20%"
    },
    {
        "min_amount": 200000,
        "max_amount": 500000,  # 500,000 MZN
        "rate": 25.0,
        "description": "Quarta faixa - 25%"
    },
    {
        "min_amount": 500000,
        "max_amount": float('inf'),  # Above 500,000 MZN
        "rate": 32.0,
        "description": "Quinta faixa - 32%"
    }
]

def calculate_inss_contributions(gross_salary, company):
    """
    Calculate INSS contributions for employer and employee
    
    Args:
        gross_salary (float): Gross salary amount
        company (str): Company name
        
    Returns:
        dict: INSS calculations
    """
    
    # Get company-specific INSS rates if configured
    employer_rate = get_company_inss_rate(company, "employer")
    employee_rate = get_company_inss_rate(company, "employee")
    
    # Calculate contributions
    employer_contribution = (gross_salary * employer_rate) / 100
    employee_contribution = (gross_salary * employee_rate) / 100
    
    return {
        "gross_salary": gross_salary,
        "employer_rate": employer_rate,
        "employee_rate": employee_rate,
        "employer_contribution": employer_contribution,
        "employee_contribution": employee_contribution,
        "total_contribution": employer_contribution + employee_contribution
    }

def calculate_irps_tax(taxable_income, company):
    """
    Calculate IRPS tax using progressive brackets
    
    Args:
        taxable_income (float): Taxable income amount
        company (str): Company name
        
    Returns:
        dict: IRPS calculations
    """
    
    total_tax = 0
    tax_breakdown = []
    
    for bracket in IRPS_BRACKETS:
        min_amount = bracket["min_amount"]
        max_amount = bracket["max_amount"]
        rate = bracket["rate"]
        
        if taxable_income > min_amount:
            # Calculate taxable amount for this bracket
            if max_amount == float('inf'):
                bracket_amount = taxable_income - min_amount
            else:
                bracket_amount = min(taxable_income - min_amount, max_amount - min_amount)
            
            if bracket_amount > 0:
                bracket_tax = (bracket_amount * rate) / 100
                total_tax += bracket_tax
                
                tax_breakdown.append({
                    "bracket": bracket["description"],
                    "min_amount": min_amount,
                    "max_amount": max_amount if max_amount != float('inf') else "∞",
                    "rate": rate,
                    "bracket_amount": bracket_amount,
                    "bracket_tax": bracket_tax
                })
    
    return {
        "taxable_income": taxable_income,
        "total_tax": total_tax,
        "effective_rate": (total_tax / taxable_income * 100) if taxable_income > 0 else 0,
        "tax_breakdown": tax_breakdown
    }

def calculate_net_salary(gross_salary, benefits_in_kind=0, company=None):
    """
    Calculate net salary after INSS and IRPS
    
    Args:
        gross_salary (float): Gross salary amount
        benefits_in_kind (float): Benefits in kind value
        company (str): Company name
        
    Returns:
        dict: Complete salary breakdown
    """
    
    # Calculate INSS
    inss_calc = calculate_inss_contributions(gross_salary, company)
    
    # Calculate taxable income (gross + benefits - INSS employee contribution)
    taxable_income = gross_salary + benefits_in_kind - inss_calc["employee_contribution"]
    
    # Calculate IRPS
    irps_calc = calculate_irps_tax(taxable_income, company)
    
    # Calculate net salary
    net_salary = gross_salary - inss_calc["employee_contribution"] - irps_calc["total_tax"]
    
    return {
        "gross_salary": gross_salary,
        "benefits_in_kind": benefits_in_kind,
        "inss_employer": inss_calc["employer_contribution"],
        "inss_employee": inss_calc["employee_contribution"],
        "taxable_income": taxable_income,
        "irps_tax": irps_calc["total_tax"],
        "net_salary": net_salary,
        "total_deductions": inss_calc["employee_contribution"] + irps_calc["total_tax"],
        "inss_breakdown": inss_calc,
        "irps_breakdown": irps_calc
    }

def get_company_inss_rate(company, rate_type):
    """
    Get company-specific INSS rate if configured
    
    Args:
        company (str): Company name
        rate_type (str): 'employer' or 'employee'
        
    Returns:
        float: INSS rate
    """
    
    # Default rates
    default_rates = {
        "employer": INSS_EMPLOYER_RATE,
        "employee": INSS_EMPLOYEE_RATE
    }
    
    # Check if company has custom rates configured
    company_settings = frappe.get_doc("Company", company)
    
    if hasattr(company_settings, 'custom_inss_employer_rate') and rate_type == "employer":
        return company_settings.custom_inss_employer_rate or default_rates["employer"]
    
    if hasattr(company_settings, 'custom_inss_employee_rate') and rate_type == "employee":
        return company_settings.custom_inss_employee_rate or default_rates["employee"]
    
    return default_rates[rate_type]

def create_inss_salary_component(company):
    """
    Create INSS salary component for the company
    
    Args:
        company (str): Company name
    """
    
    component_name = "INSS - Empregador"
    
    if frappe.db.exists("Salary Component", {"name": component_name, "company": company}):
        return
    
    # Ensure HRMS/Salary Component doctype exists
    if not frappe.db.table_exists("tabSalary Component"):
        frappe.msgprint(_("Skipping INSS Salary Component creation: HRMS app not installed"))
        return

    component = frappe.new_doc("Salary Component")
    component.name = component_name
    component.type = "Earning"
    component.company = company
    component.description = "Contribuição INSS do empregador (4%) - contabilizada via contrapartida nas despesas de pessoal"
    component.condition = ""  # always applies when included in structure
    component.do_not_include_in_total = 1
    component.statistical_component = 1
    component.formula = "base * 0.04"
    component.insert()
    
    frappe.msgprint(_("INSS salary component created successfully"))

def create_irps_salary_component(company):
    """
    Create IRPS salary component for the company
    
    Args:
        company (str): Company name
    """
    
    component_name = "IRPS"
    
    if frappe.db.exists("Salary Component", {"name": component_name, "company": company}):
        return
    
    # Ensure HRMS/Salary Component doctype exists
    if not frappe.db.table_exists("tabSalary Component"):
        frappe.msgprint(_("Skipping IRPS Salary Component creation: HRMS app not installed"))
        return

    component = frappe.new_doc("Salary Component")
    component.name = component_name
    component.type = "Deduction"
    component.company = company
    component.description = "Imposto sobre Rendimentos de Pessoas Singulares"
    component.condition = ""  # evaluated per-employee in HRMS engine
    component.formula = "0"  # encourage rule-based calculation elsewhere
    component.insert()
    
    frappe.msgprint(_("IRPS salary component created successfully"))

def get_mozambique_payroll_components(company):
    """
    Get all Mozambique payroll components for a company
    
    Args:
        company (str): Company name
        
    Returns:
        list: List of salary component names
    """
    
    components = frappe.get_all("Salary Component",
                               filters={"company": company},
                               fields=["name", "type", "description"])
    return components
