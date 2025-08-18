# -*- coding: utf-8 -*-
"""
SAF-T XML Generator for Mozambique

This module generates SAF-T XML files for:
- Sales (Vendas)
- Payroll (Folha de Pagamento)

Following Mozambique AT specifications and requirements.
"""

import frappe
from frappe import _
import xml.etree.ElementTree as ET
from xml.dom import minidom
import hashlib
from frappe.utils import now_datetime, getdate
import json
import os
# lxml is optional; only used for XSD validation if available
try:
    from lxml import etree  # type: ignore
except Exception:
    etree = None  # Optional dependency

class SAFTGenerator:
    """
    SAF-T XML Generator for Mozambique compliance
    """
    
    def __init__(self, company, period_start, period_end):
        """
        Initialize SAF-T generator
        
        Args:
            company (str): Company name
            period_start (str): Period start date (YYYY-MM-DD)
            period_end (str): Period end date (YYYY-MM-DD)
        """
        self.company = company
        self.period_start = period_start
        self.period_end = period_end
        self.company_doc = frappe.get_doc("Company", company)
        
    def generate_sales_saf_t(self):
        """
        Generate SAF-T XML for sales
        
        Returns:
            str: XML content
        """
        
        try:
            # Create root element
            root = ET.Element("SAFT")
            root.set("xmlns", "urn:OECD:StandardAuditFile-Tax:Mozambique")
            root.set("version", "1.0")
            
            # Header
            header = ET.SubElement(root, "Header")
            self._add_header_info(header)
            
            # Master files
            master_files = ET.SubElement(root, "MasterFiles")
            self._add_customer_master(master_files)
            self._add_product_master(master_files)
            
            # General ledger entries
            general_ledger = ET.SubElement(root, "GeneralLedgerEntries")
            self._add_sales_entries(general_ledger)
            
            # Source documents
            source_documents = ET.SubElement(root, "SourceDocuments")
            self._add_sales_invoices(source_documents)
            
            return self._format_xml(root)
        except Exception as e:
            frappe.log_error(f"Failed to generate sales SAF-T: {str(e)}")
            raise frappe.ValidationError(_("A geração do SAF-T de Vendas falhou: {0}").format(str(e)))
    
    def generate_payroll_saf_t(self):
        """
        Generate SAF-T XML for payroll
        
        Returns:
            str: XML content
        """
        
        try:
            # Create root element
            root = ET.Element("SAFT")
            root.set("xmlns", "urn:OECD:StandardAuditFile-Tax:Mozambique")
            root.set("version", "1.0")
            
            # Header
            header = ET.SubElement(root, "Header")
            self._add_header_info(header)
            
            # Master files
            master_files = ET.SubElement(root, "MasterFiles")
            self._add_employee_master(master_files)
            
            # General ledger entries
            general_ledger = ET.SubElement(root, "GeneralLedgerEntries")
            self._add_payroll_entries(general_ledger)
            
            # Source documents
            source_documents = ET.SubElement(root, "SourceDocuments")
            self._add_payroll_entries_docs(source_documents)
            
            return self._format_xml(root)
        except Exception as e:
            frappe.log_error(f"Failed to generate payroll SAF-T: {str(e)}")
            raise frappe.ValidationError(_("A geração do SAF-T de Folha falhou: {0}").format(str(e)))
    
    def _add_header_info(self, header):
        """Add header information to SAF-T"""
        
        # Company info
        company_info = ET.SubElement(header, "CompanyInfo")
        ET.SubElement(company_info, "CompanyName").text = getattr(self.company_doc, 'company_name', '')
        ET.SubElement(company_info, "CompanyAddress").text = self._get_company_address() or ''
        # Prefer Company.nuit, fallback to tax_id
        nuit_value = getattr(self.company_doc, 'nuit', '') or getattr(self.company_doc, 'tax_id', '') or ''
        ET.SubElement(company_info, "NUIT").text = nuit_value
        # ATCertificationNumber not required in system metadata
        
        # Period info
        period_info = ET.SubElement(header, "PeriodInfo")
        ET.SubElement(period_info, "StartDate").text = self.period_start
        ET.SubElement(period_info, "EndDate").text = self.period_end
        
        # Generation info
        generation_info = ET.SubElement(header, "GenerationInfo")
        ET.SubElement(generation_info, "GenerationDate").text = getdate().strftime("%Y-%m-%d")
        ET.SubElement(generation_info, "GenerationTime").text = now_datetime().strftime("%H:%M:%S")
        ET.SubElement(generation_info, "SoftwareVersion").text = "ERPNext Mozambique 1.0.0"

    def _get_company_address(self):
        """Fetch a reliable default address text for the company."""
        try:
            # Prefer a primary Address linked to Company
            link_filters = {
                "link_doctype": "Company",
                "link_name": self.company,
            }
            address_links = frappe.get_all(
                "Dynamic Link",
                filters=link_filters,
                fields=["parent"],
                limit=1,
            )
            if address_links:
                address_name = address_links[0].parent
                addr = frappe.get_doc("Address", address_name)
                return ", ".join(
                    [
                        part
                        for part in [
                            getattr(addr, "address_line1", None),
                            getattr(addr, "address_line2", None),
                            getattr(addr, "city", None),
                            getattr(addr, "state", None),
                            getattr(addr, "pincode", None),
                            getattr(addr, "country", None),
                        ]
                        if part
                    ]
                )
        except Exception:
            pass
        # Fallback to Company fields (some setups have custom address fields)
        return getattr(self.company_doc, 'registered_address', None) or getattr(self.company_doc, 'address', None)
    
    def _add_customer_master(self, master_files):
        """Add customer master data"""
        
        customers = ET.SubElement(master_files, "Customers")
        
        # Get all customers (include 'nuit' only if the field exists)
        customer_fields = ["name", "customer_name", "tax_id"]
        try:
            if frappe.get_meta("Customer").has_field("nuit"):
                customer_fields.append("nuit")
        except Exception:
            pass
        customer_list = frappe.get_all("Customer", fields=customer_fields)
        
        for customer_data in customer_list:
            customer = ET.SubElement(customers, "Customer")
            ET.SubElement(customer, "CustomerID").text = customer_data.name
            ET.SubElement(customer, "CustomerName").text = customer_data.customer_name
            ET.SubElement(customer, "NUIT").text = getattr(customer_data, "nuit", "") or ""
            ET.SubElement(customer, "TaxID").text = customer_data.tax_id or ""
    
    def _add_product_master(self, master_files):
        """Add product master data"""
        
        products = ET.SubElement(master_files, "Products")
        
        # Get all items (avoid fields not present in this ERPNext version)
        item_list = frappe.get_all(
            "Item",
            fields=["name", "item_name", "item_group"],
        )
        
        for item_data in item_list:
            product = ET.SubElement(products, "Product")
            ET.SubElement(product, "ProductID").text = item_data.name
            ET.SubElement(product, "ProductName").text = item_data.item_name
            ET.SubElement(product, "ProductGroup").text = item_data.item_group or ""
            ET.SubElement(product, "TaxCategory").text = ""
    
    def _add_employee_master(self, master_files):
        """Add employee master data"""
        
        employees = ET.SubElement(master_files, "Employees")
        
        # Get all employees for the company
        employee_list = frappe.get_all("Employee", 
                                     filters={"company": self.company},
                                     fields=["name", "employee_name"])
        
        for employee_data in employee_list:
            employee = ET.SubElement(employees, "Employee")
            ET.SubElement(employee, "EmployeeID").text = employee_data.name
            ET.SubElement(employee, "EmployeeName").text = employee_data.employee_name
            ET.SubElement(employee, "NUIT").text = ""
            ET.SubElement(employee, "NationalID").text = ""
    
    def _add_sales_entries(self, general_ledger):
        """Add sales general ledger entries"""
        
        # Get sales invoices for the period
        sales_invoices = frappe.get_all("Sales Invoice",
                                      filters={
                                          "company": self.company,
                                          "posting_date": ["between", [self.period_start, self.period_end]],
                                          "docstatus": 1
                                      },
                                      fields=["name", "posting_date", "grand_total", "total_taxes_and_charges"])
        
        for invoice in sales_invoices:
            entry = ET.SubElement(general_ledger, "Entry")
            ET.SubElement(entry, "EntryNumber").text = invoice.name
            ET.SubElement(entry, "EntryDate").text = invoice.posting_date
            ET.SubElement(entry, "EntryType").text = "Sales"
            ET.SubElement(entry, "TotalAmount").text = str(invoice.grand_total)
            ET.SubElement(entry, "TotalTaxes").text = str(invoice.total_taxes_and_charges)
    
    def _add_payroll_entries(self, general_ledger):
        """Add payroll general ledger entries"""
        
        # Get payroll entries for the period
        payroll_entries = frappe.get_all(
            "Payroll Entry",
            filters={
                "company": self.company,
                "posting_date": ["between", [self.period_start, self.period_end]],
                # include draft and submitted; exclude cancelled
                "docstatus": ["!=", 2],
            },
            fields=["name", "posting_date"],
        )
        
        for payroll in payroll_entries:
            entry = ET.SubElement(general_ledger, "Entry")
            ET.SubElement(entry, "EntryNumber").text = payroll.name
            ET.SubElement(entry, "EntryDate").text = payroll.posting_date
            ET.SubElement(entry, "EntryType").text = "Payroll"
            ET.SubElement(entry, "TotalAmount").text = "0"
    
    def _add_sales_invoices(self, source_documents):
        """Add sales invoice source documents"""
        
        sales_invoices = ET.SubElement(source_documents, "SalesInvoices")
        
        # Get sales invoices for the period
        invoice_list = frappe.get_all("Sales Invoice",
                                    filters={
                                        "company": self.company,
                                        "posting_date": ["between", [self.period_start, self.period_end]],
                                        "docstatus": 1
                                    },
                                    fields=["name", "posting_date", "customer", "grand_total", "total_taxes_and_charges"])
        
        for invoice_data in invoice_list:
            invoice = ET.SubElement(sales_invoices, "Invoice")
            ET.SubElement(invoice, "InvoiceNumber").text = invoice_data.name
            ET.SubElement(invoice, "InvoiceDate").text = invoice_data.posting_date
            ET.SubElement(invoice, "CustomerID").text = invoice_data.customer
            ET.SubElement(invoice, "TotalAmount").text = str(invoice_data.grand_total)
            ET.SubElement(invoice, "TotalTaxes").text = str(invoice_data.total_taxes_and_charges)
    
    def _add_payroll_entries_docs(self, source_documents):
        """Add payroll entry source documents"""
        
        payroll_entries = ET.SubElement(source_documents, "PayrollEntries")
        
        # Get payroll entries for the period
        payroll_list = frappe.get_all(
            "Payroll Entry",
            filters={
                "company": self.company,
                "posting_date": ["between", [self.period_start, self.period_end]],
                "docstatus": ["!=", 2],
            },
            fields=["name", "posting_date"],
        )
        
        for payroll_data in payroll_list:
            payroll = ET.SubElement(payroll_entries, "PayrollEntry")
            ET.SubElement(payroll, "EntryNumber").text = payroll_data.name
            ET.SubElement(payroll, "EntryDate").text = payroll_data.posting_date
            ET.SubElement(payroll, "TotalAmount").text = "0"

            # Include Benefits in Kind aggregated per payroll entry (best-effort)
            try:
                # Skip if HRMS/Salary Slip not available
                if not frappe.db.table_exists("tabSalary Slip") or not frappe.db.table_exists("tabEmployee"):
                    continue

                # Import lazily to avoid hard dependency
                try:
                    from erpnext_mz.modules.hr_payroll.benefits_in_kind import BenefitsInKind  # type: ignore
                except Exception:
                    BenefitsInKind = None  # type: ignore

                if BenefitsInKind is None:
                    continue

                slips = frappe.get_all(
                    "Salary Slip",
                    filters={"payroll_entry": payroll_data.name},
                    fields=["employee"],
                )

                if not slips:
                    continue

                benefits_root = ET.SubElement(payroll, "BenefitsInKind")
                bik_manager = BenefitsInKind(self.company)
                total_bik = 0.0
                seen_employees = set()
                for slip in slips:
                    emp = slip.employee
                    if not emp or emp in seen_employees:
                        continue
                    seen_employees.add(emp)
                    try:
                        calc = bik_manager.calculate_total_benefits(emp)
                        monthly_benefit = float(calc.get("total_monthly_benefit", 0) or 0)
                    except Exception:
                        monthly_benefit = 0.0
                    if monthly_benefit <= 0:
                        continue
                    emp_node = ET.SubElement(benefits_root, "Employee")
                    ET.SubElement(emp_node, "EmployeeID").text = emp
                    ET.SubElement(emp_node, "MonthlyBenefitsInKind").text = str(monthly_benefit)
                    total_bik += monthly_benefit

                ET.SubElement(benefits_root, "TotalBenefitsInKind").text = str(total_bik)
            except Exception:
                # Never block file generation on optional enrichment
                continue
    
    def _format_xml(self, root):
        """Format XML with proper indentation"""
        
        try:
            rough_string = ET.tostring(root, 'unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception as e:
            frappe.log_error(f"Failed to format XML: {str(e)}")
            # Fallback to basic formatting
            return ET.tostring(root, 'unicode')
    
    def generate_checksum(self, xml_content):
        """
        Generate checksum for XML content
        
        Args:
            xml_content (str): XML content
            
        Returns:
            str: SHA-256 checksum
        """
        
        return hashlib.sha256(xml_content.encode('utf-8')).hexdigest()
    
    def save_saf_t_file(self, xml_content, file_type, period):
        """
        Save SAF-T file to the system
        
        Args:
            xml_content (str): XML content
            file_type (str): 'sales' or 'payroll'
            period (str): Period identifier (e.g., '2025-01')
            
        Returns:
            str: File path
        """
        
        filename = f"SAFT_{file_type}_{period}_{self.company}_{now_datetime().strftime('%Y%m%d_%H%M%S')}.xml"
        
        # Create file document
        file_doc = frappe.new_doc("File")
        file_doc.file_name = filename
        file_doc.content = xml_content
        file_doc.attached_to_doctype = "Company"
        file_doc.attached_to_name = self.company
        file_doc.insert()
        
        # Save to filesystem using Frappe's file handling
        try:
            # Use Frappe's file system path
            from frappe.utils import get_site_path
            site_path = get_site_path()
            file_path = os.path.join(site_path, "public", "files", filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            return file_path
        except Exception as e:
            frappe.log_error(f"Failed to save SAF-T file: {str(e)}")
            # Return the file document reference instead
            return f"File: {file_doc.name}"

    def _validate_against_schema(self, xml_content: str) -> None:
        """Validate SAF-T XML against an XSD if available on disk.

        Non-blocking if schema is missing; raises ValidationError on schema errors if present.
        """
        try:
            # Skip if lxml is not available
            if etree is None:
                return
            from frappe.utils import get_site_path
            schema_path = os.path.join(get_site_path(), "private", "schemas", "saft_mz.xsd")
            if not os.path.exists(schema_path):
                return
            schema_doc = etree.parse(schema_path)
            schema = etree.XMLSchema(schema_doc)
            parser = etree.XMLParser(schema=schema)
            etree.fromstring(xml_content.encode("utf-8"), parser)
        except etree.XMLSchemaError as e:
            frappe.log_error(f"SAF-T XSD validation error: {str(e)}")
            raise frappe.ValidationError("SAF-T XML failed schema validation")
        except Exception:
            # Do not block if lxml not fully available or other IO issues
            return

def generate_monthly_saf_t(company, year, month):
    """
    Generate monthly SAF-T files for a company
    
    Args:
        company (str): Company name
        year (int): Year
        month (int): Month
        
    Returns:
        dict: Generated files info
    """
    
    try:
        period_start = f"{year}-{month:02d}-01"
        
        # Calculate last day of month
        if month == 12:
            period_end = f"{year + 1}-01-01"
        else:
            period_end = f"{year}-{month + 1:02d}-01"
        
        # Adjust to last day of current month
        from frappe.utils import add_days, getdate
        end_date = add_days(getdate(period_end), -1)
        period_end = end_date.strftime("%Y-%m-%d")
        
        generator = SAFTGenerator(company, period_start, period_end)
        
        # Generate SAF-T files
        sales_xml = generator.generate_sales_saf_t()
        # Generate payroll only if HRMS tables exist; otherwise skip gracefully
        payroll_xml = None
        try:
            if frappe.db.table_exists("tabPayroll Entry"):
                payroll_xml = generator.generate_payroll_saf_t()
        except Exception as _e:
            # Skip payroll if HRMS not installed or doctype missing
            payroll_xml = None
        
        # Save files (validate against XSD if available)
        period_id = f"{year}-{month:02d}"
        generator._validate_against_schema(sales_xml)
        sales_file = generator.save_saf_t_file(sales_xml, "sales", period_id)
        payroll_file = generator.save_saf_t_file(payroll_xml, "payroll", period_id) if payroll_xml else None
        
        # Generate checksums
        sales_checksum = generator.generate_checksum(sales_xml)
        payroll_checksum = generator.generate_checksum(payroll_xml) if payroll_xml else None
        
        return {
            "sales_file": sales_file,
            "payroll_file": payroll_file,
            "sales_checksum": sales_checksum,
            "payroll_checksum": payroll_checksum,
            "sales_xml": sales_xml,
            "payroll_xml": payroll_xml,
            "period": period_id,
            "generation_date": now_datetime().isoformat(),
        }
    except Exception as e:
        frappe.log_error(f"Monthly SAF-T generation failed for {company}: {str(e)}")
        raise frappe.ValidationError(f"Monthly SAF-T generation failed: {str(e)}")
