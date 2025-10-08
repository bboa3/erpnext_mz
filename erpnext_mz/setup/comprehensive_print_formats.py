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
        meta_cards_section = self.get_meta_cards_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True),
#            ("base_grand_total", "Total em {{ doc.company_currency }}", False)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                """ + meta_cards_section + """
                
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
        meta_cards_section = self.get_meta_cards_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True),
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + meta_cards_section + """

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
        meta_cards_section = self.get_meta_cards_delivery_note_section()
        signatures_section = self.get_signatures_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + meta_cards_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + signatures_section + """

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
        meta_cards_section = self.get_meta_cards_section()
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + meta_cards_section + """

            """ + items_section + """

            """ + totals_section + """

            """ + qr_section + """

            {% if print_settings and print_settings.repeat_header_footer %}
                {{ add_footer(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
            {% endif %}

            </div>
            {% endfor %}
        """


class SalesInvoiceReturnPrintFormat(PrintFormatTemplate):
    """Sales Invoice Return"""

    def __init__(self):
        super().__init__("Sales Invoice", "Nota de Crédito (MZ)")
    
    def get_html_template(self):
        header_macro = self.get_common_header_macro("NOTA DE CRÉDITO")
        footer_macro = self.get_common_footer_macro()
        meta_cards_section = self.get_meta_cards_section("customer", "customer_name", "Beneficiário do Crédito")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True)
        ])
        qr_section = self.get_qr_code_section()

        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                """ + meta_cards_section + """

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
        meta_cards_section = self.get_meta_cards_section("supplier", "supplier_name")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + meta_cards_section + """

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
        meta_cards_section = self.get_meta_cards_section("supplier", "supplier_name")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + meta_cards_section + """

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
        meta_cards_section = self.get_meta_cards_section("supplier", "supplier_name")
        items_section = self.get_items_table_section()
        totals_section = self.get_totals_section([
            ("net_total", "Sub-Total", True),
            ("tax_amount", "Imposto", False),
            ("discount_amount", "Desconto", False),
            ("grand_total", "TOTAL", True)
        ])
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

            """ + meta_cards_section + """

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

                <!-- Meta cards -->
                <table class="meta avoid-break" aria-label="Detalhes">
                  <tr>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DETALHES</h3>
                        <p>{{ _("Tipo de Entrada") }}: <span>{{ doc.stock_entry_type }}</span></p>
                      </section>
                    </td>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DETALHES DO DOCUMENTO</h3>
                        {% set __dt = (doc.get('posting_date') and (doc.posting_date ~ " " ~ (doc.get('posting_time') or "00:00:00")))
                            or (doc.get('transaction_date') and (doc.transaction_date ~ " 00:00:00"))
                            or doc.creation %}
                        <p>{{ _("Data") }}: <span>{{ frappe.utils.format_datetime(__dt) }}</span></p>
                        {% if doc.from_warehouse %}<p>{{ _("De Armazém") }}: <span>{{ doc.from_warehouse }}</span></p>{% endif %}
                        {% if doc.to_warehouse %}<p>{{ _("Para Armazém") }}: <span>{{ doc.to_warehouse }}</span></p>{% endif %}
                      </section>
                    </td>
                  </tr>
                </table>

                <!-- Soft divider -->
                <div class="hr" aria-hidden="true"></div>

                <!-- Items table -->
                <section aria-label="Artigos">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Descrição") }}</th>
                        <th scope="col" class="right">{{ _("Qtd") }}</th>
                        <th scope="col" class="right">{{ _("U.M.") }}</th>
                        <th scope="col" class="right">{{ _("Armazém") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for item in doc.items %}
                      <tr>
                        <td>{{ item.item_name or item.item_code }}</td>
                        <td class="right">{{ item.get_formatted('qty', doc) }}</td>
                        <td class="right">{{ item.get_formatted('uom', doc) }}</td>
                        <td class="right">{{ item.warehouse }}</td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </section>

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

                <!-- Meta cards -->
                <table class="meta avoid-break" aria-label="Detalhes e Destino">
                  <tr>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DETALHES DO PEDIDO</h3>
                        <p>{{ _("Tipo") }}: <span>{{ doc.material_request_type }}</span></p>
                        {% if doc.schedule_date %}
                        <p>{{ _("Data Prevista") }}: <span>{{ frappe.utils.format_date(doc.schedule_date) }}</span></p>
                        {% endif %}
                      </section>
                    </td>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DESTINO</h3>
                        {% set __dt = (doc.get('posting_date') and (doc.posting_date ~ " " ~ (doc.get('posting_time') or "00:00:00")))
                            or (doc.get('transaction_date') and (doc.transaction_date ~ " 00:00:00"))
                            or doc.creation %}
                        <p>{{ _("Data") }}: <span>{{ frappe.utils.format_datetime(__dt) }}</span></p>
                        {% if doc.warehouse %}<p>{{ _("Armazém") }}: <span>{{ doc.warehouse }}</span></p>{% endif %}
                      </section>
                    </td>
                  </tr>
                </table>

                <div class="hr" aria-hidden="true"></div>

                <!-- Items table -->
                <section aria-label="Artigos">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Descrição") }}</th>
                        <th scope="col" class="right">{{ _("Qtd") }}</th>
                        <th scope="col" class="right">{{ _("U.M.") }}</th>
                        <th scope="col" class="right">{{ _("Data Prevista") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for item in doc.items %}
                      <tr>
                        <td>{{ item.item_name or item.item_code }}</td>
                        <td class="right">{{ item.get_formatted('qty', doc) }}</td>
                        <td class="right">{{ item.get_formatted('uom', doc) }}</td>
                        <td class="right">{% if item.schedule_date %}{{ frappe.utils.format_date(item.schedule_date) }}{% endif %}</td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </section>

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
        header_macro = self.get_common_header_macro("RECIBO DE PAGAMENTO")
        meta_cards_section = self.get_meta_cards_payment_entry_section()
        footer_macro = self.get_common_footer_macro()
        qr_section = self.get_qr_code_section()
        
        return header_macro + footer_macro + """
            {% for page in layout %}
            <div class="page-break">
                <div {% if print_settings and print_settings.repeat_header_footer %} id="header-html" class="hidden-pdf" {% endif %}>
                    {{ add_header(loop.index, layout|len, doc, letter_head, no_letterhead, footer, print_settings) }}
                </div>

                """ + meta_cards_section + """

                <!-- References Section -->
                {% if doc.references %}
                    <section>
                        <h4 class="muted">{{ _("Referências") }}</h4>
                        <div class="hr" aria-hidden="true"></div>
                        <table class="items" role="table">
                            <thead>
                                <tr>
                                    <th scope="col" class="left">{{ _("Tipo") }}</th>
                                    <th scope="col" class="right">{{ _("Documento") }}</th>
                                    <th scope="col" class="right">{{ _("Data") }}</th>
                                    <th scope="col" class="right">{{ _("Total da Fatura") }}</th>
                                    <th scope="col" class="right">{{ _("Saldo Antes") }}</th>
                                    <th scope="col" class="right">{{ _("Saldo Após Pagamento") }}</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for ref in doc.references %}
                                    <tr>
                                        <td class="left">{{ ref.reference_doctype }}</td>
                                        <td class="right">{{ ref.reference_name }}</td>
                                        {% set __ref_doc = frappe.get_doc(ref.reference_doctype, ref.reference_name) %}
                                        {% set __ref_date = __ref_doc.get('posting_date') or __ref_doc.get('transaction_date') or __ref_doc.get('bill_date') %}
                                        <td class="right">{% if __ref_date %}{{ frappe.utils.format_date(__ref_date) }}{% endif %}</td>
                                        {% set __grand_total = __ref_doc.get('grand_total') %}
                                        <td class="right">{% if __grand_total is not none %}{{ frappe.utils.fmt_money(__grand_total, currency=(doc.paid_to_account_currency or doc.company_currency)) }}{% else %}—{% endif %}</td>
                                        {% if ref.reference_doctype in ['Sales Order', 'Purchase Order'] %}
                                            {% set __advance_paid_before = __ref_doc.get('advance_paid') or 0 %}
                                            {% set __advance_paid_after = __advance_paid_before + ref.allocated_amount %}
                                            {% set __outstanding_before = (__grand_total - __advance_paid_before) if __grand_total is not none else none %}
                                            {% set __outstanding_after = (__grand_total - __advance_paid_after) if __grand_total is not none else none %}
                                        {% else %}
                                            {% set __outstanding_amount = __ref_doc.get('outstanding_amount') %}
                                            {% set __outstanding_before = (__outstanding_amount + ref.allocated_amount) if __outstanding_amount is not none else none %}
                                            {% set __outstanding_after = __outstanding_amount %}
                                        {% endif %}
                                        
                                        <td class="right">{% if __outstanding_before is not none %}{{ frappe.utils.fmt_money(__outstanding_before, currency=(doc.paid_to_account_currency or doc.company_currency)) }}{% else %}—{% endif %}</td>
                                        <td class="right">{% if __outstanding_after is not none %}{{ frappe.utils.fmt_money(__outstanding_after, currency=(doc.paid_to_account_currency or doc.company_currency)) }}{% else %}—{% endif %}</td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </section>
                {% endif %}

                <!-- Deduções / Retenções -->
                {% if doc.deductions or doc.get('difference_amount') %}
                <section>
                    <h4 class="muted">{{ _("Retenções e Outras Deduções") }}</h4>
                    <div class="hr" aria-hidden="true"></div>
                    <table class="items" role="table">
                        <thead>
                            <tr>
                                <th class="left">{{ _("Conta") }}</th>
                                <th class="right">{{ _("Descrição") }}</th>
                                <th class="right">{{ _("Valor") }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for d in doc.deductions %}
                            <tr>
                                <td class="left">{{ d.account }}</td>
                                <td class="right">{{ d.description or '' }}</td>
                                <td class="right">{{ d.get_formatted('amount', doc) }}</td>
                            </tr>
                            {% endfor %}
                            {% if doc.get('difference_amount') %}
                            <tr>
                                <td class="left">—</td>
                                <td class="right">{{ _("Diferença") }}</td>
                                <td class="right">{{ doc.get_formatted('difference_amount', doc) }}</td>
                            </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </section>
                {% endif %}

                <!-- Disclaimer -->
                <section>
                    <div class="text-left">
                        <div class="disclaimer">{{ _("Comprovativo de pagamento. Não substitui a factura para efeitos fiscais (CIVA).") }}</div>
                    </div>
                </section>

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

                <!-- Meta cards -->
                <table class="meta avoid-break" aria-label="Detalhes do Lançamento">
                  <tr>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DETALHES DO LANÇAMENTO</h3>
                        <p>{{ _("Tipo") }}: <span>{{ doc.voucher_type }}</span></p>
                        {% if doc.cheque_no %}<p>{{ _("Nº Cheque") }}: <span>{{ doc.cheque_no }}</span></p>{% endif %}
                        {% if doc.cheque_date %}<p>{{ _("Data Cheque") }}: <span>{{ frappe.utils.format_date(doc.cheque_date) }}</span></p>{% endif %}
                      </section>
                    </td>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DETALHES DO DOCUMENTO</h3>
                        {% set __dt = (doc.get('posting_date') and (doc.posting_date ~ " " ~ (doc.get('posting_time') or "00:00:00")))
                            or (doc.get('transaction_date') and (doc.transaction_date ~ " 00:00:00"))
                            or doc.creation %}
                        <p>{{ _("Data") }}: <span>{{ frappe.utils.format_datetime(__dt) }}</span></p>
                        <p>{{ _("Total Débito") }}: <span>{{ doc.get_formatted('total_debit', doc) }}</span></p>
                        <p>{{ _("Total Crédito") }}: <span>{{ doc.get_formatted('total_credit', doc) }}</span></p>
                      </section>
                    </td>
                  </tr>
                </table>

                <div class="hr" aria-hidden="true"></div>

                <!-- Accounts table -->
                <section aria-label="Contas">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Conta") }}</th>
                        <th scope="col" class="right">{{ _("Centro de Custo") }}</th>
                        <th scope="col" class="right">{{ _("Débito") }}</th>
                        <th scope="col" class="right">{{ _("Crédito") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for account in doc.accounts %}
                      <tr>
                        <td>{{ account.account }}</td>
                        <td class="right">{{ account.cost_center or '' }}</td>
                        <td class="right">{% if account.debit %}{{ account.get_formatted('debit', doc) }}{% endif %}</td>
                        <td class="right">{% if account.credit %}{{ account.get_formatted('credit', doc) }}{% endif %}</td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </section>

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

                <!-- Meta cards -->
                <table class="meta avoid-break" aria-label="Funcionário e Período">
                  <tr>
                    <td>
                      <section class="card">
                        <h3 class="card-title">DADOS DO FUNCIONÁRIO</h3>
                        <p><strong>{{ doc.employee_name }}</strong></p>
                        <p>{{ _("Nº Funcionário") }}: <span>{{ doc.employee }}</span></p>
                        {% if doc.designation %}<p>{{ _("Cargo") }}: <span>{{ doc.designation }}</span></p>{% endif %}
                        {% if doc.department %}<p>{{ _("Departamento") }}: <span>{{ doc.department }}</span></p>{% endif %}
                      </section>
                    </td>
                    <td>
                      <section class="card">
                        <h3 class="card-title">PERÍODO</h3>
                        <p>{{ _("De") }}: <span>{{ frappe.utils.format_date(doc.start_date) }}</span></p>
                        <p>{{ _("Até") }}: <span>{{ frappe.utils.format_date(doc.end_date) }}</span></p>
                        <p>{{ _("Dias Trabalhados") }}: <span>{{ doc.payment_days }}</span></p>
                      </section>
                    </td>
                  </tr>
                </table>

                <div class="hr" aria-hidden="true"></div>

                {% if doc.earnings %}
                <section aria-label="Vencimentos">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Descrição") }}</th>
                        <th scope="col" class="right">{{ _("Dias/Horas") }}</th>
                        <th scope="col" class="right">{{ _("Taxa") }}</th>
                        <th scope="col" class="right">{{ _("Valor") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for earning in doc.earnings %}
                      <tr>
                        <td>{{ earning.salary_component }}</td>
                        <td class="right">{% if earning.amount %}{{ earning.get_formatted('amount', doc) }}{% endif %}</td>
                        <td class="right">{% if earning.default_amount %}{{ earning.get_formatted('default_amount', doc) }}{% endif %}</td>
                        <td class="right">{{ earning.get_formatted('amount', doc) }}</td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </section>
                {% endif %}

                {% if doc.deductions %}
                <section aria-label="Descontos">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Descrição") }}</th>
                        <th scope="col" class="right">{{ _("Valor") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for deduction in doc.deductions %}
                      <tr>
                        <td>{{ deduction.salary_component }}</td>
                        <td class="right">{{ deduction.get_formatted('amount', doc) }}</td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </section>
                {% endif %}

                <!-- Totals as mockup totals-terms -->
                <table class="totals-terms avoid-break" aria-label="Totais">
                  <tr>
                    <td></td>
                    <td class="right" style="width:62mm;">
                      <aside class="totals" aria-label="Resumo de valores">
                        <div class="row"><span>{{ _("Total Vencimentos") }}</span><span>{{ doc.get_formatted('gross_pay', doc) }}</span></div>
                        <div class="row"><span>{{ _("Total Descontos") }}</span><span>{{ doc.get_formatted('total_deduction', doc) }}</span></div>
                        <div class="row total"><span>{{ _("TOTAL") }}</span><span>{{ doc.get_formatted('net_pay', doc) }}</span></div>
                      </aside>
                    </td>
                  </tr>
                </table>

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

                <table class="meta avoid-break" aria-label="Cliente">
                  <tr>
                    <td>
                      <section class="card">
                        <h3 class="card-title">INFORMAÇÕES GERAIS</h3>
                        <p><strong>{{ doc.customer_name }}</strong></p>
                        {% if doc.tax_id %}<p>NUIT: <span>{{ doc.tax_id }}</span></p>{% endif %}
                        {% if doc.customer_type %}<p>{{ _("Tipo") }}: <span>{{ doc.customer_type }}</span></p>{% endif %}
                        {% if doc.territory %}<p>{{ _("Território") }}: <span>{{ doc.territory }}</span></p>{% endif %}
                      </section>
                    </td>
                    <td>
                      <section class="card">
                        <h3 class="card-title">CONTACTOS</h3>
                        {% if doc.mobile_no %}<p>{{ _("Telemóvel") }}: <span>{{ doc.mobile_no }}</span></p>{% endif %}
                        {% if doc.email_id %}<p>{{ _("Email") }}: <span>{{ doc.email_id }}</span></p>{% endif %}
                        {% if doc.website %}<p>{{ _("Website") }}: <span>{{ doc.website }}</span></p>{% endif %}
                      </section>
                    </td>
                  </tr>
                </table>

                <div class="hr" aria-hidden="true"></div>

                {% if doc.customer_primary_address %}
                <section aria-label="Endereço">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Endereço Principal") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{{ doc.customer_primary_address }}</td>
                      </tr>
                    </tbody>
                  </table>
                </section>
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

                <table class="meta avoid-break" aria-label="Fornecedor">
                  <tr>
                    <td>
                      <section class="card">
                        <h3 class="card-title">INFORMAÇÕES GERAIS</h3>
                        <p><strong>{{ doc.supplier_name }}</strong></p>
                        {% if doc.tax_id %}<p>NUIT: <span>{{ doc.tax_id }}</span></p>{% endif %}
                        {% if doc.supplier_type %}<p>{{ _("Tipo") }}: <span>{{ doc.supplier_type }}</span></p>{% endif %}
                        {% if doc.country %}<p>{{ _("País") }}: <span>{{ doc.country }}</span></p>{% endif %}
                      </section>
                    </td>
                    <td>
                      <section class="card">
                        <h3 class="card-title">CONTACTOS</h3>
                        {% if doc.mobile_no %}<p>{{ _("Telemóvel") }}: <span>{{ doc.mobile_no }}</span></p>{% endif %}
                        {% if doc.email_id %}<p>{{ _("Email") }}: <span>{{ doc.email_id }}</span></p>{% endif %}
                        {% if doc.website %}<p>{{ _("Website") }}: <span>{{ doc.website }}</span></p>{% endif %}
                      </section>
                    </td>
                  </tr>
                </table>

                <div class="hr" aria-hidden="true"></div>

                {% if doc.supplier_primary_address %}
                <section aria-label="Endereço">
                  <table class="items" role="table">
                    <thead>
                      <tr>
                        <th scope="col">{{ _("Endereço Principal") }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{{ doc.supplier_primary_address }}</td>
                      </tr>
                    </tbody>
                  </table>
                </section>
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
        
        sales_invoice_return = SalesInvoiceReturnPrintFormat()
        formats_created.append(sales_invoice_return.create_print_format())
        
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