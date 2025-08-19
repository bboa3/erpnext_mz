import os, json, frappe
site = os.environ.get('SITE', '').strip()
if not site:
    raise SystemExit('SITE env required')
frappe.init(site=site)
frappe.connect()
try:
    ss = frappe.get_single('System Settings')
    number_format = getattr(ss, 'number_format', None)
    float_precision = getattr(ss, 'float_precision', None)
    currency_precision = getattr(ss, 'currency_precision', None)
except Exception:
    number_format = float_precision = currency_precision = None
try:
    gd = frappe.get_single('Global Defaults')
    default_currency = getattr(gd, 'default_currency', None)
except Exception:
    default_currency = None
print(json.dumps({
    'site': site,
    'number_format': number_format,
    'float_precision': float_precision,
    'currency_precision': currency_precision,
    'default_currency': default_currency
}, ensure_ascii=False))
frappe.destroy()
