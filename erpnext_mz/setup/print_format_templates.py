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
            border-bottom: 1px solid #e5e5e5;
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
            border: 1px solid #fecaca;
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

        /* Section Titles */
        .section-title {
            color: #2c3e50;
            font-size: 14px;
            font-weight: 600;
            margin: 0 0 6px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #e5e5e5;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Customer and Invoice Details */
        .customer-invoice-section {
            margin-bottom: 12px;
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
            color: #7f8c8d;
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
            margin-bottom: 12px;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
            border: 1px solid #e5e5e5;
        }

        .items-table th {
            background-color: #f8f9fa;
            color: #2c3e50;
            padding: 8px 6px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #e5e5e5;
            text-align: left;
        }

        .items-table th.text-center {
            text-align: center;
        }

        .items-table th.text-right {
            text-align: right;
        }

        .items-table td {
            padding: 6px 6px;
            border-bottom: 1px solid #f0f0f0;
            vertical-align: top;
            font-size: 12px;
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
            margin-bottom: 12px;
        }

        .amount-in-words, .terms-section {
            padding: 8px 0;
            margin-bottom: 8px;
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
            border-bottom: 1px solid #f0f0f0;
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
            width: 60%;
        }

        .totals-value {
            color: #2c3e50;
            font-size: 12px;
            font-weight: 500;
            float: right;
            width: 40%;
            text-align: right;
        }

        .totals-row::after {
            content: "";
            display: table;
            clear: both;
        }

        .totals-row.grand-total {
            border-top: 2px solid #2c3e50;
            margin-top: 6px;
            padding-top: 8px;
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
            margin-bottom: 12px;
        }

        .payment-info {
            background-color: #fef3c7;
            border: 1px solid #f59e0b;
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
            margin-top: 20px;
            margin-bottom: 8px;
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
            border: 1px solid #e5e5e5;
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
            .items-table th, .items-table td { padding: 6px 4px; }
            .totals-row { padding: 2px 0; }
            .payment-info { padding: 6px; }
            
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
            }
            
            .section-title {
                margin-bottom: 8px;
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
                        <div class="document-date">{{ frappe.utils.format_date(doc.posting_date or doc.transaction_date or doc.creation) }}</div>
                    </div>
                </div>
            </div>
            {%- if doc.meta.is_submittable and doc.docstatus==2 -%}
            <div class="text-center document-status-cancelled">
                <h3>{{ _("CANCELADA") }}</h3>
            </div>
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
                {% if qr_code_img %}
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
                    </div>
                </div>
            </div>
        """

    def get_items_table_section(self, items_field="items", custom_columns=None):
        """Common items table section"""
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
                ("Valor", "text-right", "{{ item.get_formatted('net_amount', doc) }}")
            ]
        
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
                <table class="items-table">
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
        """Common totals section (safe on doctypes without those fields)"""
        if totals_fields is None:
            totals_fields = [
                ("net_total", "Sub Total"),
                ("grand_total", "Total Geral")
            ]

        rows = []
        for field, label in totals_fields:
            row_class = "totals-row grand-total" if field == "grand_total" else "totals-row"
            # Render only if the value is present (None => likely missing field on this doctype)
            if field == "tax_amount":
                rows.append("""
                    {% for tax in doc.taxes %}
                        {% if tax.tax_amount %}
                        <div class="totals-row">
                            <span class="totals-label">{{ _(tax.description) }}:</span>
                            <span class="totals-value">{{ tax.get_formatted("tax_amount", doc) }}</span>
                        </div>
                        {% endif %}
                    {% endfor %}
                """)
                continue

            rows.append(f"""
                    {{% set __val = doc.get("{field}") %}}
                    {{% if __val %}}
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
                    {{% if doc.get("in_words") %}}
                    <div class="amount-in-words">
                        <h5>{{{{ _("Valor por Extenso") }}}}</h5>
                        <p><strong>{{{{ doc.in_words }}}}</strong></p>
                    </div>
                    {{% endif %}}
                    
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
