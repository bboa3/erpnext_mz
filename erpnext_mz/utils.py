import frappe


def enforce_guest_language():
	"""
	Ensure guest pages use the site's default language by setting
	the 'preferred_language' cookie to the site's default (pt-MZ) if missing.
	"""
	try:
		if frappe.session.user != "Guest":
			return

		desired = (
			frappe.db.get_default("lang")
			or frappe.db.get_single_value("System Settings", "language")
			or "pt-MZ"
		)

		enabled = set(frappe.translate.get_all_languages())
		if desired not in enabled and "-" in desired:
			parent = desired.split("-", 1)[0]
			if parent in enabled:
				desired = parent

		current = frappe.request.cookies.get("preferred_language") if hasattr(frappe, "request") else None
		if current != desired and hasattr(frappe.local, "cookie_manager"):
			frappe.local.cookie_manager.set_cookie("preferred_language", desired)
	except Exception:
		frappe.log_error(title="enforce_guest_language failed", message=frappe.get_traceback())
