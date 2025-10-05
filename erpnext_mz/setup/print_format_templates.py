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
    
    def __init__(self, doc_type, format_name, module="Accounts"):
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
                "font": "Montserrat",
                "font_size": 10,
                "margin_top": 10.0,
                "margin_bottom": 10.0,
                "margin_left": 10.0,
                "margin_right": 10.0,
                "align_labels_right": 0,
                "show_section_headings": 1,
                "line_breaks": 0,
                "absolute_value": 0,
                "page_number": "Bottom Center",
                "default_print_language": "pt-MZ",
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

        /* ==========================
        Root tokens & basic reset
        ========================== */
        :root {
            --ink: #111;
            --muted: #444;
            --line: #111;
            --paper: #fff;
            --gutter: 18mm;
            --lh-tight: 1.1;
            --lh-base: 1.35;
            --fs-09: 9pt;
            --fs-10: 10pt;
            --fs-11: 11pt;
            --fs-12: 12pt;
            --fs-14: 14pt;
            --fs-16: 16pt;
            --fs-20: 20pt;
        }

        *,
        *::before,
        *::after {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            color: var(--ink);
            background: #f7f7f7;
            font-family: "Montserrat", system-ui, -apple-system, Segoe UI, Roboto, Cantarell, Noto Sans, sans-serif;
            line-height: var(--lh-base);
        }

        /* ==========================
        Page box (A4)
        ========================== */
        .page {
            width: 210mm;
            min-height: 297mm;
            margin: 10mm auto;
            background: var(--paper);
            color: var(--ink);
            padding: var(--gutter);
            position: relative;
            display: block;
            border: 0.2mm solid rgba(0, 0, 0, .08);
        }

        /* Print rules */
        @media print {
            @page {
                size: A4;
                margin: 12mm;
            }

            body {
                background: var(--paper);
            }

            .page {
                margin: 0;
                border: none;
            }

            a[href^="mailto:"],
            a[href^="http"] {
                text-decoration: none;
                color: inherit;
            }
        }

        /* ==========================
        Utilities
        ========================== */
        .small { font-size: var(--fs-09); letter-spacing: .08em; }
        .tight { margin: 0; }
        .right { text-align: right; }
        .center { text-align: center; }
        .caps { text-transform: uppercase; letter-spacing: .14em; }
        .muted { color: var(--muted); }
        .hr { height: 0.25mm; background: #000; margin: 3mm 0; }
        .avoid-break { page-break-inside: avoid; break-inside: avoid; }

        /* ==========================
        Header (two columns via table)
        ========================== */
        .hdr { width: 100%; border-collapse: collapse; }
        .hdr td { vertical-align: top; }
        .brand { display: inline-block; }
        .logo-mark {
            width: 10mm; height: 10mm; border-radius: 1.8mm; background: #0bbf84;
            display: inline-block; vertical-align: middle; margin-right: 3mm;
        }
        .brand h1 { display: inline-block; vertical-align: middle; margin: 0; font-weight: 700; font-size: var(--fs-14); letter-spacing: .02em; line-height: var(--lh-tight); }
        .brand h1 span { font-weight: 300; margin-left: 1mm; }
        .company-name { font-size: var(--fs-16); font-weight: 700; letter-spacing: .08em; margin-bottom:1mm; text-transform: uppercase; line-height: var(--lh-tight); }
        .company-meta { font-size: var(--fs-09); letter-spacing: .18em; }
        .nuit { margin-top: 2mm; font-size: var(--fs-09); letter-spacing: .18em; }

        /* ==========================
        Title / Doc number
        ========================== */
        .title-block { text-align: right; }
        .title { font-size: var(--fs-20); font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin: 0 0 0.5mm; }
        .doc-no { font-size: var(--fs-12); font-weight: 600; letter-spacing: .10em; }

        /* ==========================
        Meta cards (two columns via table)
        ========================== */
        .meta { width: 100%; border-collapse: separate; border-spacing: 0 0; margin-top: 3mm; }
        .meta td { width: 50%; vertical-align: top; padding: 0; }
        .card-title { font-size: var(--fs-09); font-weight: 700; text-transform: uppercase; letter-spacing: .14em; margin: 0 0 2mm; }
        .card p { margin: 0 0 1.2mm; font-size: var(--fs-10); }
        .card address { font-style: normal; font-size: var(--fs-10); line-height: 1.5; }

        /* ==========================
        Items table
        ========================== */
        table.items { width: 100%; border-collapse: collapse; }
        table.items thead th { font-size: var(--fs-10); font-weight: 700; letter-spacing: .12em; text-transform: uppercase; padding: 3.2mm 2.5mm; text-align: left; border-bottom: 0.6mm solid var(--line); }
        table.items thead th.right { text-align: right; }
        table.items tbody td { font-size: var(--fs-10); padding: 3.2mm 2.5mm; border-bottom: 0.25mm solid rgba(0, 0, 0, .25); vertical-align: top; word-wrap: break-word; word-break: break-word; }
        table.items tbody td.right { text-align: right; }
        table.items thead { display: table-header-group; }
        table.items tfoot { display: table-footer-group; }
        table.items tr { page-break-inside: avoid; }

        /* ==========================
        Totals & terms
        ========================== */
        .totals-terms { width: 100%; margin-top: 1.5mm; border-collapse: collapse; }
        .totals-terms td { vertical-align: top; }
        .terms { margin-top: 1.5mm; }
        .terms .lead { font-size: var(--fs-10); font-weight: 700; letter-spacing: .14em; text-transform: uppercase; margin: 0 0 2mm; }
        .terms p { margin: 0; font-size: var(--fs-10); }
        .disclaimer { font-size: var(--fs-09); margin-top: 3mm; color: var(--ink); }
        .totals { width: 60mm; margin-left: auto; }
        .totals .row { display: table; width: 100%; border-collapse: collapse; font-size: var(--fs-11); padding: 0; margin: 1.5mm 0; }
        .totals .row>span { display: table-cell; }
        .totals .row>span:last-child { text-align: right; }
        .totals .row.total { font-weight: 700; font-size: var(--fs-11); border-top: 0.6mm solid var(--ink); border-top: 0.6mm solid var(--line); padding-top: 2mm; margin-top: 2mm; }

        /* ==========================
        QR / Payment area
        ========================== */
        .qr-wrap { margin: 7mm auto 0; text-align: center; }
        .qr { width: 20mm; height: 20mm; display: inline-block; }
        .qr-caption { font-size: var(--fs-09); font-style: italic; margin-top: 1mm; color: var(--muted); }

        /* ==========================
        Footer
        ========================== */
        footer { margin-top: auto; }
        .footline { height: 0.6mm; background: var(--line); margin: 6mm 0 3mm; }
        .foot { text-align: center; font-size: var(--fs-10); color: var(--ink); }
        .foot .sub { font-size: var(--fs-09); color: var(--muted); margin-top: 1mm; }

        /* Screen responsiveness (non‑print preview only) */
        @media screen and (max-width: 900px) {
            .page { width: 100%; min-height: auto; padding: 10mm; }
        }
    """

    def get_common_header_macro(self, document_title):
        return """
        {%- macro add_header(page_num, max_pages, doc, letter_head, no_letterhead, footer, print_settings=none, print_heading_template=none) -%}
            {% if letter_head and not no_letterhead %}
                <div class="letter-head">{{ letter_head }}</div>
            {% endif %}
            <section class="title-block avoid-break" >
                <h2 class="title">""" + document_title + """</h2>
                <div class="doc-no">{{ doc.name }}</div>
            </section>
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
        <section class=\"qr-wrap center avoid-break\">
          {% set qr_code_img = get_qr_image(doc.doctype, doc.name) %}
          {% if qr_code_img and qr_code_img.strip() %}
            <img class=\"qr\" src=\"data:image/png;base64,{{ qr_code_img }}\" alt=\"QR\"/>
            <div class=\"qr-caption\">{{ _("Escaneie o QR para verificar a autenticidade") }}</div>
          {% endif %}
        </section>
    """

    def get_meta_cards_section(self, customer_field="customer", customer_name_field="customer_name", left_label: str | None = None):
        """Meta cards (mockup) for party and document details"""
        left_title = left_label or "FACTURAR PARA"
        return """
            <table class=\"meta avoid-break\">
              <tr>
                <td>
                  <section class=\"card\">
                    <h3 id=\"billto\" class=\"card-title\">""" + left_title + """</h3>
                    <p><strong>{{ doc.""" + customer_name_field + """ or doc.""" + customer_field + """ }}</strong></p>
                    <address>
                      {% if doc.address_display %}
                      {% set __address_display = doc.address_display 
                            | replace("<br>", ", ")
                            | replace("<br/>", ", ")
                            | replace("\n", "")
                        %}
                        {{ __address_display }} <br/>
                      {% endif %}
                      {% if doc.tax_id %}
                        {{ _("NUIT") }}: {{ doc.tax_id }}
                      {% else %}
                        {% if doc.""" + customer_field + """ %}
                          {% set __party_doctype = doc.meta.get_field('""" + customer_field + """').options or 'Customer' %}
                          {% set __party_nuit = frappe.db.get_value(__party_doctype, doc.""" + customer_field + """, 'tax_id') %}
                          {% if __party_nuit %}
                            {{ _("NUIT") }}: {{ __party_nuit }}
                          {% endif %}
                        {% endif %}
                      {% endif %}
                    </address>
                  </section>
                </td>
                <td>
                  <section class=\"card\">
                    <h3 id=\"detalhes\" class=\"card-title\">{{ _("Detalhes do Documento") }}</h3>
                    {% set __dt = (doc.posting_date and (doc.posting_date ~ " " ~ (doc.posting_time or "00:00:00")))
                        or (doc.transaction_date and (doc.transaction_date ~ " 00:00:00"))
                        or doc.creation %}
                    <p>{{ _("Data de Emissão") }}: <span>{{ frappe.utils.format_datetime(__dt) }}</span></p>
                    {% if doc.due_date %}
                    <p>{{ _("Vencimento") }}: <span>{{ frappe.utils.format_date(doc.due_date) }}</span></p>
                    {% endif %}
                    {% if doc.po_no %}
                    <p>{{ _("Nº Encomenda") }}: <span>{{ doc.po_no }}</span></p>
                    {% endif %}
                    {% if doc.currency %}
                    <p>{{ _("Moeda") }}: <span>{{ doc.currency }}</span></p>
                    {% endif %}
                    {% if doc.currency and doc.company_currency and doc.currency != doc.company_currency and doc.conversion_rate %}
                    <p>{{ _("Taxa de câmbio") }}: <span>1 {{ doc.currency }} = {{ doc.conversion_rate }} {{ doc.company_currency }}</span></p>
                    {% endif %}
                    {% if doc.return_against %}
                    <p>{{ _("Referência à Factura Original") }}: <span>{{ doc.return_against }}</span></p>
                    {% endif %}
                    {% if doc.is_return %}
                    <p>{{ _("Tipo de Crédito") }}: <span>{{ _("Devolução de Bens/Serviços") }}</span></p>
                    {% endif %}
                  </section>
                </td>
              </tr>
            </table>
        """
    def get_meta_cards_delivery_note_section(self, customer_field="customer", customer_name_field="customer_name", left_label: str | None = None):
        """Meta cards (mockup) for party and document details"""
        left_title = left_label or "Destino"
        return """
            <table class=\"meta avoid-break\">
                <tr>
                    <td>
                        <section class=\"card\">
                            <h3 id=\"billto\" class=\"card-title\">""" + left_title + """</h3>
                            <p><strong>{{ doc.""" + customer_name_field + """ or doc.""" + customer_field + """ }}</strong></p>
                            {% if doc.tax_id %}
                                {{ _("NUIT") }}: {{ doc.tax_id }}
                            {% else %}
                                {% if doc.""" + customer_field + """ %}
                                    {% set __party_doctype = doc.meta.get_field('""" + customer_field + """').options or 'Customer' %}
                                    {% set __party_nuit = frappe.db.get_value(__party_doctype, doc.""" + customer_field + """, 'tax_id') %}
                                    {% if __party_nuit %}
                                        {{ _("NUIT") }}: {{ __party_nuit }}
                                    {% endif %}
                                {% endif %}
                            {% endif %}
                            {% if doc.shipping_address_display %}
                                <address>
                                {{ _("Endereço de Entrega") }}: <span>
                                {% set __address_display = doc.shipping_address_display 
                                    | replace("<br>", ", ")
                                    | replace("<br/>", ", ")
                                    | replace("\n", " ")
                                %}
                                {{ __address_display }} <br/>
                                </span>
                                </address>
                            {% endif %}
                        </section>
                    </td>
                    <td>
                        <section class=\"card\">
                            <h3 id=\"detalhes\" class=\"card-title\">{{ _("Detalhes do Documento") }}</h3>
                            {% set __dt = (doc.posting_date and (doc.posting_date ~ " " ~ (doc.posting_time or "00:00:00")))
                                or (doc.transaction_date and (doc.transaction_date ~ " 00:00:00"))
                                or doc.creation %}
                            <p>{{ _("Data de Saída") }}: <span>{{ frappe.utils.format_datetime(__dt) }}</span></p>
                            {% if doc.po_no %}
                                <p>{{ _("Nº Encomenda") }}: <span>{{ doc.po_no }}</span></p>
                            {% endif %}
                            {% if doc.currency %}
                                <p>{{ _("Moeda") }}: <span>{{ doc.currency }}</span></p>
                            {% endif %}
                            {% if doc.transporter_name or doc.transporter %}
                                <p>{{ _("Transportadora") }}: <span>{{ doc.transporter_name or doc.transporter }}</span></p>
                            {% endif %}
                            {% if doc.vehicle_no %}
                                <p>{{ _("Matrícula") }}: <span>{{ doc.vehicle_no }}</span></p>
                            {% endif %}
                            {% if doc.driver_name or doc.driver %}
                                <p>{{ _("Motorista") }}: <span>{{ doc.driver_name or doc.driver }}</span></p>
                            {% endif %}
                            {% if doc.lr_no %}
                                <p>{{ _("Documento Transporte") }}: <span>{{ doc.lr_no }}</span></p>
                            {% endif %}
                        </section>
                    </td>
                </tr>
            </table>
        """

    def get_meta_cards_payment_entry_section(self, left_label: str | None = None):
        """Meta cards (mockup) for party and document details"""
        left_title = left_label or "Detalhes do Pagamento"
        return """
            <table class=\"meta avoid-break\">
                <tr>
                    <td>
                        <section class=\"card\">
                            <h3 id=\"billto\" class=\"card-title\">""" + left_title + """</h3>
                            <p><strong>{{ _("Tipo") }}:</strong> {{ doc.payment_type }}</p>
                            <p><strong>{{ _("Modo") }}:</strong> {{ doc.mode_of_payment }}</p>
                            {% if doc.party %}
                                {% set __party_label = (doc.party_type=="Customer" and _("Cliente")) or (doc.party_type=="Supplier" and _("Fornecedor")) or _("Parte") %}
                                <p><strong>{{ __party_label }}:</strong> {{ doc.party_name or doc.party }}</p>
                                {% set __party_nuit = frappe.db.get_value(doc.party_type, doc.party, 'tax_id') %}
                                {% if __party_nuit %}
                                    <p><strong>{{ _("NUIT") }}:</strong> {{ __party_nuit }}</p>
                                {% endif %}
                            {% endif %}
                            {% if doc.paid_from %}
                                <p><strong>{{ _("Conta Origem") }}:</strong> {{ doc.paid_from }}</p>
                            {% endif %}
                            {% if doc.paid_to %}
                                <p><strong>{{ _("Conta Destino") }}:</strong> {{ doc.paid_to }}</p>
                            {% endif %}
                            {% if doc.reference_no %}
                                <p><strong>{{ _("Ref. Nº") }}:</strong> {{ doc.reference_no }}</p>
                            {% endif %}
                            {% if doc.reference_date %}
                                <p><strong>{{ _("Data da Referência") }}:</strong> {{ frappe.utils.format_date(doc.reference_date) }}</p>
                            {% endif %}
                            {% set __dt = (doc.posting_date and (doc.posting_date ~ " " ~ (doc.posting_time or "00:00:00")))
                                or (doc.transaction_date and (doc.transaction_date ~ " 00:00:00"))
                                or doc.creation %}
                            <p><strong>{{ _("Data do Pagamento") }}:</strong> {{ frappe.utils.format_datetime(__dt) }}</p>
                            {% if doc.clearance_date %}
                                <p><strong>{{ _("Data de Compensação") }}:</strong> {{ frappe.utils.format_date(doc.clearance_date) }}</p>
                            {% endif %}
                        </section>
                    </td>
                    <td>
                        <section class=\"card\">
                            <h3 id=\"detalhes\" class=\"card-title\">{{ _("Valores") }}</h3>
                            <p>{{_("Valor pago (origem)") }} [{{ doc.paid_from_account_currency or doc.company_currency }}]: <span>{{ frappe.utils.fmt_money(doc.total_allocated_amount, currency=(doc.paid_from_account_currency or doc.company_currency)) }}</span></p>
                            {% if doc.received_amount %}
                                <p>{{_("Valor recebido (destino)") }} [{{ doc.paid_to_account_currency or doc.company_currency }}]: <span>{{ frappe.utils.fmt_money(doc.total_allocated_amount, currency=(doc.paid_to_account_currency or doc.company_currency)) }}</span></p>
                            {% endif %}
                            {% if doc.paid_from_account_currency and doc.paid_to_account_currency and doc.paid_from_account_currency != doc.paid_to_account_currency %}
                                {% set __fx = doc.get('target_exchange_rate') or 0 %}
                                {% if __fx %}
                                    <p>{{ _("Taxa de câmbio") }}: <span>1 {{ doc.paid_from_account_currency }} = {{ __fx }} {{ doc.paid_to_account_currency }}</span></p>
                                {% endif %}
                            {% endif %}
                            {% if doc.currency %}
                                <p>{{ _("Moeda") }}: <span>{{ doc.currency }}</span></p>
                            {% endif %}
                        </section>
                    </td>
                </tr>
            </table>
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
                ("DESCRIÇÃO", "left", """
                    <strong>{{ item.item_code }}</strong><br>
                    {% if item.item_name != item.item_code %}
                        <br><em>{{ item.item_name }}</em>
                    {% endif %}
                    {% if item.description and item.description != item.item_name %}
                        <br><em>{{ item.description }}</em>
                    {% endif %}
                    {% if item.serial_no %}
                        <br><small><strong>{{ _("Nº de Série") }}:</strong> {{ item.serial_no }}</small>
                    {% endif %}
                """),
                ("QTD", "right", "{{ item.get_formatted('qty', doc) }}"),
                ("U.M.", "right", "{{ item.get_formatted('uom', doc) }}"),
                ("PREÇO", "right", "{{ item.get_formatted('net_rate', doc) }}"),
                ("IVA %", "right", self.get_item_tax_rate_jinja()),
                ("TOTAL ILÍQUIDO", "right", "{{ item.get_formatted('net_amount', doc) }}")
            ]
        
        header_html = ""
        for col_name, col_class, _ in custom_columns:
            header_html += '<th scope="col" class="' + col_class + '">{{ _("' + col_name + '") }}</th>\n                    '
        
        body_html = ""
        for col_name, col_class, col_template in custom_columns:
            body_html += '<td class="' + col_class + '">' + col_template + '</td>\n                    '
        
        return """
            <!-- Items Table Section -->
            <div class="hr" aria-hidden="true"></div>
            <section>
                <table class="items" role="table">
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
            </section>
        """

    def get_totals_section(self, totals_fields=None):
        """Common totals section (safe on doctypes without those fields)
        
        Args:
            totals_fields: List of tuples with (field_name, label) or (field_name, label, always_show)
                          where always_show=True means the field will be displayed even if zero
        """
        if totals_fields is None:
            totals_fields = [
                ("net_total", "Sub-Total"),
                ("grand_total", "TOTAL", True)
            ]

        rows = []
        for field_data in totals_fields:
            if len(field_data) == 2:
                field, label = field_data
                always_show = False
            else:
                field, label, always_show = field_data
            
            if field == "tax_amount":
                rows.append("""
                    {% for tax in doc.taxes %}
                        {% if tax.tax_amount or """ + str(always_show).lower() + """ %}
                        <div class="row">
                            <span>{{ _(tax.description) }}</span><span>{{ tax.get_formatted("tax_amount", doc) }}</span>
                        </div>
                        {% endif %}
                    {% endfor %}
                """)
                continue

            if always_show:
                condition = f"doc.get('{field}') is not none"
            else:
                condition = f"doc.get('{field}')"

            row_class = "row total" if field == "grand_total" else "row"
            rows.append(f"""
            {{% if {condition} %}}
              <div class=\"{row_class}\"><span>{label}</span><span>{{{{ doc.get_formatted('{field}', doc) }}}}</span></div>
            {{% endif %}}
            """)

        totals_html = "".join(rows)

        return f"""
        <table class=\"totals-terms avoid-break\">
            <tr>
                <td>
                    <aside class=\"terms\">
                        {{% if doc.get('terms') %}}
                            <div class=\"lead\">{{{{ _("TERMOS E CONDIÇÕES") }}}}</div>
                            <p>{{{{ doc.terms }}}}</p>
                        {{% endif %}}
                    </aside>
                </td>
                <td class=\"right\" style=\"width:62mm;\">
                    <aside class=\"totals\">
                        {totals_html}
                    </aside>
                </td>
            </tr>
        </table>
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