# Utilities for ERPNext Mozambique

from .web import enforce_guest_language

# expose jinja helpers from this package when referenced in hooks
try:
    from .jinja import get_qr_image, get_validation_url  # noqa: F401
except Exception:
    # Gracefully handle import errors
    def get_qr_image(doctype, name):
        return ""
    
    def get_validation_url(doctype, name):
        return ""

__all__ = ["enforce_guest_language", "get_qr_image", "get_validation_url"]
