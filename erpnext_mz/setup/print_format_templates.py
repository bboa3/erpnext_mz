#!/usr/bin/env python3
"""
Mozambique Print Format Templates - Fixed Version

This module provides a comprehensive base system for creating professional
print formats for all business documents in Mozambique ERPNext implementation.

FIXES APPLIED:
- Removed flexbox layouts for PDF compatibility
- Simplified Bootstrap grid usage
- Fixed border rendering issues
- Improved WeasyPrint compatibility
- Enhanced CSS consistency
"""

import frappe
from frappe import _


class PrintFormatTemplate:
    """Base class for all print format templates - PDF OPTIMIZED"""
    
    def __init__(self, doc_type, format_name, module="ERPNext MZ"):
        self.doc_type = doc_type
        self.format_name = format_name
        self.module = module
        self.base_css = self._get_base_css()
    
    def create_print_format(self):
        """Create or update the print format document"""
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
        """Base CSS styles optimized for PDF rendering with WeasyPrint"""
        return """
        /* Mozambique Print Format Base Styles - PDF OPTIMIZED */

        .print-format {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            background: #fff;
            width: 100%;
            max-width: 100%;
        }

        /* Document Header - Fixed Layout */
        .document-header {
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 10px;
            margin-bottom: 15px;
            overflow: hidden;
        }

        .document-title {
            color: #2c3e50;
            font-size: 24px;
            font-weight: 600;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
            float: left;
            width: 60%;
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
            float: right;
            width: 35%;
            text-align: right;
        }

        .document-date {
            font-size: 12px;
            color: #7f8c8d;
            float: right;
            width: 35%;
            text-align: right;
            clear: right;
        }

        /* Clear floats */
        .document-header::after {
            content: "";
            display: table;
            clear: both;
        }

        /* Document Status */
        .document-status-cancelled {
            background-color: #fdf2f2;
            border: 2px solid #fecaca;
            padding: 10px;
            margin: 15px 0;
            border-radius: 4px;
            text-align: center;
            clear: both;
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
            margin: 0 0 8px 0;
            padding-bottom: 4px;
            border-bottom: 1px solid #e5e5e5;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Customer and Invoice Details - Fixed Layout */
        .customer-invoice-section {
            margin-bottom: 15px;
            overflow: hidden;
        }

        .customer-details, .invoice-details {
            padding: 0;
            float: left;
            width: 48%;
            margin-right: 4%;
        }

        .invoice-details {
            margin-right: 0;
        }

        .customer-name {
            color: #2c3e50;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
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

        /* Info rows - Fixed layout instead of flexbox */
        .info-row {
            margin-bottom: 4px;
            padding: 3px 0;
            overflow: hidden;
        }

        .info-row .label {
            color: #7f8c8d;
            font-weight: 500;
            float: left;
            width: 40%;
        }

        .info-row .value {
            color: #2c3e50;
            font-weight: 500;
            float: right;
            width: 55%;
            text-align: right;
        }

        /* Clear floats for info rows */
        .info-row::after {
            content: "";
            display: table;
            clear: both;
        }

        /* Items Table - Simplified */
        .items-section {
            margin-bottom: 15px;
            clear: both;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            border: 1px solid #2c3e50;
        }

        .items-table th {
            background-color: #f8f9fa;
            color: #2c3e50;
            padding: 8px 6px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #2c3e50;
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
            border-bottom: 1px solid #e5e5e5;
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

        /* Totals Section - Fixed Layout */
        .totals-section {
            margin-bottom: 15px;
            overflow: hidden;
        }

        .amount-in-words, .terms-section {
            padding: 8px 0;
            margin-bottom: 8px;
            float: left;
            width: 48%;
            margin-right: 4%;
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
            float: right;
            width: 45%;
        }

        /* Totals rows - Fixed layout instead of flexbox */
        .totals-row {
            padding: 4px 0;
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
            width: 35%;
            text-align: right;
        }

        .totals-row.grand-total {
            border-top: 2px solid #2c3e50;
            margin-top: 8px;
            padding-top: 8px;
            font-weight: 600;
            font-size: 14px;
        }

        .totals-row.grand-total .totals-label,
        .totals-row.grand-total .totals-value {
            font-weight: 600;
            font-size: 14px;
        }

        /* Clear floats for totals */
        .totals-row::after {
            content: "";
            display: table;
            clear: both;
        }

        /* Payment Section */
        .payment-section {
            margin-bottom: 15px;
            clear: both;
        }

        .payment-info {
            background-color: #fef3c7;
            border: 2px solid #f59e0b;
            padding: 10px;
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
            margin-bottom: 10px;
            clear: both;
        }

        .qr-code-container {
            text-align: center;
            padding: 8px 0;
        }

        .qr-code-img {
            max-width: 100px;
            max-height: 100px;
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

        .page-break { 
            page-break-inside: avoid; 
            clear: both;
        }

        /* Print Specific Styles - Enhanced for WeasyPrint */
        @media print {
            .print-format { 
                font-size: 11px; 
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }
            .document-title { font-size: 20px; }
            .items-table th, .items-table td { padding: 6px 4px; }
            .totals-row { padding: 3px 0; }
            .payment-info { padding: 8px; }
            
            /* Ensure proper page breaks */
            .page-break {
                page-break-before: always;
            }
            
            /* Fix for WeasyPrint float issues */
            .customer-details, .invoice-details,
            .amount-in-words, .terms-section, .totals-table {
                float: none;
                width: 100%;
                margin-right: 0;
                margin-bottom: 10px;
            }
            
            .totals-table {
                width: 100%;
            }
        }

        /* Screen specific styles */
        @media screen {
            .print-format {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
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
                <h1 class="document-title">""" + document_title + """</h1>
                <div class="document-number"><strong>{{ doc.name }}</strong></div>
                <div class="document-date">{{ frappe.utils.format_date(doc.posting_date or doc.transaction_date or doc.creation) }}</div>
            </div>
            {%- if doc.meta.is_submittable and doc.docstatus==2 -%}
            <div class="document-status-cancelled">
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
                <p class="text-center small page-number visible-pdf">
                    {{ _("Página") }} <span class="page"></span> {{ _("de") }} <span class="topage"></span>
                </p>
            </div>
            {% endif %}
        {%- endmacro -%}
    """

    def get_qr_code_section(self):
        """Common QR code section for all documents"""
        return """
        <!-- QR Code Section for Digital Compliance -->
        <div class="qr-section">
            {% set qr_code_img = get_qr_image(doc.doctype, doc.name) %}
            {% if qr_code_img %}
            <div class="qr-code-container">
                <img src="data:image/png;base64,{{ qr_code_img }}" alt="QR Code" class="qr-code-img" />
                <p class="qr-label">{{ _("Escaneie o QR para verificar a autenticidade") }}</p>
            </div>
            {% endif %}
        </div>
    """

    def get_customer_details_section(self, customer_field="customer", customer_name_field="customer_name"):
        """Common customer details section - Fixed Layout"""
        return """
            <!-- Customer Details Section -->
            <div class="customer-invoice-section">
                <div class="customer-details">
                    <h4 class="section-title">{{ _("Facturar Para") }}</h4>
                    <div class="customer-info">
                        <strong class="customer-name">{{ doc.""" + customer_name_field + """ or doc.""" + customer_field + """ }}</strong><br>
                        {% if doc.tax_id %}
                            <strong>{{ _("NUIT") }}:</strong> {{ doc.tax_id }}<br>
                        {% endif %}
                        {% if doc.address_display %}
                            {{ doc.address_display }}<br>
                        {% endif %}
                        {% if doc.contact_display %}
                            <strong>{{ _("Contacto") }}:</strong> {{ doc.contact_display }}<br>
                        {% endif %}
                        {% if doc.contact_mobile %}
                            <strong>{{ _("Telemóvel") }}:</strong> {{ doc.contact_mobile }}
                        {% endif %}
                    </div>
                </div>
                
                <div class="invoice-details">
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
        """Common totals section (safe on doctypes without those fields) - Fixed Layout"""
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
            <div class="totals-section">
                <div class="amount-in-words">
                    {{% if doc.get("in_words") %}}
                    <h5>{{{{ _("Valor por Extenso") }}}}</h5>
                    <p><strong>{{{{ doc.in_words }}}}</strong></p>
                    {{% endif %}}
                    
                    {{% if doc.get("terms") %}}
                    <h5>{{{{ _("Termos e Condições") }}}}</h5>
                    <p>{{{{ doc.terms }}}}</p>
                    {{% endif %}}
                </div>
                <div class="totals-table">
                {totals_html}
                </div>
            </div>
        """
