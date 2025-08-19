# -*- coding: utf-8 -*-
"""
ERPNext Mozambique Compliance Custom App

This app provides Mozambique-specific tax compliance, accounting, and HR features:
- Chart of Accounts aligned with IFRS
- VAT templates (16%, 5%, 0%)
- INSS and IRPS calculations
- SAF-T XML generation
- AT (Autoridade Tributária) integration
- Benefits in kind management
- Compliance validations and reporting
"""

__version__ = "1.0.0"
__author__ = "ERPNext Mozambique Team"
__email__ = "support@erpnextmz.com"

# Import modules to register them
# Ensure subpackages are importable when app is loaded by bench
try:
    from . import modules  # noqa: F401
    from . import doctypes  # noqa: F401
    from . import pages  # noqa: F401
except Exception:
    # Avoid import errors during partial installs/migrations
    pass
