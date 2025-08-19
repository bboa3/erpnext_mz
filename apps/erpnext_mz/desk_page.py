from frappe import _
import frappe

@frappe.whitelist()
def get_app_page():
	# Minimal placeholder page route handler; the Workspace handles UI.
	return {
		"title": _("ERPNext Mozambique"),
		"route": "/app/erpnext-mozambique",
	}