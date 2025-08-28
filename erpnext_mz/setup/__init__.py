# Setup modules for ERPNext Mozambique

"""
Setup Module Organization:

- setup/language.py: Language configuration and system settings
- setup/branding.py: Website branding and appearance
- setup/uom.py: Unit of Measure setup and Portuguese translation

These modules are called during app installation and migration
to configure the system for Mozambican localization.
"""

from .language import ensure_language_pt_mz, apply_system_settings
from .branding import apply_website_branding
from .uom import setup_portuguese_uoms_complete, test_portuguese_uoms

__all__ = [
    "ensure_language_pt_mz",
    "apply_system_settings", 
    "apply_website_branding",
    "setup_portuguese_uoms_complete",
    "test_portuguese_uoms"
]