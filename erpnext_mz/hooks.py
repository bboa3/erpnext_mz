# -*- coding: utf-8 -*-
"""
Hooks for ERPNext Mozambique Custom App

This file defines all the integration points between the custom app
and ERPNext core functionality.
"""

# App configuration
app_name = "erpnext_mz"
app_title = "ERPNext Moçambique"
app_publisher = "MozEconomia, SA"
app_description = f"""
Aplicação Personalizada ERPNext MZ
Esta aplicação fornece funcionalidades específicas para Moçambique em conformidade fiscal, contabilidade e RH:
- Plano de Contas alinhado às IFRS
- Modelos de IVA (16%, 5%, 0%)
- Cálculos de INSS e IRPS
- Geração de XML SAF-T
- Integração com a AT (Autoridade Tributária)
- Gestão de benefícios em espécie
- Validações de conformidade e relatórios
"""
app_email = "contacto@mozeconomia.co.mz"
app_license = "MIT"
app_version = "1.0.0"
# DocType Registrations
doctype_js = {
    # add client scripts later if needed
}


# Install/Migrate hooks
after_install = "erpnext_mz.setup.after_install"
after_migrate = "erpnext_mz.setup.after_migrate"

# No fixtures are required; setup.py creates custom fields and print formats idempotently.

# DocType events
doc_events = {
    "Sales Invoice": {
        "before_submit": "erpnext_mz.modules.tax_compliance.fiscal.assign_fiscal_number",
        "on_submit": "erpnext_mz.modules.tax_compliance.at_integration.transmit_to_at",
        "on_cancel": "erpnext_mz.modules.tax_compliance.at_integration.handle_cancellation",
    },
}

# Ensure the HR module group exists on the Desk. Some stacks show a modal error if missing.
desk_sidebar = [
    {
        "module": "HR",
        "hidden": 0,
    }
]

# Custom fields will be created via setup.py
# This is the correct way to handle custom fields in Frappe

# Print formats will be created via setup.py
# This is the correct way to handle print formats in Frappe

# Server scripts will be created via setup.py
# This is the correct way to handle server scripts in Frappe

# Permissions
has_permission = {
    "Sales Invoice": "erpnext_mz.permissions.has_sales_invoice_permission",
    "Payroll Entry": "erpnext_mz.permissions.has_payroll_permission"
}

# Avoid overriding global whitelisted methods like frappe.client.get_list to prevent
# unintended recursion and side-effects across the UI.

# Scheduled tasks
scheduler_events = {
    "cron": {
        # Daily compliance at 01:15
        "15 1 * * *": [
            "erpnext_mz.tasks.daily_compliance_check"
        ],
        # SAF-T generation at 02:15 on day 1 of month
        "15 2 1 * *": [
            "erpnext_mz.tasks.monthly_saf_t_generation"
        ],
    }
}

# API modules expose their own whitelisted methods; no hook registration required.

# Show on the app selection screen
add_to_apps_screen = [
    {
        "name": "erpnext_mz",
        "logo": "/assets/erpnext/images/erpnext-logo.svg",
        "title": "ERPNext Mozambique",
        "route": "/app/erpnext-mozambique",
    }
]

# Provide minimal Desk module map to avoid missing module popups
modules = {
    "HR": {
        "color": "blue",
        "icon": "octicon octicon-organization",
        "label": "HR",
    },
    "HR and Payroll": {
        "color": "blue",
        "icon": "octicon octicon-organization",
        "label": "HR and Payroll",
    },
}
