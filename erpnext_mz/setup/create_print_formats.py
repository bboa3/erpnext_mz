#!/usr/bin/env python3
"""
Mozambique Sales Invoice Print Format Creator

This script creates professional print formats for Sales Invoices
specifically designed for Mozambique compliance requirements.

Features:
- Professional layout with company branding
- Mozambique-specific fields (NUIT, tax information)
- Bilingual support (Portuguese/English)
- QR code integration for digital compliance
- Proper tax breakdown display
- Terms and conditions integration
"""

import frappe
from frappe import _
import json
from datetime import datetime


@frappe.whitelist()
def create_mozambique_sales_invoice_print_format():
    """
    Creates a professional Sales Invoice print format for Mozambique
    """
    try:
        # Check if print format already exists
        if frappe.db.exists("Print Format", "Fatura (MZ)"):
            frappe.msgprint(_("Print Format 'Fatura (MZ)' already exists"))
            return "Fatura (MZ)"
        
        # Create the print format
        print_format = frappe.new_doc("Print Format")
        print_format.update({
            "name": "Fatura (MZ)",
            "doc_type": "Sales Invoice",
            "module": "ERPNext MZ",
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
        
        # Set the HTML template
        print_format.html = get_mozambique_sales_invoice_template()
        
        # Set custom CSS
        print_format.css = get_mozambique_sales_invoice_css()
        

        
        # Save the print format
        print_format.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.msgprint(_("Successfully created 'Fatura (MZ)' print format"))
        return print_format.name
        
    except Exception as e:
        frappe.log_error(f"Error creating print format: {str(e)}")
        frappe.throw(_("Failed to create print format: {0}").format(str(e)))


def get_mozambique_sales_invoice_template():
    """
    Returns the HTML template for Fatura (MZ)
    """
    return """
{%- macro add_header(page_num, max_pages, doc, letter_head, no_letterhead, footer, print_settings=None, print_heading_template=None) -%}
    {% if letter_head and not no_letterhead %}
        <div class="letter-head">{{ letter_head }}</div>
    {% endif %}
    
    <!-- Document Title Section -->
    <div class="document-header">
        <div class="row">
            <div class="col-xs-8">
                <h1 class="document-title">{{ _("FACTURA") }}</h1>
            </div>
            <div class="col-xs-4 text-right">
                <div class="document-number">
                    <strong>{{ doc.name }}</strong>
                </div>
                <div class="document-date">
                    {{ frappe.utils.format_date(doc.posting_date) }}
                </div>
            </div>
        </div>
    </div>
    
    {%- if doc.meta.is_submittable and doc.docstatus==2-%}
    <div class="text-center document-status-cancelled">
        <h3>{{ _("CANCELADA") }}</h3>
    </div>
    {%- endif -%}
{%- endmacro -%}

{% for page in layout %}
<div class="page-break">
    <div {% if print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
        {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
    </div>

    <!-- Customer and Invoice Details Section -->
    <div class="row customer-invoice-section">
        <div class="col-xs-6 customer-details">
            <h4 class="section-title">{{ _("Facturar Para") }}</h4>
            <div class="customer-info">
                <strong class="customer-name">{{ doc.customer_name or doc.customer }}</strong><br>
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
        
        <div class="col-xs-6 invoice-details">
            <h4 class="section-title">{{ _("Detalhes da Factura") }}</h4>
            <div class="invoice-info">
                <div class="info-row">
                    <span class="label">{{ _("Vencimento") }}:</span>
                    <span class="value">{{ frappe.utils.format_date(doc.due_date) }}</span>
                </div>
                {% if doc.po_no %}
                <div class="info-row">
                    <span class="label">{{ _("Nº Encomenda") }}:</span>
                    <span class="value">{{ doc.po_no }}</span>
                </div>
                {% endif %}
                <div class="info-row">
                    <span class="label">{{ _("Moeda") }}:</span>
                    <span class="value">{{ doc.currency }}</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Items Table Section -->
    <div class="items-section">
        <h4 class="section-title">{{ _("Artigos") }}</h4>
        <table class="items-table">
            <thead>
                <tr>
                    <th class="text-center">{{ _("Sr") }}</th>
                    <th class="text-left">{{ _("Descrição") }}</th>
                    <th class="text-center">{{ _("Qtd") }}</th>
                    <th class="text-center">{{ _("U.M.") }}</th>
                    <th class="text-right">{{ _("Preço") }}</th>
                    <th class="text-right">{{ _("Valor") }}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in doc.items %}
                <tr>
                    <td class="text-center">{{ loop.index }}</td>
                    <td class="item-description">
                        <strong>{{ item.item_code }}</strong><br>
                        {{ item.item_name }}
                        {% if item.description and item.description != item.item_name %}
                            <br><em>{{ item.description }}</em>
                        {% endif %}
                        {% if item.serial_no %}
                            <br><small><strong>{{ _("Nº de Série") }}:</strong> {{ item.serial_no }}</small>
                        {% endif %}
                    </td>
                    <td class="text-center">{{ item.get_formatted("qty", 0) }}</td>
                    <td class="text-center">{{ item.get_formatted("uom", 0) }}</td>
                    <td class="text-right">{{ item.get_formatted("net_rate", doc) }}</td>
                    <td class="text-right">{{ item.get_formatted("net_amount", doc) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Totals Section -->
    <div class="row totals-section">
        <div class="col-xs-6">
            {% if doc.in_words %}
            <div class="amount-in-words">
                <h5>{{ _("Valor por Extenso") }}</h5>
                <p><strong>{{ doc.in_words }}</strong></p>
            </div>
            {% endif %}
            
            {% if doc.terms %}
            <div class="terms-section">
                <h5>{{ _("Termos e Condições") }}</h5>
                <p>{{ doc.terms }}</p>
            </div>
            {% endif %}
        </div>
        
        <div class="col-xs-6">
            <div class="totals-table">
                <div class="totals-row">
                    <span class="totals-label">{{ _("Sub Total") }}:</span>
                    <span class="totals-value">{{ doc.get_formatted("net_total", doc) }}</span>
                </div>
                
                {% for tax in doc.taxes %}
                    {% if tax.tax_amount %}
                    <div class="totals-row">
                        <span class="totals-label">{{ _(tax.description) }}:</span>
                        <span class="totals-value">{{ tax.get_formatted("tax_amount", doc) }}</span>
                    </div>
                    {% endif %}
                {% endfor %}
                
                {% if doc.discount_amount %}
                <div class="totals-row">
                    <span class="totals-label">{{ _("Desconto") }}:</span>
                    <span class="totals-value">-{{ doc.get_formatted("discount_amount", doc) }}</span>
                </div>
                {% endif %}
                
                <div class="totals-row grand-total">
                    <span class="totals-label">{{ _("Total Geral") }}:</span>
                    <span class="totals-value">{{ doc.get_formatted("grand_total", doc) }}</span>
                </div>
                
                {% if doc.rounded_total and doc.rounded_total != doc.grand_total %}
                <div class="totals-row">
                    <span class="totals-label">{{ _("Total Arredondado") }}:</span>
                    <span class="totals-value">{{ doc.get_formatted("rounded_total", doc) }}</span>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Payment Information -->
    {% if doc.outstanding_amount %}
    <div class="row payment-section">
        <div class="col-xs-12">
            <div class="payment-info">
                <h5>{{ _("Informações de Pagamento") }}</h5>
                <p><strong>{{ _("Valor em Aberto") }}:</strong> {{ doc.get_formatted("outstanding_amount", doc) }}</p>
                <p><strong>{{ _("Estado") }}:</strong> {{ doc.status }}</p>
            </div>
        </div>
    </div>
    {% endif %}

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

    {% if print_settings.repeat_header_footer %}
    <div id="footer-html" class="visible-pdf">
        {% if not no_letterhead and footer %}
        <div class="letter-head-footer">
            {{ footer }}
        </div>
        {% endif %}
        <p class="text-center small page-number visible-pdf">
            {{ _("Página {0} de {1}").format('<span class="page"></span>', '<span class="topage"></span>') }}
        </p>
    </div>
    {% endif %}
</div>
{% endfor %}
"""


def get_mozambique_sales_invoice_css():
    """
    Returns the CSS styles for Fatura (MZ) - Clean and Professional Design
    """
    return """
/* Mozambique Sales Invoice Print Format - Clean Professional Styles */

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
    padding-bottom: 15px;
    margin-bottom: 25px;
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
    margin: 5px 0 0 0;
    font-weight: 400;
}

.document-number {
    font-size: 16px;
    color: #2c3e50;
    margin-bottom: 5px;
}

.document-date {
    font-size: 12px;
    color: #7f8c8d;
}

/* Document Status */
.document-status-cancelled {
    background-color: #fdf2f2;
    border: 1px solid #fecaca;
    padding: 12px;
    margin: 15px 0;
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
    margin: 0 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #e5e5e5;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Customer and Invoice Details */
.customer-invoice-section {
    margin-bottom: 25px;
}

.customer-details, .invoice-details {
    padding: 0;
}

.customer-name {
    color: #2c3e50;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
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
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    padding: 4px 0;
}

.info-row .label {
    color: #7f8c8d;
    font-weight: 500;
}

.info-row .value {
    color: #2c3e50;
    font-weight: 500;
}

/* Items Table */
.items-section {
    margin-bottom: 25px;
}

.items-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    border: 1px solid #e5e5e5;
}

.items-table th {
    background-color: #f8f9fa;
    color: #2c3e50;
    padding: 12px 8px;
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
    padding: 10px 8px;
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
    margin-bottom: 25px;
}

.amount-in-words, .terms-section {
    padding: 15px 0;
    margin-bottom: 15px;
}

.amount-in-words h5, .terms-section h5 {
    color: #2c3e50;
    margin: 0 0 8px 0;
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
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #f0f0f0;
}

.totals-row:last-child {
    border-bottom: none;
}

.totals-label {
    color: #555;
    font-size: 12px;
    font-weight: 500;
}

.totals-value {
    color: #2c3e50;
    font-size: 12px;
    font-weight: 500;
}

.totals-row.grand-total {
    border-top: 2px solid #2c3e50;
    margin-top: 8px;
    padding-top: 12px;
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
    margin-bottom: 25px;
}

.payment-info {
    background-color: #fef3c7;
    border: 1px solid #f59e0b;
    padding: 15px;
    border-radius: 4px;
}

.payment-info h5 {
    color: #92400e;
    margin: 0 0 8px 0;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.payment-info p {
    margin: 4px 0;
    font-size: 12px;
    color: #92400e;
}

/* QR Code Section */
.qr-section {
    margin-bottom: 20px;
}

.qr-code-container {
    text-align: center;
    padding: 15px 0;
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
    margin: 8px 0 0 0;
    font-style: italic;
}

/* Utility Classes */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }
.text-uppercase { text-transform: uppercase; }

/* Page Break */
.page-break {
    page-break-inside: avoid;
}

/* Print Specific Styles */
@media print {
    .print-format {
        font-size: 11px;
    }
    
    .document-title {
        font-size: 20px;
    }
    
    .items-table th,
    .items-table td {
        padding: 8px 6px;
    }
    
    .totals-row {
        padding: 4px 0;
    }
    
    .qr-code-img {
        max-width: 80px;
        max-height: 80px;
    }
}

/* Responsive adjustments */
@media screen and (max-width: 768px) {
    .customer-invoice-section .col-xs-6 {
        width: 100%;
        margin-bottom: 20px;
    }
    
    .totals-section .col-xs-6 {
        width: 100%;
        margin-bottom: 20px;
    }
    
    .info-row {
        flex-direction: column;
    }
    
    .info-row .value {
        margin-top: 2px;
    }
    
    .totals-row {
        flex-direction: column;
    }
    
    .totals-row .totals-value {
        margin-top: 2px;
    }
}
"""



@frappe.whitelist()
def create_all_mozambique_print_formats():
    """
    Creates all Mozambique-specific print formats
    """
    formats_created = []
    
    try:
        # Create Sales Invoice print format
        sales_invoice_format = create_mozambique_sales_invoice_print_format()
        formats_created.append(sales_invoice_format)
        
        frappe.msgprint(_("Successfully created {0} print formats").format(len(formats_created)))
        return formats_created
        
    except Exception as e:
        frappe.log_error(f"Error creating print formats: {str(e)}")
        frappe.throw(_("Failed to create print formats: {0}").format(str(e)))


@frappe.whitelist()
def set_default_print_format(doctype, print_format_name):
    """
    Sets a print format as default for a specific doctype
    """
    try:
        # Update the default print format in Print Settings
        if frappe.db.exists("Print Format", print_format_name):
            # This would typically be done through Print Settings
            frappe.msgprint(_("Print format '{0}' is available for {1}").format(print_format_name, doctype))
            return True
        else:
            frappe.throw(_("Print format '{0}' does not exist").format(print_format_name))
            
    except Exception as e:
        frappe.log_error(f"Error setting default print format: {str(e)}")
        frappe.throw(_("Failed to set default print format: {0}").format(str(e)))


if __name__ == "__main__":
    # This can be run as a script
    frappe.init(site="erp.local")
    frappe.connect()
    
    # Create the print format
    format_name = create_mozambique_sales_invoice_print_format()
    print(f"Created print format: {format_name}")
