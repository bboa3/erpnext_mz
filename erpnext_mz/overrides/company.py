import json
import os
import frappe

from erpnext.setup.doctype.company.company import Company as ERPNextCompany
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts


def load_mz_coa_tree() -> dict:
    """Load Mozambique COA JSON and return the 'tree' object expected by ERPNext.

    Raises a frappe.throw if the file is missing or invalid.
    """
    path = frappe.get_app_path("erpnext_mz", "chart_of_accounts", "mozambique_coa.json")
    if not os.path.exists(path):
        frappe.throw(f"Mozambique CoA file not found: {path}")

    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    tree = data.get("tree")
    if not isinstance(tree, dict) or not tree:
        frappe.throw("Mozambique CoA JSON is missing a non-empty 'tree' object.")

    return tree


class Company(ERPNextCompany):  # type: ignore[misc]
    def create_default_accounts(self):  # noqa: D401
        """Seed Mozambique chart for every company when Accounts are absent."""
        frappe.logger().info(
            f"ERPNext MZ: Company.create_default_accounts override called for '{self.name}'"
        )

        forest = load_mz_coa_tree()
        frappe.local.flags.ignore_root_company_validation = True
        create_charts(self.name, custom_chart=forest)
        frappe.logger().info(
            f"ERPNext MZ: Seeded Mozambique COA for company '{self.name}' with {len(forest.keys())} roots"
        )

        # Match ERPNext behavior: set defaults for receivable and payable
        self.db_set(
            "default_receivable_account",
            frappe.db.get_value(
                "Account", {"company": self.name, "account_type": "Receivable", "is_group": 0}
            ),
        )
        self.db_set(
            "default_payable_account",
            frappe.db.get_value(
                "Account", {"company": self.name, "account_type": "Payable", "is_group": 0}
            ),
        )
        frappe.logger().info(
            f"ERPNext MZ: Default AR/AP set for '{self.name}' => AR='{self.default_receivable_account}', AP='{self.default_payable_account}'"
        )


def ensure_mz_coa_seeded(doc, method=None):
    """Doc Event Guard: Ensure Mozambique COA is seeded if no accounts exist.

    This serves as a safety net in case the class override is bypassed during setup.
    """
    try:
        if frappe.db.exists("Account", {"company": doc.name}):
            return

        forest = load_mz_coa_tree()
        frappe.local.flags.ignore_root_company_validation = True
        create_charts(doc.name, custom_chart=forest)
        frappe.logger().info(
            f"ERPNext MZ: Guard seeded Mozambique COA for company '{doc.name}' with {len(forest.keys())} roots"
        )

        ar = frappe.db.get_value(
            "Account", {"company": doc.name, "account_type": "Receivable", "is_group": 0}
        )
        ap = frappe.db.get_value(
            "Account", {"company": doc.name, "account_type": "Payable", "is_group": 0}
        )
        if ar:
            frappe.db.set_value("Company", doc.name, "default_receivable_account", ar)
        if ap:
            frappe.db.set_value("Company", doc.name, "default_payable_account", ap)
    except Exception:
        frappe.log_error(
            title="ERPNext MZ: ensure_mz_coa_seeded failed",
            message=frappe.get_traceback(),
        )


