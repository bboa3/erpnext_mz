# -*- coding: utf-8 -*-
"""
Benefits in Kind Management for Mozambique

This module handles benefits in kind valuation and management:
- Vehicle benefits
- Housing benefits
- Insurance benefits
- Other non-cash benefits
"""

import frappe
from frappe import _
from datetime import datetime, date

class BenefitsInKind:
    """
    Benefits in Kind management class
    """
    
    def __init__(self, company):
        """
        Initialize Benefits in Kind manager
        
        Args:
            company (str): Company name
        """
        self.company = company
        self.company_doc = frappe.get_doc("Company", company)
    
    def calculate_vehicle_benefit(self, employee, vehicle_value, fuel_allowance=0):
        """
        Calculate vehicle benefit value
        
        Args:
            employee (str): Employee name
            vehicle_value (float): Vehicle market value
            fuel_allowance (float): Monthly fuel allowance
            
        Returns:
            dict: Vehicle benefit calculation
        """
        
        # Vehicle benefit calculation (simplified)
        # In real implementation, this would follow Mozambique tax rules
        
        monthly_benefit = (vehicle_value * 0.02) / 12  # 2% annual depreciation
        total_monthly_benefit = monthly_benefit + fuel_allowance
        
        return {
            "vehicle_value": vehicle_value,
            "monthly_depreciation": monthly_benefit,
            "fuel_allowance": fuel_allowance,
            "total_monthly_benefit": total_monthly_benefit,
            "annual_benefit": total_monthly_benefit * 12
        }
    
    def calculate_housing_benefit(self, employee, rent_amount, utilities=0):
        """
        Calculate housing benefit value
        
        Args:
            employee (str): Employee name
            rent_amount (float): Monthly rent amount
            utilities (float): Monthly utilities amount
            
        Returns:
            dict: Housing benefit calculation
        """
        
        # Housing benefit calculation
        # In Mozambique, housing benefits are typically valued at market rent
        total_monthly_benefit = rent_amount + utilities
        
        return {
            "rent_amount": rent_amount,
            "utilities": utilities,
            "total_monthly_benefit": total_monthly_benefit,
            "annual_benefit": total_monthly_benefit * 12
        }
    
    def calculate_insurance_benefit(self, employee, insurance_premium, coverage_type):
        """
        Calculate insurance benefit value
        
        Args:
            employee (str): Employee name
            insurance_premium (float): Monthly insurance premium
            coverage_type (str): Type of insurance coverage
            
        Returns:
            dict: Insurance benefit calculation
        """
        
        # Insurance benefit calculation
        # In Mozambique, employer-paid insurance is typically a taxable benefit
        
        return {
            "insurance_premium": insurance_premium,
            "coverage_type": coverage_type,
            "monthly_benefit": insurance_premium,
            "annual_benefit": insurance_premium * 12
        }
    
    def calculate_total_benefits(self, employee):
        """
        Calculate total benefits in kind for an employee
        
        Args:
            employee (str): Employee name
            
        Returns:
            dict: Total benefits calculation
        """
        
        # Get employee benefits from custom fields
        employee_doc = frappe.get_doc("Employee", employee)
        
        total_monthly_benefit = 0
        benefits_breakdown = {}
        
        # Vehicle benefit
        if hasattr(employee_doc, 'vehicle_benefit_enabled') and employee_doc.vehicle_benefit_enabled:
            vehicle_value = getattr(employee_doc, 'vehicle_value', 0) or 0
            fuel_allowance = getattr(employee_doc, 'fuel_allowance', 0) or 0
            
            vehicle_benefit = self.calculate_vehicle_benefit(employee, vehicle_value, fuel_allowance)
            total_monthly_benefit += vehicle_benefit['total_monthly_benefit']
            benefits_breakdown['vehicle'] = vehicle_benefit
        
        # Housing benefit
        if hasattr(employee_doc, 'housing_benefit_enabled') and employee_doc.housing_benefit_enabled:
            rent_amount = getattr(employee_doc, 'rent_amount', 0) or 0
            utilities = getattr(employee_doc, 'utilities_amount', 0) or 0
            
            housing_benefit = self.calculate_housing_benefit(employee, rent_amount, utilities)
            total_monthly_benefit += housing_benefit['total_monthly_benefit']
            benefits_breakdown['housing'] = housing_benefit
        
        # Insurance benefit
        if hasattr(employee_doc, 'insurance_benefit_enabled') and employee_doc.insurance_benefit_enabled:
            insurance_premium = getattr(employee_doc, 'insurance_premium', 0) or 0
            coverage_type = getattr(employee_doc, 'insurance_coverage_type', 'Health') or 'Health'
            
            insurance_benefit = self.calculate_insurance_benefit(employee, insurance_premium, coverage_type)
            total_monthly_benefit += insurance_benefit['monthly_benefit']
            benefits_breakdown['insurance'] = insurance_benefit
        
        return {
            "total_monthly_benefit": total_monthly_benefit,
            "total_annual_benefit": total_monthly_benefit * 12,
            "benefits_breakdown": benefits_breakdown
        }
    
    def create_benefits_salary_component(self, employee, benefit_type, amount):
        """
        Deprecated: avoid per-employee Salary Component creation.
        Use HRMS-native earnings/deductions with dynamic amounts.
        """
        return f"{benefit_type} Benefit"
    
    def update_employee_benefits(self, employee):
        """
        Update employee benefits in kind
        
        Args:
            employee (str): Employee name
            
        Returns:
            dict: Update result
        """
        
        try:
            # Calculate total benefits
            total_benefits = self.calculate_total_benefits(employee)
            
            # Update employee document
            employee_doc = frappe.get_doc("Employee", employee)
            employee_doc.total_benefits_in_kind = total_benefits['total_monthly_benefit']
            employee_doc.save()
            
            # Create or update salary components
            for benefit_type, benefit_data in total_benefits['benefits_breakdown'].items():
                component_name = self.create_benefits_salary_component(
                    employee, 
                    benefit_type.title(), 
                    benefit_data['total_monthly_benefit']
                )
                
                # Avoid linking per-employee components; amounts should be handled
                # via Salary Structure Assignment or Additional Salary.
            
            return {
                "success": True,
                "message": f"Benefits updated for {employee}",
                "total_monthly_benefit": total_benefits['total_monthly_benefit']
            }
            
        except Exception as e:
            frappe.log_error(f"Benefits update failed for {employee}: {str(e)}")
            return {
                "success": False,
                "message": f"Update failed: {str(e)}"
            }
    
    def _link_to_salary_structure(self, employee, component_name):
        """
        Link salary component to employee salary structure
        
        Args:
            employee (str): Employee name
            component_name (str): Salary component name
        """
        
        # Get employee salary structure
        salary_structures = frappe.get_all("Salary Structure Assignment",
                                         filters={"employee": employee, "docstatus": 1},
                                         fields=["salary_structure"],
                                         limit=1)
        
        if salary_structures:
            salary_structure = salary_structures[0].salary_structure
            
            # Check if component is already in structure
            existing_components = frappe.get_all("Salary Structure",
                                               filters={"name": salary_structure},
                                               fields=["earnings", "deductions"])
            
            if existing_components:
                structure_doc = frappe.get_doc("Salary Structure", salary_structure)
                
                # Add to earnings if not exists
                component_exists = False
                for earning in structure_doc.earnings:
                    if earning.salary_component == component_name:
                        component_exists = True
                        break
                
                if not component_exists:
                    new_earning = structure_doc.append("earnings", {})
                    new_earning.salary_component = component_name
                    new_earning.amount = 0  # Amount will be set per employee
                    structure_doc.save()

def create_benefits_custom_fields():
    """
    Create custom fields for benefits in kind
    """
    
    # Employee custom fields
    custom_fields = [
        {
            "dt": "Employee",
            "fieldname": "vehicle_benefit_enabled",
            "label": "Vehicle Benefit Enabled",
            "fieldtype": "Check",
            "insert_after": "employment_type"
        },
        {
            "dt": "Employee",
            "fieldname": "vehicle_value",
            "label": "Vehicle Value (MZN)",
            "fieldtype": "Currency",
            "insert_after": "vehicle_benefit_enabled",
            "depends_on": "eval:doc.vehicle_benefit_enabled"
        },
        {
            "dt": "Employee",
            "fieldname": "fuel_allowance",
            "label": "Fuel Allowance (MZN/month)",
            "fieldtype": "Currency",
            "insert_after": "vehicle_value",
            "depends_on": "eval:doc.vehicle_benefit_enabled"
        },
        {
            "dt": "Employee",
            "fieldname": "housing_benefit_enabled",
            "label": "Housing Benefit Enabled",
            "fieldtype": "Check",
            "insert_after": "fuel_allowance"
        },
        {
            "dt": "Employee",
            "fieldname": "rent_amount",
            "label": "Rent Amount (MZN/month)",
            "fieldtype": "Currency",
            "insert_after": "housing_benefit_enabled",
            "depends_on": "eval:doc.housing_benefit_enabled"
        },
        {
            "dt": "Employee",
            "fieldname": "utilities_amount",
            "label": "Utilities Amount (MZN/month)",
            "fieldtype": "Currency",
            "insert_after": "rent_amount",
            "depends_on": "eval:doc.housing_benefit_enabled"
        },
        {
            "dt": "Employee",
            "fieldname": "insurance_benefit_enabled",
            "label": "Insurance Benefit Enabled",
            "fieldtype": "Check",
            "insert_after": "utilities_amount"
        },
        {
            "dt": "Employee",
            "fieldname": "insurance_premium",
            "label": "Insurance Premium (MZN/month)",
            "fieldtype": "Currency",
            "insert_after": "insurance_benefit_enabled",
            "depends_on": "eval:doc.insurance_benefit_enabled"
        },
        {
            "dt": "Employee",
            "fieldname": "insurance_coverage_type",
            "label": "Insurance Coverage Type",
            "fieldtype": "Select",
            "options": "Health\nLife\nVehicle\nOther",
            "insert_after": "insurance_premium",
            "depends_on": "eval:doc.insurance_benefit_enabled"
        },
        {
            "dt": "Employee",
            "fieldname": "total_benefits_in_kind",
            "label": "Total Benefits in Kind (MZN/month)",
            "fieldtype": "Currency",
            "insert_after": "insurance_coverage_type",
            "read_only": 1
        }
    ]
    
    for field_data in custom_fields:
        if not frappe.db.exists("Custom Field", {"fieldname": field_data["fieldname"], "dt": field_data["dt"]}):
            custom_field = frappe.new_doc("Custom Field")
            custom_field.update(field_data)
            custom_field.insert()
    
    frappe.msgprint(_("Benefits in kind custom fields created successfully"))
