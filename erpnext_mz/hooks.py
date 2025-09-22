# App configuration
app_name = "erpnext_mz"
app_title = "MozEconomia Cloud"
app_publisher = "MozEconomia, SA"
app_description = f"""
Aplicação Personalizada MozEconomia Cloud
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
app_license = "mit"
app_version = "1.0.0"
app_logo_url = "/assets/erpnext_mz/images/logo180.png"
app_icon = "/assets/erpnext_mz/images/icon.svg"
app_color = "#02664D"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "erpnext_mz",
		"logo": "/assets/erpnext_mz/images/logo180.png",
		"title": "ERPNext MZ",
		"route": "/app/home"
#		"has_permission": "erpnext_mz.api.permission.has_app_permission"
	}
]

fixtures = [
  "Workspace",
  "Number Card",
  "Property Setter",
  #"Document Naming Settings",
  #"Document Naming Rule",
  "Client Script",
  #"Payroll Settings",
  "Custom Field",
  #"MZ Company Setup",
  #"QR Code"
]

website_context = {
    "favicon": "/assets/erpnext_mz/images/favicon.ico",
    "brand_image": "/assets/erpnext_mz/images/logo180.png",
    "brand_image_alt": "MozEconomia Cloud",
    "splash_image": "/assets/erpnext_mz/images/icon.svg",
}

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/erpnext_mz/css/erpnext_mz.css"
app_include_js = [
    "/assets/erpnext_mz/js/mz_onboarding.js",
]

# include js, css files in header of web template
web_include_css = "/assets/erpnext_mz/css/erpnext_mz.css"
# web_include_js = "/assets/erpnext_mz/js/erpnext_mz.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_mz/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpnext_mz/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods to jinja environment for print formats
jinja = {
    "methods": "erpnext_mz.utils.jinja",
}

# Installation
# ------------

# before_install = "erpnext_mz.install.before_install"
after_install = "erpnext_mz.install.after_install"
after_migrate = "erpnext_mz.install.after_migrate"

# Setup Wizard Complete
# ---------------------
# Trigger onboarding after setup wizard is completed
setup_wizard_complete = "erpnext_mz.setup.onboarding.trigger_onboarding_after_setup"

# Uninstallation
# ------------

# before_uninstall = "erpnext_mz.uninstall.before_uninstall"
# after_uninstall = "erpnext_mz.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpnext_mz.utils.before_app_install"
# after_app_install = "erpnext_mz.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpnext_mz.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_mz.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_mz.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Company": "erpnext_mz.overrides.company.Company",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Company": {
		"after_insert": "erpnext_mz.overrides.company.ensure_mz_coa_seeded",
		"on_update": "erpnext_mz.overrides.company.ensure_mz_coa_seeded",
	},
	"Sales Invoice": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
	"Purchase Invoice": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
	"Sales Order": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
	"Purchase Order": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
	"Delivery Note": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
	"Purchase Receipt": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
  "Payment Entry": {
		"on_submit": "erpnext_mz.qr_code.qr_generator.generate_document_qr_code",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_mz.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_mz.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_mz.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_mz.tasks.weekly"
# 	],
# 	"monthly": [
# 		"erpnext_mz.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "erpnext_mz.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_mz.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_mz.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

#################################
# Request Events
# ----------------
# Enforce pt-MZ language for Guest (login and other guest pages)
before_request = [
    "erpnext_mz.utils.web.enforce_guest_language",
]

# Job Events
# ----------
# before_job = ["erpnext_mz.utils.before_job"]
# after_job = ["erpnext_mz.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"erpnext_mz.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

default_mail_footer = """
  <div>
  Enviado via <a style="color: #02664D;" href="https://mozeconomia.co.mz" target="_blank">MozEconomia Cloud</a>
  </div>
"""

portal_menu_items = [
    {"title": "Painel", "route": "/dashboard", "role": "Customer"},
    {"title": "Pedidos", "route": "/orders", "role": "Customer"},
    {"title": "Sobre Nós", "route": "/about", "role": "Customer"},
    {"title": "Contacto", "route": "/contact", "role": "Customer"},
]

translated_languages_for_website = [
    {"language": "pt-MZ", "name": "Português (Moçambique)"},
    {"language": "pt", "name": "Português"},
    {"language": "en", "name": "English"},
]

# Boot Session: expose onboarding status
boot_session = "erpnext_mz.setup.boot.boot_session"
