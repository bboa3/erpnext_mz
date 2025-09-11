#!/usr/bin/env python3
"""
Comprehensive Print Formats for Mozambique ERPNext

This module creates all essential business document print formats
with consistent design and Mozambique compliance requirements.
"""

import frappe
from frappe import _
from .print_format_templates import PrintFormatTemplate


class SalesInvoicePrintFormat(PrintFormatTemplate):
    """Sales Invoice Print Format"""
    
    def __init__(self):
        super().__init__("Sales Invoice", "Fatura (MZ)")

    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("FACTURA")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
#            ("base_grand_total", "Total em {{ doc.company_currency }}", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            <!-- Compliance Enrichment: NUIT fallback and FX info -->
            <div class="row customer-invoice-section">
                <div class="col-xs-6 customer-details">
                    <div class="customer-info">
                        {% if not doc.tax_id and doc.customer %}
                            {% set __cust_nuit = frappe.db.get_value('Customer', doc.customer, 'tax_id') %}
                            {% if __cust_nuit %}
                                <div><strong>{{ _("NUIT") }}:</strong> {{ __cust_nuit }}</div>
                            {% endif %}
                        {% endif %}
                    </div>
                </div>
                <div class="col-xs-6 invoice-details">
                    <div class="invoice-info">
                        {% if doc.currency and doc.company_currency and doc.currency != doc.company_currency and doc.conversion_rate %}
                        <div class="info-row">
                            <span class="label">{{ _("Taxa de câmbio") }}:</span>
                            <span class="value">1 {{ doc.currency }} = {{ doc.conversion_rate }} {{ doc.company_currency }}</span>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}
            
            </div>
            {% endfor %}
        """


class SalesOrderPrintFormat(PrintFormatTemplate):
    """Sales Order Print Format"""
    
    def __init__(self):
        super().__init__("Sales Order", "Encomenda de Venda (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("ENCOMENDA DE VENDA")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class DeliveryNotePrintFormat(PrintFormatTemplate):
    """Delivery Note Print Format"""
    
    def __init__(self):
        super().__init__("Delivery Note", "Guia de Remessa (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("GUIA DE REMESSA")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            <!-- Transporte e Destino -->
            <div class="row customer-invoice-section">
                <div class="col-xs-6 customer-details">
                    <h4 class="section-title">{{ _("Transporte") }}</h4>
                    <div class="customer-info">
                        {% if doc.transporter_name or doc.transporter %}
                        <div><strong>{{ _("Transportadora") }}:</strong> {{ doc.transporter_name or doc.transporter }}</div>
                        {% endif %}
                        {% if doc.vehicle_no %}
                        <div><strong>{{ _("Matrícula") }}:</strong> {{ doc.vehicle_no }}</div>
                        {% endif %}
                        {% if doc.driver_name or doc.driver %}
                        <div><strong>{{ _("Motorista") }}:</strong> {{ doc.driver_name or doc.driver }}</div>
                        {% endif %}
                        {% if doc.lr_no %}
                        <div><strong>{{ _("Documento Transporte") }}:</strong> {{ doc.lr_no }}</div>
                        {% endif %}
                        {% if doc.lr_date %}
                        <div><strong>{{ _("Data Documento") }}:</strong> {{ frappe.utils.format_date(doc.lr_date) }}</div>
                        {% endif %}
                    </div>
                </div>
                <div class="col-xs-6 invoice-details">
                    <h4 class="section-title">{{ _("Destino") }}</h4>
                    <div class="invoice-info">
                        {% if doc.customer %}
                        <div class="info-row"><span class="label">{{ _("Cliente") }}:</span><span class="value">{{ doc.customer_name or doc.customer }}</span></div>
                        {% endif %}
                        {% if doc.shipping_address_display %}
                        <div class="info-row"><span class="label">{{ _("Endereço de Entrega") }}:</span><span class="value">{{ doc.shipping_address_display }}</span></div>
                        {% endif %}
                        {% if doc.posting_date %}
                        <div class="info-row"><span class="label">{{ _("Data de Saída") }}:</span><span class="value">{{ frappe.utils.format_date(doc.posting_date) }}</span></div>
                        {% endif %}
                    </div>
                </div>
            </div>

            """ + items_section + """

            """ + totals_section + """

            <!-- Assinaturas -->
            <div class="row" style="margin-top: 8px;">
                <div class="col-xs-6 text-left">
                    <div style="border-top: 1px solid #e5e5e5; padding-top: 6px;">{{ _("Emitido por") }}: {% if doc.owner %}{{ frappe.utils.get_fullname(doc.owner) or doc.owner }}{% endif %}</div>
                </div>
                <div class="col-xs-6 text-right">
                    <div style="border-top: 1px solid #e5e5e5; padding-top: 6px;">{{ _("Recebido por") }}: ____________________</div>
                </div>
            </div>

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class QuotationPrintFormat(PrintFormatTemplate):
    """Quotation Print Format"""
    
    def __init__(self):
        super().__init__("Quotation", "Orçamento (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("ORÇAMENTO")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


# Purchase Document Print Formats
class PurchaseInvoicePrintFormat(PrintFormatTemplate):
    """Purchase Invoice Print Format"""
    
    def __init__(self):
        super().__init__("Purchase Invoice", "Factura de Compra (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("FACTURA DE COMPRA")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section("supplier", "supplier_name")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class PurchaseOrderPrintFormat(PrintFormatTemplate):
    """Purchase Order Print Format"""
    
    def __init__(self):
        super().__init__("Purchase Order", "Encomenda de Compra (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("ENCOMENDA DE COMPRA")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section("supplier", "supplier_name")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class PurchaseReceiptPrintFormat(PrintFormatTemplate):
    """Purchase Receipt Print Format"""
    
    def __init__(self):
        super().__init__("Purchase Receipt", "Recibo de Compra (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("RECIBO DE COMPRA")
        footer_macro = self.get_common_footer_macro()
        customer_section = self.get_customer_details_section("supplier", "supplier_name")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "Total Geral", True),
            ("rounded_total", "Total Arredondado", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + customer_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


# Inventory Document Print Formats
class StockEntryPrintFormat(PrintFormatTemplate):
    """Stock Entry Print Format"""
    
    def __init__(self):
        super().__init__("Stock Entry", "Entrada de Stock (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("ENTRADA DE STOCK")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Stock Entry Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Tipo de Entrada") }}</h4>
                        <div class="customer-info">
                            <strong>{{ doc.stock_entry_type }}</strong>
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Detalhes") }}</h4>
                        <div class="invoice-info">
                            {% if doc.from_warehouse %}
                            <div class="info-row">
                                <span class="label">{{ _("De Armazém") }}:</span>
                                <span class="value">{{ doc.from_warehouse }}</span>
                            </div>
                            {% endif %}
                            {% if doc.to_warehouse %}
                            <div class="info-row">
                                <span class="label">{{ _("Para Armazém") }}:</span>
                                <span class="value">{{ doc.to_warehouse }}</span>
                            </div>
                            {% endif %}
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
                                <th class="text-left">{{ _("Item") }}</th>
                                <th class="text-center">{{ _("Qtd") }}</th>
                                <th class="text-center">{{ _("U.M.") }}</th>
                                <th class="text-center">{{ _("Armazém") }}</th>
                                <th class="text-right">{{ _("Valor") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in doc.items %}
                            <tr>
                                <td class="text-center">{{ loop.index }}</td>
                                <td class="text-left">
                                    <strong>{{ item.item_code }}</strong><br>
                                    {{ item.item_name }}
                                </td>
                                <td class="text-center">{{ item.get_formatted("qty", doc) }}</td>
                                <td class="text-center">{{ item.get_formatted("uom", doc) }}</td>
                                <td class="text-center">{{ item.warehouse }}</td>
                                <td class="text-right">{{ item.get_formatted("basic_rate", doc) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class MaterialRequestPrintFormat(PrintFormatTemplate):
    """Material Request Print Format"""
    
    def __init__(self):
        super().__init__("Material Request", "Pedido de Material (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("PEDIDO DE MATERIAL")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Material Request Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Detalhes do Pedido") }}</h4>
                        <div class="customer-info">
                            <strong>{{ _("Tipo") }}:</strong> {{ doc.material_request_type }}<br>
                            {% if doc.schedule_date %}
                            <strong>{{ _("Data Prevista") }}:</strong> {{ frappe.utils.format_date(doc.schedule_date) }}
                            {% endif %}
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Destino") }}</h4>
                        <div class="invoice-info">
                            {% if doc.warehouse %}
                            <div class="info-row">
                                <span class="label">{{ _("Armazém") }}:</span>
                                <span class="value">{{ doc.warehouse }}</span>
                            </div>
                            {% endif %}
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
                                <th class="text-left">{{ _("Item") }}</th>
                                <th class="text-center">{{ _("Qtd") }}</th>
                                <th class="text-center">{{ _("U.M.") }}</th>
                                <th class="text-center">{{ _("Data Prevista") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in doc.items %}
                            <tr>
                                <td class="text-center">{{ loop.index }}</td>
                                <td class="text-left">
                                    <strong>{{ item.item_code }}</strong><br>
                                    {{ item.item_name }}
                                </td>
                                <td class="text-center">{{ item.get_formatted("qty", doc) }}</td>
                                <td class="text-center">{{ item.get_formatted("uom", doc) }}</td>
                                <td class="text-center">{% if item.schedule_date %}{{ frappe.utils.format_date(item.schedule_date) }}{% endif %}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


# Financial Document Print Formats
class PaymentEntryPrintFormat(PrintFormatTemplate):
    """Payment Entry Print Format"""
    
    def __init__(self):
        super().__init__("Payment Entry", "Entrada de Pagamento (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("ENTRADA DE PAGAMENTO")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Payment Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Detalhes do Pagamento") }}</h4>
                        <div class="customer-info">
                            <div><strong>{{ _("Tipo") }}:</strong> {{ doc.payment_type  }}</div>
                            <div><strong>{{ _("Modo") }}:</strong> {{ doc.mode_of_payment }}</div>
                            {% if doc.party %}
                            {% set __party_label = (doc.party_type=="Customer" and _("Cliente")) or (doc.party_type=="Supplier" and _("Fornecedor")) or _("Parte") %}
                            <div><strong>{{ __party_label }}:</strong> {{ doc.party_name or doc.party }}</div>
                            {% set __party_nuit = frappe.db.get_value(doc.party_type, doc.party, 'tax_id') %}
                            {% if __party_nuit %}
                                <div><strong>{{ _("NUIT") }}:</strong> {{ __party_nuit }}</div>
                            {% endif %}
                            {% endif %}
                            {% if doc.paid_from %}
                            <div><strong>{{ _("Conta Origem") }}:</strong> {{ doc.paid_from }}</div>
                            {% endif %}
                            {% if doc.paid_to %}
                            <div><strong>{{ _("Conta Destino") }}:</strong> {{ doc.paid_to }}</div>
                            {% endif %}
                            {% if doc.reference_no %}
                            <div><strong>{{ _("Ref. Nº") }}:</strong> {{ doc.reference_no }}</div>
                            {% endif %}
                            {% if doc.reference_date %}
                            <div><strong>{{ _("Data da Referência") }}:</strong> {{ frappe.utils.format_date(doc.reference_date) }}</div>
                            {% endif %}
                            {% if doc.clearance_date %}
                            <div><strong>{{ _("Data de Compensação") }}:</strong> {{ frappe.utils.format_date(doc.clearance_date) }}</div>
                            {% endif %}
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Valores") }}</h4>
                        <div class="invoice-info">
                            <div class="info-row">
                                <span class="label">{{ _("Valor pago (origem)") }} [{{ doc.paid_from_account_currency or doc.company_currency }}]:</span>
                                <span class="value">{{ doc.get_formatted("paid_amount", doc) }}</span>
                            </div>
                            {% if doc.received_amount %}
                            <div class="info-row">
                                <span class="label">{{ _("Valor recebido (destino)") }} [{{ doc.paid_to_account_currency or doc.company_currency }}]:</span>
                                <span class="value">{{ doc.get_formatted("received_amount", doc) }}</span>
                            </div>
                            {% endif %}
                            {% if doc.paid_from_account_currency and doc.paid_to_account_currency and doc.paid_from_account_currency != doc.paid_to_account_currency %}
                            {% set __fx = doc.get('target_exchange_rate') or 0 %}
                            {% if __fx %}
                            <div class="info-row">
                                <span class="label">{{ _("Taxa de câmbio") }}:</span>
                                <span class="value">1 {{ doc.paid_from_account_currency }} = {{ __fx }} {{ doc.paid_to_account_currency }}</span>
                            </div>
                            {% endif %}
                            {% endif %}
                        </div>
                    </div>
                </div>

                <!-- References Section -->
                {% if doc.references %}
                <div class="items-section">
                    <h4 class="section-title">{{ _("Referências") }}</h4>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th class="text-left">{{ _("Tipo") }}</th>
                                <th class="text-left">{{ _("Documento") }}</th>
                                <th class="text-center">{{ _("Data") }}</th>
                                <th class="text-right">{{ _("Valor") }}</th>
                                <th class="text-right">{{ _("Saldo Após Pagamento") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for ref in doc.references %}
                            <tr>
                                <td class="text-left">{{ ref.reference_doctype }}</td>
                                <td class="text-left">{{ ref.reference_name }}</td>
                                {% set __ref_date = frappe.db.get_value(ref.reference_doctype, ref.reference_name, 'posting_date') or frappe.db.get_value(ref.reference_doctype, ref.reference_name, 'transaction_date') or frappe.db.get_value(ref.reference_doctype, ref.reference_name, 'bill_date') %}
                                <td class="text-center">{% if __ref_date %}{{ frappe.utils.format_date(__ref_date) }}{% endif %}</td>
                                <td class="text-right">{{ ref.get_formatted("allocated_amount", doc) }}</td>
                                {% set __remaining = frappe.db.get_value(ref.reference_doctype, ref.reference_name, 'outstanding_amount') %}
                                <td class="text-right">{% if __remaining is not none %}{{ frappe.utils.fmt_money(__remaining, currency=(doc.paid_to_account_currency or doc.company_currency)) }}{% else %}—{% endif %}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- Deduções / Retenções -->
                {% if doc.deductions or doc.get('difference_amount') %}
                <div class="items-section">
                    <h4 class="section-title">{{ _("Retenções e Outras Deduções") }}</h4>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th class="text-left">{{ _("Conta") }}</th>
                                <th class="text-left">{{ _("Descrição") }}</th>
                                <th class="text-right">{{ _("Valor") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for d in doc.deductions %}
                            <tr>
                                <td class="text-left">{{ d.account }}</td>
                                <td class="text-left">{{ d.description or '' }}</td>
                                <td class="text-right">{{ d.get_formatted('amount', doc) }}</td>
                            </tr>
                            {% endfor %}
                            {% if doc.get('difference_amount') %}
                            <tr>
                                <td class="text-left">—</td>
                                <td class="text-left">{{ _("Diferença") }}</td>
                                <td class="text-right">{{ doc.get_formatted('difference_amount', doc) }}</td>
                            </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- Disclaimer -->
                <div class="row">
                    <div class="col-xs-12 text-left">
                        <div class="qr-label">{{ _("Comprovativo de pagamento. Não substitui a factura para efeitos fiscais (CIVA).") }}</div>
                    </div>
                </div>

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class JournalEntryPrintFormat(PrintFormatTemplate):
    """Journal Entry Print Format"""
    
    def __init__(self):
        super().__init__("Journal Entry", "Lançamento Contabilístico (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("LANÇAMENTO CONTABILÍSTICO")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Journal Entry Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Detalhes do Lançamento") }}</h4>
                        <div class="customer-info">
                            <strong>{{ _("Tipo") }}:</strong> {{ doc.voucher_type }}<br>
                            {% if doc.cheque_no %}
                            <strong>{{ _("Nº Cheque") }}:</strong> {{ doc.cheque_no }}<br>
                            {% endif %}
                            {% if doc.cheque_date %}
                            <strong>{{ _("Data Cheque") }}:</strong> {{ frappe.utils.format_date(doc.cheque_date) }}
                            {% endif %}
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Valores") }}</h4>
                        <div class="invoice-info">
                            <div class="info-row">
                                <span class="label">{{ _("Total Débito") }}:</span>
                                <span class="value">{{ doc.get_formatted("total_debit", doc) }}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">{{ _("Total Crédito") }}:</span>
                                <span class="value">{{ doc.get_formatted("total_credit", doc) }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Accounts Section -->
                <div class="items-section">
                    <h4 class="section-title">{{ _("Contas") }}</h4>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th class="text-left">{{ _("Conta") }}</th>
                                <th class="text-left">{{ _("Centro de Custo") }}</th>
                                <th class="text-right">{{ _("Débito") }}</th>
                                <th class="text-right">{{ _("Crédito") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for account in doc.accounts %}
                            <tr>
                                <td class="text-left">
                                    <strong>{{ account.account }}</strong><br>
                                    {% if account.party_type and account.party %}
                                    <small>{{ account.party_type }}: {{ account.party }}</small>
                                    {% endif %}
                                </td>
                                <td class="text-left">{{ account.cost_center or '' }}</td>
                                <td class="text-right">{% if account.debit %}{{ account.get_formatted("debit", doc) }}{% endif %}</td>
                                <td class="text-right">{% if account.credit %}{{ account.get_formatted("credit", doc) }}{% endif %}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


# HR Document Print Formats
class PayslipPrintFormat(PrintFormatTemplate):
    """Payslip Print Format"""
    
    def __init__(self):
        super().__init__("Salary Slip", "Recibo de Vencimento (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("RECIBO DE VENCIMENTO")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Employee Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Dados do Funcionário") }}</h4>
                        <div class="customer-info">
                            <strong>{{ doc.employee_name }}</strong><br>
                            <strong>{{ _("Nº Funcionário") }}:</strong> {{ doc.employee }}<br>
                            {% if doc.designation %}
                            <strong>{{ _("Cargo") }}:</strong> {{ doc.designation }}<br>
                            {% endif %}
                            {% if doc.department %}
                            <strong>{{ _("Departamento") }}:</strong> {{ doc.department }}
                            {% endif %}
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Período") }}</h4>
                        <div class="invoice-info">
                            <div class="info-row">
                                <span class="label">{{ _("De") }}:</span>
                                <span class="value">{{ frappe.utils.format_date(doc.start_date) }}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">{{ _("Até") }}:</span>
                                <span class="value">{{ frappe.utils.format_date(doc.end_date) }}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">{{ _("Dias Trabalhados") }}:</span>
                                <span class="value">{{ doc.payment_days }}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Earnings Section -->
                {% if doc.earnings %}
                <div class="items-section">
                    <h4 class="section-title">{{ _("Vencimentos") }}</h4>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th class="text-left">{{ _("Descrição") }}</th>
                                <th class="text-center">{{ _("Dias/Horas") }}</th>
                                <th class="text-right">{{ _("Taxa") }}</th>
                                <th class="text-right">{{ _("Valor") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for earning in doc.earnings %}
                            <tr>
                                <td class="text-left">{{ earning.salary_component }}</td>
                                <td class="text-center">{% if earning.amount %}{{ earning.get_formatted("amount", doc) }}{% endif %}</td>
                                <td class="text-right">{% if earning.default_amount %}{{ earning.get_formatted("default_amount", doc) }}{% endif %}</td>
                                <td class="text-right">{{ earning.get_formatted("amount", doc) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- Deductions Section -->
                {% if doc.deductions %}
                <div class="items-section">
                    <h4 class="section-title">{{ _("Descontos") }}</h4>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th class="text-left">{{ _("Descrição") }}</th>
                                <th class="text-right">{{ _("Valor") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for deduction in doc.deductions %}
                            <tr>
                                <td class="text-left">{{ deduction.salary_component }}</td>
                                <td class="text-right">{{ deduction.get_formatted("amount", doc) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- Totals Section -->
                <div class="row totals-section">
                    <div class="col-xs-12">
                        <div class="totals-table">
                            <div class="totals-row">
                                <span class="totals-label">{{ _("Total Vencimentos") }}:</span>
                                <span class="totals-value">{{ doc.get_formatted("gross_pay", doc) }}</span>
                            </div>
                            <div class="totals-row">
                                <span class="totals-label">{{ _("Total Descontos") }}:</span>
                                <span class="totals-value">{{ doc.get_formatted("total_deduction", doc) }}</span>
                            </div>
                            <div class="totals-row grand-total">
                                <span class="totals-label">{{ _("Líquido a Receber") }}:</span>
                                <span class="totals-value">{{ doc.get_formatted("net_pay", doc) }}</span>
                            </div>
                        </div>
                    </div>
                </div>

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


# Customer/Supplier Print Formats
class CustomerPrintFormat(PrintFormatTemplate):
    """Customer Print Format"""
    
    def __init__(self):
        super().__init__("Customer", "Cliente (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("DADOS DO CLIENTE")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Customer Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Informações Gerais") }}</h4>
                        <div class="customer-info">
                            <strong>{{ doc.customer_name }}</strong><br>
                            {% if doc.tax_id %}
                            <strong>{{ _("NUIT") }}:</strong> {{ doc.tax_id }}<br>
                            {% endif %}
                            {% if doc.customer_type %}
                            <strong>{{ _("Tipo") }}:</strong> {{ doc.customer_type }}<br>
                            {% endif %}
                            {% if doc.territory %}
                            <strong>{{ _("Território") }}:</strong> {{ doc.territory }}
                            {% endif %}
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Contactos") }}</h4>
                        <div class="invoice-info">
                            {% if doc.mobile_no %}
                            <div class="info-row">
                                <span class="label">{{ _("Telemóvel") }}:</span>
                                <span class="value">{{ doc.mobile_no }}</span>
                            </div>
                            {% endif %}
                            {% if doc.email_id %}
                            <div class="info-row">
                                <span class="label">{{ _("Email") }}:</span>
                                <span class="value">{{ doc.email_id }}</span>
                            </div>
                            {% endif %}
                            {% if doc.website %}
                            <div class="info-row">
                                <span class="label">{{ _("Website") }}:</span>
                                <span class="value">{{ doc.website }}</span>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>

                <!-- Address Section -->
                {% if doc.customer_primary_address %}
                <div class="items-section">
                    <h4 class="section-title">{{ _("Endereço Principal") }}</h4>
                    <div class="customer-info">
                        {{ doc.customer_primary_address }}
                    </div>
                </div>
                {% endif %}

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class SupplierPrintFormat(PrintFormatTemplate):
    """Supplier Print Format"""
    
    def __init__(self):
        super().__init__("Supplier", "Fornecedor (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("DADOS DO FORNECEDOR")
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                <!-- Supplier Details -->
                <div class="row customer-invoice-section">
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Informações Gerais") }}</h4>
                        <div class="customer-info">
                            <strong>{{ doc.supplier_name }}</strong><br>
                            {% if doc.tax_id %}
                            <strong>{{ _("NUIT") }}:</strong> {{ doc.tax_id }}<br>
                            {% endif %}
                            {% if doc.supplier_type %}
                            <strong>{{ _("Tipo") }}:</strong> {{ doc.supplier_type }}<br>
                            {% endif %}
                            {% if doc.country %}
                            <strong>{{ _("País") }}:</strong> {{ doc.country }}
                            {% endif %}
                        </div>
                    </div>
                    <div class="col-xs-6">
                        <h4 class="section-title">{{ _("Contactos") }}</h4>
                        <div class="invoice-info">
                            {% if doc.mobile_no %}
                            <div class="info-row">
                                <span class="label">{{ _("Telemóvel") }}:</span>
                                <span class="value">{{ doc.mobile_no }}</span>
                            </div>
                            {% endif %}
                            {% if doc.email_id %}
                            <div class="info-row">
                                <span class="label">{{ _("Email") }}:</span>
                                <span class="value">{{ doc.email_id }}</span>
                            </div>
                            {% endif %}
                            {% if doc.website %}
                            <div class="info-row">
                                <span class="label">{{ _("Website") }}:</span>
                                <span class="value">{{ doc.website }}</span>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                </div>

                <!-- Address Section -->
                {% if doc.supplier_primary_address %}
                <div class="items-section">
                    <h4 class="section-title">{{ _("Endereço Principal") }}</h4>
                    <div class="customer-info">
                        {{ doc.supplier_primary_address }}
                    </div>
                </div>
                {% endif %}

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


# Main function to create all print formats
@frappe.whitelist()
def create_all_mozambique_print_formats():
    """Create all Mozambique print formats and set them as default"""
    formats_created = []
    
    try:
        # Step 1: Complete preparation using enhanced script
        from .disable_existing_print_formats import (
            prepare_for_mozambique_print_formats,
            set_mozambique_print_formats_as_default,
            ensure_only_mozambique_formats_enabled
        )
        
        preparation_result = prepare_for_mozambique_print_formats()
        frappe.log_error(f"Preparation completed: {preparation_result}", "Print Format Preparation")
        
        # Step 2: Create all Mozambique print formats
        # Sales Documents
        sales_invoice = SalesInvoicePrintFormat()
        formats_created.append(sales_invoice.create_print_format())
        
        sales_order = SalesOrderPrintFormat()
        formats_created.append(sales_order.create_print_format())
        
        delivery_note = DeliveryNotePrintFormat()
        formats_created.append(delivery_note.create_print_format())
        
        quotation = QuotationPrintFormat()
        formats_created.append(quotation.create_print_format())
        
        # Purchase Documents
        purchase_invoice = PurchaseInvoicePrintFormat()
        formats_created.append(purchase_invoice.create_print_format())
        
        purchase_order = PurchaseOrderPrintFormat()
        formats_created.append(purchase_order.create_print_format())
        
        purchase_receipt = PurchaseReceiptPrintFormat()
        formats_created.append(purchase_receipt.create_print_format())
        
        # Inventory Documents
        stock_entry = StockEntryPrintFormat()
        formats_created.append(stock_entry.create_print_format())
        
        material_request = MaterialRequestPrintFormat()
        formats_created.append(material_request.create_print_format())
        
        # Financial Documents
        payment_entry = PaymentEntryPrintFormat()
        formats_created.append(payment_entry.create_print_format())
        
        journal_entry = JournalEntryPrintFormat()
        formats_created.append(journal_entry.create_print_format())
        
        # HR Documents
        payslip = PayslipPrintFormat()
        formats_created.append(payslip.create_print_format())
        
        # Customer/Supplier Documents
        customer = CustomerPrintFormat()
        formats_created.append(customer.create_print_format())
        
        supplier = SupplierPrintFormat()
        formats_created.append(supplier.create_print_format())
        
        # Step 3: Set Mozambique formats as default for their DocTypes
        default_result = set_mozambique_print_formats_as_default()

        # Step 4: Ensure only Mozambique formats are enabled
        enable_result = ensure_only_mozambique_formats_enabled()
        
        return {
            "formats_created": formats_created,
            "defaults_set": default_result,
            "enforcement": enable_result,
            "status": "complete"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating print formats: {str(e)}", "Print Format Creation")
        frappe.throw(_("Failed to create print formats: {0}").format(str(e)))


if __name__ == "__main__":
    # This can be run as a script
    frappe.init(site="erp.local")
    frappe.connect()
    
    # Create all print formats
    formats = create_all_mozambique_print_formats()
    print(f"Created {len(formats)} print formats: {formats}")