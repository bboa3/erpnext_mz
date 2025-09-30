#!/usr/bin/env python3
"""
Mozambique Print Format Templates - Base System

This module provides a comprehensive base system for creating professional
print formats for all business documents in Mozambique ERPNext implementation.

Features:
- Modular template system
- Consistent design across all documents
- Mozambique-specific compliance
- QR code integration
- Bilingual support (Portuguese/English)
- Professional styling
"""

import frappe
from frappe import _


class PrintFormatTemplate:
    """Base class for all print format templates"""
    
    def __init__(self, doc_type, format_name, module="ERPNext MZ"):
        self.doc_type = doc_type
        self.format_name = format_name
        self.module = module
        self.base_css = self._get_base_css()
    
    def create_print_format(self):
        """Create the print format document"""
        try:
            print_format = None
            # Check if print format already exists
            if frappe.db.exists("Print Format", self.format_name):
                    # Update existing print format
                print_format = frappe.get_doc("Print Format", self.format_name)
            else:
                # Create new print format
                print_format = frappe.new_doc("Print Format")
        
            if print_format is None:
                frappe.log_error(_("Print Format '{0}' does not exist").format(self.format_name), "Print Format Creation")
                return None
            
            # Set/update the print format properties
            print_format.update({
                "name": self.format_name,
                "doc_type": self.doc_type,
                "module": self.module,
                "standard": "No",
                "custom_format": 1,
                "print_format_type": "Jinja",
                "raw_printing": 0,
                "font": "Default",
                "font_size": 12,
                "margin_top": 15.0,
                "margin_bottom": 15.0,
                "margin_left": 15.0,
                "margin_right": 15.0,
                "align_labels_right": 0,
                "show_section_headings": 1,
                "line_breaks": 0,
                "absolute_value": 0,
                "page_number": "Bottom Center",
                "default_print_language": "pt",
                "disabled": 0
            })
            
            # Set/update the HTML template and CSS
            print_format.html = self.get_html_template()
            print_format.css = self.get_css_styles()
            
            # Save the print format
            if frappe.db.exists("Print Format", self.format_name):
                print_format.save(ignore_permissions=True)
                frappe.msgprint(_("Successfully updated '{0}' print format").format(self.format_name))
            else:
                print_format.insert(ignore_permissions=True)
                frappe.msgprint(_("Successfully created '{0}' print format").format(self.format_name))
            
            frappe.db.commit()
            return print_format.name
            
        except Exception as e:
            frappe.log_error(f"Error creating/updating print format {self.format_name}: {str(e)}")
            frappe.throw(_("Failed to create/update print format: {0}").format(str(e)))
    
    def get_html_template(self):
        """Override in subclasses to provide specific HTML template"""
        raise NotImplementedError("Subclasses must implement get_html_template")
    
    def get_css_styles(self):
        """Override in subclasses to provide specific CSS styles"""
        return self.base_css
    
    def _get_base_css(self):
        """Base CSS styles shared across all print formats"""
        return """
        /* Mozambique Print Format Base Styles */

        .print-format {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 12px;
            line-height: 1.5;
            color: #333;
            background: #fff;
        }

        /* Document Header */
        .document-header {
            border-bottom: 1px solid #7f8c8d;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }

        .document-title {
            color: #2c3e50;
            font-size: 24px;
            font-weight: 600;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .document-subtitle {
            color: #7f8c8d;
            font-size: 12px;
            margin: 2px 0 0 0;
            font-weight: 400;
        }

        .document-number {
            font-size: 16px;
            color: #2c3e50;
            margin-bottom: 2px;
        }

        .document-date {
            font-size: 12px;
            color: #7f8c8d;
        }

        /* Document Status */
        .document-status-cancelled {
            background-color: #fdf2f2;
            border: 1px solid #cc0000;
            padding: 8px;
            margin: 10px 0;
            border-radius: 4px;
            text-align: center;
        }

        .document-status-cancelled h3 {
            color: #dc2626;
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }

        .document-status-draft {
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
            padding: 8px;
            margin: 10px 0;
            border-radius: 4px;
            text-align: center;
        }

        .document-status-draft h3 {
            color: #92400e;
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }

        /* Section Titles */
        .section-title {
            color: #2c3e50;
            font-size: 14px;
            font-weight: 600;
            margin: 0 0 6px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Customer and Invoice Details */
        .customer-invoice-section {
            margin-bottom: 12px;
            overflow: hidden;
        }

        .customer-invoice-section .col-xs-6 {
            width: 48%;
            float: left;
            box-sizing: border-box;
        }

        .customer-invoice-section .col-xs-6:first-child {
            padding-right: 15px;
            padding-left: 0;
        }

        .customer-invoice-section .col-xs-6:last-child {
            padding-left: 15px;
            padding-right: 0;
        }

        .customer-details, .invoice-details {
            padding: 0;
        }

        .customer-name {
            color: #2c3e50;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
            display: block;
        }

        .customer-info {
            font-size: 12px;
            line-height: 1.4;
            color: #555;
        }

        .invoice-info {
            font-size: 12px;
        }

        .info-row {
            margin-bottom: 4px;
            padding: 2px 0;
            overflow: hidden;
        }

        .info-row .label {
            color: #2c3e50;
            font-weight: 500;
            float: left;
            width: 40%;
            text-align: left;
        }

        .info-row .value {
            color: #2c3e50;
            font-weight: 500;
            float: right;
            width: 60%;
            text-align: right;
        }

        /* Clear floats */
        .info-row::after {
            content: "";
            display: table;
            clear: both;
        }

        /* Items Table */
        .items-section {
            margin-bottom: 4px;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 4px;
            border: 1px solid #7f8c8d;
            table-layout: fixed;
        }

        /* Adaptive Column Width System - Supports 3-7 columns */
        
        /* 3-Column Layout (e.g., Deductions, Simple Lists) */
        .items-table.cols-3 th:nth-child(1),
        .items-table.cols-3 td:nth-child(1) { width: 25%; }  /* Conta/Label */
        .items-table.cols-3 th:nth-child(2),
        .items-table.cols-3 td:nth-child(2) { width: 50%; }  /* Descrição */
        .items-table.cols-3 th:nth-child(3),
        .items-table.cols-3 td:nth-child(3) { width: 25%; }  /* Valor */
        
        /* 4-Column Layout (e.g., Material Request, Simple Stock Entry) */
        .items-table.cols-4 th:nth-child(1),
        .items-table.cols-4 td:nth-child(1) { width: 6%; }   /* Sr */
        .items-table.cols-4 th:nth-child(2),
        .items-table.cols-4 td:nth-child(2) { width: 45%; }  /* Item/Descrição */
        .items-table.cols-4 th:nth-child(3),
        .items-table.cols-4 td:nth-child(3) { width: 15%; }  /* Qtd */
        .items-table.cols-4 th:nth-child(4),
        .items-table.cols-4 td:nth-child(4) { width: 34%; }  /* U.M./Data/Valor */
        
        /* 5-Column Layout (e.g., Stock Entry with Warehouse) */
        .items-table.cols-5 th:nth-child(1),
        .items-table.cols-5 td:nth-child(1) { width: 5%; }   /* Sr */
        .items-table.cols-5 th:nth-child(2),
        .items-table.cols-5 td:nth-child(2) { width: 35%; }  /* Item/Descrição */
        .items-table.cols-5 th:nth-child(3),
        .items-table.cols-5 td:nth-child(3) { width: 12%; }  /* Qtd */
        .items-table.cols-5 th:nth-child(4),
        .items-table.cols-5 td:nth-child(4) { width: 15%; }  /* U.M./Armazém */
        .items-table.cols-5 th:nth-child(5),
        .items-table.cols-5 td:nth-child(5) { width: 33%; }  /* Valor */
        
        /* 6-Column Layout (e.g., Payment Entry References) */
        .items-table.cols-6 th:nth-child(1),
        .items-table.cols-6 td:nth-child(1) { width: 12%; }  /* Tipo */
        .items-table.cols-6 th:nth-child(2),
        .items-table.cols-6 td:nth-child(2) { width: 17%; }  /* Documento */
        .items-table.cols-6 th:nth-child(3),
        .items-table.cols-6 td:nth-child(3) { width: 12%; }  /* Data */
        .items-table.cols-6 th:nth-child(4),
        .items-table.cols-6 td:nth-child(4) { width: 19%; }  /* Total da Fatura */
        .items-table.cols-6 th:nth-child(5),
        .items-table.cols-6 td:nth-child(5) { width: 19%; }  /* Saldo Antes */
        .items-table.cols-6 th:nth-child(6),
        .items-table.cols-6 td:nth-child(6) { width: 22%; }  /* Saldo Após */
        
        /* 7-Column Layout (e.g., Sales Invoice with IVA) */
        .items-table.cols-7 th:nth-child(1),
        .items-table.cols-7 td:nth-child(1) { width: 4%; }   /* Sr */
        .items-table.cols-7 th:nth-child(2),
        .items-table.cols-7 td:nth-child(2) { width: 31%; }  /* Descrição */
        .items-table.cols-7 th:nth-child(3),
        .items-table.cols-7 td:nth-child(3) { width: 8%; }  /* Qtd */
        .items-table.cols-7 th:nth-child(4),
        .items-table.cols-7 td:nth-child(4) { width: 10%; }   /* U.M. */
        .items-table.cols-7 th:nth-child(5),
        .items-table.cols-7 td:nth-child(5) { width: 17%; }  /* Preço */
        .items-table.cols-7 th:nth-child(6),
        .items-table.cols-7 td:nth-child(6) { width: 9%; }   /* IVA (%) */
        .items-table.cols-7 th:nth-child(7),
        .items-table.cols-7 td:nth-child(7) { width: 21%; }  /* Valor */
        
        /* Default fallback for tables without explicit column count */
        .items-table th:nth-child(1),
        .items-table td:nth-child(1) { width: 4%; }
        .items-table th:nth-child(2),
        .items-table td:nth-child(2) { width: 31%; }
        .items-table th:nth-child(3),
        .items-table td:nth-child(3) { width: 8%; }
        .items-table th:nth-child(4),
        .items-table td:nth-child(4) { width: 10%; }
        .items-table th:nth-child(5),
        .items-table td:nth-child(5) { width: 17%; }
        .items-table th:nth-child(6),
        .items-table td:nth-child(6) { width: 9%; }
        .items-table th:nth-child(7),
        .items-table td:nth-child(7) { width: 21%; }

        .items-table th {
            background-color: #f8f9fa;
            color: #2c3e50;
            padding: 4px 3px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #7f8c8d;
            text-align: left;
        }

        .items-table th.text-center {
            text-align: center;
        }

        .items-table th.text-right {
            text-align: right;
        }

        /* Enhanced column alignment for better readability */
        .items-table td.text-center {
            text-align: center;
        }

        .items-table td.text-right {
            text-align: right;
        }

        .items-table td.text-left {
            text-align: left;
        }

        .items-table td {
            padding: 3px 3px;
            border-bottom: 1px solid #999999;
            vertical-align: top;
            font-size: 12px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        .items-table tbody tr:last-child td {
            border-bottom: none;
        }

        .items-table tbody tr:nth-child(even) {
            background-color: #fafafa;
        }

        .item-description {
            font-size: 12px;
            line-height: 1.4;
        }

        /* Totals Section */
        .totals-section {
            margin-bottom: 4px;
            overflow: hidden;
        }

        .totals-section .col-xs-6 {
            float: left;
            box-sizing: border-box;
        }

        .totals-section .col-xs-6:first-child {
            width: 45%;
            padding-right: 15px;
            padding-left: 0;
        }

        .totals-section .col-xs-6:last-child {
            width: 55%;
            padding-left: 15px;
            padding-right: 0;
        }

        .amount-in-words, .terms-section {
            padding: 8px 0;
            margin-bottom: 4px;
        }

        .amount-in-words h5, .terms-section h5 {
            color: #2c3e50;
            margin: 0 0 6px 0;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .amount-in-words p, .terms-section p {
            margin: 0;
            font-size: 12px;
            line-height: 1.4;
            color: #555;
        }

        .totals-table {
            padding: 0;
        }

        .totals-row {
            margin-bottom: 3px;
            padding: 3px 0;
            border-bottom: 1px solid #999999;
            overflow: hidden;
        }

        .totals-row:last-child {
            border-bottom: none;
        }

        .totals-label {
            color: #555;
            font-size: 12px;
            font-weight: 500;
            float: left;
            width: 52%;
        }

        .totals-value {
            color: #2c3e50;
            font-size: 12px;
            font-weight: 500;
            float: right;
            width: 48%;
            text-align: right;
        }

        .totals-row::after {
            content: "";
            display: table;
            clear: both;
        }

        .totals-row.grand-total {
            border-top: 2px solid #2c3e50;
            margin-top: 4px;
            padding-top: 6px;
            font-weight: 600;
            font-size: 14px;
        }

        .totals-row.grand-total .totals-label,
        .totals-row.grand-total .totals-value {
            font-weight: 600;
            font-size: 14px;
        }

        /* Payment Section */
        .payment-section {
            margin-bottom: 4px;
        }

        .payment-info {
            background-color: #fef3c7;
            border: 1px solid #cc6600;
            padding: 8px;
            border-radius: 4px;
        }

        .payment-info h5 {
            color: #92400e;
            margin: 0 0 6px 0;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .payment-info p {
            margin: 2px 0;
            font-size: 12px;
            color: #92400e;
        }

        /* QR Code Section */
        .qr-section {
            margin-top: 16px;
            margin-bottom: 4px;
        }

        .qr-code-container {
            text-align: center;
            padding: 8px 0;
        }

        .qr-code-img {
            max-width: 80px;
            max-height: 80px;
            width: auto;
            height: auto;
            border: 1px solid #7f8c8d;
            border-radius: 4px;
        }

        .qr-label {
            color: #7f8c8d;
            font-size: 10px;
            margin: 6px 0 0 0;
            font-style: italic;
        }

        /* Utility Classes */
        .text-center { text-align: center; }
        .text-left   { text-align: left; }
        .text-right  { text-align: right; }
        .text-uppercase { text-transform: uppercase; }

        .page-break { page-break-inside: avoid; }

        .row {
            overflow: hidden;
            margin: 0;
            display: block;
        }

        /* Bootstrap Grid System - Web Display */
        .col-xs-6 {
            width: 48%;
            float: left;
            box-sizing: border-box;
            padding-left: 8px;
            padding-right: 8px;
        }
        
        .col-xs-6:first-child {
            padding-left: 0;
            padding-right: 15px;
        }
        
        .col-xs-6:last-child {
            padding-right: 0;
            padding-left: 15px;
        }

        /* Ensure consistent spacing */
        .customer-details {
            padding-right: 15px;
        }

        .invoice-details {
            padding-left: 15px;
        }

        /* Fix for potential text overflow */
        .customer-name {
            word-wrap: break-word;
            overflow-wrap: break-word;
        }

        /* Ensure proper alignment */
        .text-right {
            text-align: right !important;
        }

        .text-left {
            text-align: left !important;
        }

        .text-center {
            text-align: center !important;
        }

        /* Print Specific Styles */
        @media print {
            .print-format { font-size: 11px; }
            .document-title { font-size: 20px; }
            .items-table th, .items-table td { padding: 3px 2px; }
            .items-table th { font-size: 10px; }
            .items-table td { font-size: 11px; }
            
            /* Adaptive Column Width System for Print - Supports 3-7 columns */
            
            /* 3-Column Layout for Print */
            .items-table.cols-3 th:nth-child(1),
            .items-table.cols-3 td:nth-child(1) { width: 25% !important; }
            .items-table.cols-3 th:nth-child(2),
            .items-table.cols-3 td:nth-child(2) { width: 50% !important; }
            .items-table.cols-3 th:nth-child(3),
            .items-table.cols-3 td:nth-child(3) { width: 25% !important; }
            
            /* 4-Column Layout for Print */
            .items-table.cols-4 th:nth-child(1),
            .items-table.cols-4 td:nth-child(1) { width: 6% !important; }
            .items-table.cols-4 th:nth-child(2),
            .items-table.cols-4 td:nth-child(2) { width: 45% !important; }
            .items-table.cols-4 th:nth-child(3),
            .items-table.cols-4 td:nth-child(3) { width: 15% !important; }
            .items-table.cols-4 th:nth-child(4),
            .items-table.cols-4 td:nth-child(4) { width: 34% !important; }
            
            /* 5-Column Layout for Print */
            .items-table.cols-5 th:nth-child(1),
            .items-table.cols-5 td:nth-child(1) { width: 5% !important; }
            .items-table.cols-5 th:nth-child(2),
            .items-table.cols-5 td:nth-child(2) { width: 35% !important; }
            .items-table.cols-5 th:nth-child(3),
            .items-table.cols-5 td:nth-child(3) { width: 12% !important; }
            .items-table.cols-5 th:nth-child(4),
            .items-table.cols-5 td:nth-child(4) { width: 15% !important; }
            .items-table.cols-5 th:nth-child(5),
            .items-table.cols-5 td:nth-child(5) { width: 33% !important; }
            
            /* 6-Column Layout for Print */
            .items-table.cols-6 th:nth-child(1),
            .items-table.cols-6 td:nth-child(1) { width: 12% !important; }
            .items-table.cols-6 th:nth-child(2),
            .items-table.cols-6 td:nth-child(2) { width: 15% !important; }
            .items-table.cols-6 th:nth-child(3),
            .items-table.cols-6 td:nth-child(3) { width: 12% !important; }
            .items-table.cols-6 th:nth-child(4),
            .items-table.cols-6 td:nth-child(4) { width: 19% !important; }
            .items-table.cols-6 th:nth-child(5),
            .items-table.cols-6 td:nth-child(5) { width: 19% !important; }
            .items-table.cols-6 th:nth-child(6),
            .items-table.cols-6 td:nth-child(6) { width: 24% !important; }
            
            /* 7-Column Layout for Print */
            .items-table.cols-7 th:nth-child(1),
            .items-table.cols-7 td:nth-child(1) { width: 4% !important; }
            .items-table.cols-7 th:nth-child(2),
            .items-table.cols-7 td:nth-child(2) { width: 31% !important; }
            .items-table.cols-7 th:nth-child(3),
            .items-table.cols-7 td:nth-child(3) { width: 8% !important; }
            .items-table.cols-7 th:nth-child(4),
            .items-table.cols-7 td:nth-child(4) { width: 10% !important; }
            .items-table.cols-7 th:nth-child(5),
            .items-table.cols-7 td:nth-child(5) { width: 17% !important; }
            .items-table.cols-7 th:nth-child(6),
            .items-table.cols-7 td:nth-child(6) { width: 9% !important; }
            .items-table.cols-7 th:nth-child(7),
            .items-table.cols-7 td:nth-child(7) { width: 21% !important; }
            
            /* Default fallback for print */
            .items-table th:nth-child(1),
            .items-table td:nth-child(1) { width: 4% !important; }
            .items-table th:nth-child(2),
            .items-table td:nth-child(2) { width: 31% !important; }
            .items-table th:nth-child(3),
            .items-table td:nth-child(3) { width: 8% !important; }
            .items-table th:nth-child(4),
            .items-table td:nth-child(4) { width: 10% !important; }
            .items-table th:nth-child(5),
            .items-table td:nth-child(5) { width: 17% !important; }
            .items-table th:nth-child(6),
            .items-table td:nth-child(6) { width: 9% !important; }
            .items-table th:nth-child(7),
            .items-table td:nth-child(7) { width: 21% !important; }
            
            .totals-row { padding: 2px 0; }
            .payment-info { padding: 6px; }
            
            /* Document status print adjustments */
            .document-status-draft,
            .document-status-cancelled {
                margin: 8px 0 !important;
                padding: 6px !important;
            }
            
            .document-status-draft h3,
            .document-status-cancelled h3 {
                font-size: 14px !important;
            }
            
            /* QR Code print adjustments */
            .qr-code-img {
                max-width: 70px !important;
                max-height: 70px !important;
            }
        
            .col-xs-6 {
                width: 50% !important;
                float: left !important;
                box-sizing: border-box !important;
                padding-left: 8px !important;
                padding-right: 8px !important;
            }
            
            .col-xs-6:first-child {
                padding-left: 0 !important;
            }
            
            .col-xs-6:last-child {
                padding-right: 0 !important;
            }
            
            /* Clear floats for proper layout */
            .row::after {
                content: "";
                display: table;
                clear: both;
            }

            /* Remove any inherited borders from form elements */
            .info-row .label,
            .info-row .value,
            .customer-info,
            .invoice-info {
                border: none !important;
                background: none !important;
                box-shadow: none !important;
            }
            
            /* Ensure proper spacing */
            .customer-invoice-section {
                margin-bottom: 15px;
                overflow: hidden;
            }

            .totals-section {
                overflow: hidden;
            }
            
            .section-title {
                margin-bottom: 8px;
            }

            /* Ensure proper grid layout in print */
            .customer-invoice-section .col-xs-6 {
                width: 48% !important;
                float: left !important;
                box-sizing: border-box !important;
            }

            .customer-invoice-section .col-xs-6:first-child {
                padding-right: 15px !important;
                padding-left: 0 !important;
            }

            .customer-invoice-section .col-xs-6:last-child {
                padding-left: 15px !important;
                padding-right: 0 !important;
            }

            /* Totals section specific layout for print */
            .totals-section .col-xs-6:first-child {
                width: 45% !important;
                padding-right: 15px !important;
                padding-left: 0 !important;
            }

            .totals-section .col-xs-6:last-child {
                width: 55% !important;
                padding-left: 15px !important;
                padding-right: 0 !important;
            }
        }
    """

    def get_common_header_macro(self, document_title):
        return """
        {%- macro add_header(page_num, max_pages, doc, letter_head, no_letterhead, footer, print_settings=none, print_heading_template=none) -%}
            {% if letter_head and not no_letterhead %}
                <div class="letter-head">{{ letter_head }}</div>
            {% endif %}
            <div class="document-header">
                <div class="row">
                    <div class="col-xs-8">
                        <h1 class="document-title">""" + document_title + """</h1>
                    </div>
                    <div class="col-xs-4 text-right">
                        <div class="document-number"><strong>{{ doc.name }}</strong></div>
                        <div class="document-date">
                            {% set __dt = (doc.posting_date and (doc.posting_date ~ " " ~ (doc.posting_time or "00:00:00")))
                                or (doc.transaction_date and (doc.transaction_date ~ " 00:00:00"))
                                or doc.creation %}
                            {{ frappe.utils.format_datetime(__dt) }}
                        </div>
                    </div>
                </div>
            </div>
            {%- if doc.meta.is_submittable -%}
                {%- if doc.docstatus==0 -%}
                <div class="text-center document-status-draft">
                    <h3>{{ _("RASCUNHO") }}</h3>
                </div>
                {%- elif doc.docstatus==2 -%}
                <div class="text-center document-status-cancelled">
                    <h3>{{ _("CANCELADA") }}</h3>
                </div>
                {%- endif -%}
            {%- endif -%}
        {%- endmacro -%}
    """


    def get_common_footer_macro(self):
        """Common footer macro for all documents"""
        return """
        {%- macro add_footer(page_num, max_pages, doc, letter_head, no_letterhead, footer, print_settings=none) -%}
            {% if print_settings and print_settings.repeat_header_footer %}
            <div id="footer-html" class="visible-pdf">
                {% if not no_letterhead and footer %}
                <div class="letter-head-footer">
                    {{ footer }}
                </div>
                {% endif %}
            </div>
            {% endif %}
        {%- endmacro -%}
    """

    def get_qr_code_section(self):
        """Common QR code section for all documents"""
        return """
        <!-- QR Code Section for Digital Compliance -->
        <div class="row qr-section">
            <div class="col-xs-12 text-center">
                {% set qr_code_img = get_qr_image(doc.doctype, doc.name) %}
                {% if qr_code_img and qr_code_img.strip() %}
                <div class="qr-code-container">
                    <img src="data:image/png;base64,{{ qr_code_img }}" alt="QR Code" class="qr-code-img" />
                    <p class="qr-label">{{ _("Escaneie o QR para verificar a autenticidade") }}</p>
                </div>
                {% endif %}
            </div>
        </div>
    """

    def get_customer_details_section(self, customer_field="customer", customer_name_field="customer_name"):
        """Common customer details section"""
        return """
            <!-- Customer Details Section -->
            <div class="row customer-invoice-section">
                <div class="col-xs-6 customer-details">
                    <h4 class="section-title">{{ _("Facturar Para") }}</h4>
                    <div class="customer-info">
                        <div class="customer-name">{{ doc.""" + customer_name_field + """ or doc.""" + customer_field + """ }}</div>
                        {% if doc.tax_id %}
                            <div><strong>{{ _("NUIT") }}:</strong> {{ doc.tax_id }}</div>
                        {% endif %}
                        {% if not doc.tax_id and doc.customer %}
                            {% set __cust_nuit = frappe.db.get_value('Customer', doc.customer, 'tax_id') %}
                            {% if __cust_nuit %}
                                <div><strong>{{ _("NUIT") }}:</strong> {{ __cust_nuit }}</div>
                            {% endif %}
                        {% endif %}
                        {% if doc.address_display %}
                            <div>{{ doc.address_display }}</div>
                        {% endif %}
                        {% if doc.contact_display %}
                            <div><strong>{{ _("Contacto") }}:</strong> {{ doc.contact_display }}</div>
                        {% endif %}
                        {% if doc.contact_mobile %}
                            <div><strong>{{ _("Telemóvel") }}:</strong> {{ doc.contact_mobile }}</div>
                        {% endif %}
                    </div>
                </div>
                
                <div class="col-xs-6 invoice-details">
                    <h4 class="section-title">{{ _("Detalhes do Documento") }}</h4>
                    <div class="invoice-info">
                        {% if doc.due_date %}
                        <div class="info-row">
                            <span class="label">{{ _("Vencimento") }}:</span>
                            <span class="value">{{ frappe.utils.format_date(doc.due_date) }}</span>
                        </div>
                        {% endif %}
                        {% if doc.po_no %}
                        <div class="info-row">
                            <span class="label">{{ _("Nº Encomenda") }}:</span>
                            <span class="value">{{ doc.po_no }}</span>
                        </div>
                        {% endif %}
                        {% if doc.currency %}
                        <div class="info-row">
                            <span class="label">{{ _("Moeda") }}:</span>
                            <span class="value">{{ doc.currency }}</span>
                        </div>
                        {% endif %}
                        {% if doc.currency and doc.company_currency and doc.currency != doc.company_currency and doc.conversion_rate %}
                        <div class="info-row">
                            <span class="label">{{ _("Taxa de câmbio") }}:</span>
                            <span class="value">1 {{ doc.currency }} = {{ doc.conversion_rate }} {{ doc.company_currency }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        """

    def get_item_tax_rate_jinja(self):
        """Return Jinja template code to calculate item tax rate
        Priority: item.item_tax_template -> doc.taxes
        """
        return """
            {% if item.item_tax_template %}
                {% set tax_template = frappe.get_doc('Item Tax Template', item.item_tax_template) %}
                {% if tax_template.taxes and tax_template.taxes|first %}
                    {% set first_tax_detail = tax_template.taxes|first %}
                    {% if first_tax_detail.tax_rate and first_tax_detail.tax_rate > 0 %}
                        {{ first_tax_detail.tax_rate|int }}%
                    {% else %}
                        {% if doc.taxes and doc.taxes|first %}
                            {% set first_tax = doc.taxes|first %}
                            {% if first_tax.rate %}
                                {{ first_tax.rate|int }}%
                            {% else %}
                                0%
                            {% endif %}
                        {% else %}
                            0%
                        {% endif %}
                    {% endif %}
                {% else %}
                    {% if doc.taxes and doc.taxes|first %}
                        {% set first_tax = doc.taxes|first %}
                        {% if first_tax.rate %}
                            {{ first_tax.rate|int }}%
                        {% else %}
                            0%
                        {% endif %}
                    {% else %}
                        0%
                    {% endif %}
                {% endif %}
            {% else %}
                {% if doc.taxes and doc.taxes|first %}
                    {% set first_tax = doc.taxes|first %}
                    {% if first_tax.rate %}
                        {{ first_tax.rate|int }}%
                    {% else %}
                        0%
                    {% endif %}
                {% else %}
                    0%
                {% endif %}
            {% endif %}
        """

    def get_items_table_section(self, items_field="items", custom_columns=None):
        """Common items table section with adaptive column width support"""
        if custom_columns is None:
            custom_columns = [
                ("Sr", "text-center", "{{ loop.index }}"),
                ("Descrição", "text-left", """
                    <strong>{{ item.item_code }}</strong><br>
                    {{ item.item_name }}
                    {% if item.description and item.description != item.item_name %}
                        <br><em>{{ item.description }}</em>
                    {% endif %}
                    {% if item.serial_no %}
                        <br><small><strong>{{ _("Nº de Série") }}:</strong> {{ item.serial_no }}</small>
                    {% endif %}
                """),
                ("Qtd", "text-center", "{{ item.get_formatted('qty', doc) }}"),
                ("U.M.", "text-center", "{{ item.get_formatted('uom', doc) }}"),
                ("Preço", "text-right", "{{ item.get_formatted('net_rate', doc) }}"),
                ("IVA %", "text-center", self.get_item_tax_rate_jinja()),
                ("Total Ilíquido", "text-right", "{{ item.get_formatted('net_amount', doc) }}")
            ]
        
        # Determine column count and CSS class
        column_count = len(custom_columns)
        table_class = ""
        if column_count == 3:
            table_class = "items-table cols-3"
        elif column_count == 4:
            table_class = "items-table cols-4"
        elif column_count == 5:
            table_class = "items-table cols-5"
        elif column_count == 6:
            table_class = "items-table cols-6"
        elif column_count == 7:
            table_class = "items-table cols-7"
        else:
            # Fallback for other column counts
            table_class = "items-table"
        
        header_html = ""
        for col_name, col_class, _ in custom_columns:
            header_html += '<th class="' + col_class + '">{{ _("' + col_name + '") }}</th>\n                    '
        
        body_html = ""
        for col_name, col_class, col_template in custom_columns:
            body_html += '<td class="' + col_class + '">' + col_template + '</td>\n                    '
        
        return """
            <!-- Items Table Section -->
            <div class="items-section">
                <h4 class="section-title">{{ _("Artigos") }}</h4>
                <table class=\"""" + table_class + """\">
                    <thead>
                        <tr>
                            """ + header_html + """
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in doc.""" + items_field + """ %}
                        <tr>
                            """ + body_html + """
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        """

    def get_totals_section(self, totals_fields=None):
        """Common totals section (safe on doctypes without those fields)
        
        Args:
            totals_fields: List of tuples with (field_name, label) or (field_name, label, always_show)
                          where always_show=True means the field will be displayed even if zero
        """
        if totals_fields is None:
            totals_fields = [
                ("net_total", "Sub Total"),
                ("grand_total", "Total Geral", True)
            ]

        rows = []
        for field_data in totals_fields:
            if len(field_data) == 2:
                field, label = field_data
                always_show = False
            else:
                field, label, always_show = field_data
            
            row_class = "totals-row grand-total" if field == "grand_total" else "totals-row"
            
            if field == "tax_amount":
                rows.append("""
                    {% for tax in doc.taxes %}
                        {% if tax.tax_amount or """ + str(always_show).lower() + """ %}
                        <div class="totals-row">
                            <span class="totals-label">{{ _(tax.description) }}:</span>
                            <span class="totals-value">{{ tax.get_formatted("tax_amount", doc) }}</span>
                        </div>
                        {% endif %}
                    {% endfor %}
                """)
                continue

            if always_show:
                condition = f"doc.get('{field}') is not none"
            else:
                condition = f"doc.get('{field}')"

            rows.append(f"""
                    {{% set __val = doc.get("{field}") %}}
                    {{% if {condition} %}}
                    <div class="{row_class}">
                        <span class="totals-label">{label}:</span>
                        <span class="totals-value">{{{{ doc.get_formatted("{field}", doc) }}}}</span>
                    </div>
                    {{% endif %}}
            """)

        totals_html = "".join(rows)

        return f"""
            <!-- Totals Section -->
            <div class="row totals-section">
                <div class="col-xs-6">

                    {{% if doc.get("terms") %}}
                    <div class="terms-section">
                        <h5>{{{{ _("Termos e Condições") }}}}</h5>
                        <p>{{{{ doc.terms }}}}</p>
                    </div>
                    {{% endif %}}
                </div>
                <div class="col-xs-6">
                    <div class="totals-table">
                        {totals_html}
                    </div>
                </div>
            </div>
        """

    def get_signatures_section(self):
        """Common signatures section"""
        return """
            <!-- Signatures Section -->
            <div class="row" style="margin-top: 8px;">
                <div class="col-xs-6 text-left">
                    <div style="border-top: 1px solid #7f8c8d; padding-top: 6px;">
                        {{ _("Emitido por") }}:
                        {% if doc.owner %}
                            {{ doc.owner }}
                        {% endif %}
                    </div>
                </div>
                <div class="col-xs-6 text-right">
                    <div style="border-top: 1px solid #7f8c8d; padding-top: 6px;">{{ _("Recebido por") }}: ____________________</div>
                </div>
            </div>
        """