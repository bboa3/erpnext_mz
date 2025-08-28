import frappe
from frappe.model.naming import get_abbr
from frappe.utils import cint

def _get_company_abbr(company: str) -> str:
    abbr = frappe.db.get_value("Company", company, "abbr")
    return abbr or get_abbr(company)

def _ensure_parent_duties_and_taxes(company: str) -> str:
    """Return path 'Duties and Taxes - {ABBR}'. Create under Current Liabilities if missing."""
    abbr = _get_company_abbr(company)
    parent_name = f"Duties and Taxes - {abbr}"
    if frappe.db.exists("Account", {"company": company, "account_name": "Duties and Taxes"}):
        return frappe.db.get_value("Account", {"company": company, "account_name": "Duties and Taxes"}, "name")

    # Create under Current Liabilities
    cliab = frappe.db.get_value(
        "Account", {"company": company, "root_type": "Liability", "is_group": 1, "account_name": "Current Liabilities"}, "name"
    )
    if not cliab:
        # fallback to company root
        cliab = frappe.db.get_value("Account", {"company": company, "is_group": 1, "root_type": "Liability"}, "name")

    doc = frappe.get_doc({
        "doctype": "Account",
        "account_name": "Duties and Taxes",
        "company": company,
        "is_group": 1,
        "parent_account": cliab,
        "root_type": "Liability",
        "report_type": "Balance Sheet"
    })
    inserted = doc.insert(ignore_permissions=True)
    return inserted.name

def _ensure_account(company: str, *, account_number: str, account_name: str,
                    parent_account: str, root_type: str, balance_must_be: str,
                    tax_rate: float):
    # already exists by number or by (name, company)?
    exists = frappe.db.get_value("Account",
        {"company": company, "account_number": account_number}, "name")
    if exists:
        return exists

    exists_by_name = frappe.db.get_value("Account",
        {"company": company, "account_name": account_name}, "name")
    if exists_by_name:
        # backfill number, rate, balance rule if missing
        acc = frappe.get_doc("Account", exists_by_name)
        if not acc.account_number:
            acc.account_number = account_number
        acc.tax_rate = tax_rate
        acc.account_type = "Tax"
        acc.balance_must_be = "Credit" if balance_must_be.lower().startswith("c") else "Debit"
        if acc.root_type != root_type:
            acc.root_type = root_type
        if acc.parent_account != parent_account:
            acc.parent_account = parent_account
        acc.report_type = "Balance Sheet"
        acc.save(ignore_permissions=True)
        return acc.name

    # create new
    currency = frappe.db.get_value("Company", company, "default_currency") or "MZN"
    acc = frappe.get_doc({
        "doctype": "Account",
        "company": company,
        "parent_account": parent_account,
        "account_name": account_name,
        "account_number": account_number,              # Número da conta
        "is_group": 0,
        "root_type": root_type,                        # Asset / Liability
        "report_type": "Balance Sheet",
        "account_currency": currency,
        "account_type": "Tax",                         # Tipo de conta (Imposto)
        "tax_rate": tax_rate,                          # Taxa de imposto (ex.: 16.00)
        "balance_must_be": "Credit" if balance_must_be.lower().startswith("c") else "Debit",
    })
    acc.insert(ignore_permissions=True)
    return acc.name

def create_mz_vat_accounts(company: str):
    """Cria as 4 contas de IVA para a empresa indicada."""
    parent_dt = _ensure_parent_duties_and_taxes(company)

    # 1) 13.01.01 - IVA Dedutível 16%  (Ativo / Débito)
    _ensure_account(
        company,
        account_number="13.01.01",
        account_name="IVA Dedutível 16%",
        parent_account=parent_dt,          # mantém sob Duties and Taxes por consistência visual
        root_type="Asset",
        balance_must_be="Débito",
        tax_rate=16.0
    )

    # 2) 13.01.02 - IVA Dedutível 5%   (Ativo / Débito)
    _ensure_account(
        company,
        account_number="13.01.02",
        account_name="IVA Dedutível 5%",
        parent_account=parent_dt,
        root_type="Asset",
        balance_must_be="Débito",
        tax_rate=5.0
    )

    # 3) 13.01.03 - Isento/Exportação
    _ensure_account(
        company,
        account_number="13.01.03",
        account_name="Isento/Exportação",
        parent_account=parent_dt,
        root_type="Asset",
        balance_must_be="Débito",
        tax_rate=0.0
    )


    # 4) 24.01.01 - IVA a Entregar 16% (Passivo / Crédito)
    _ensure_account(
        company,
        account_number="24.01.01",
        account_name="IVA a Entregar 16%",
        parent_account=parent_dt,
        root_type="Liability",
        balance_must_be="Crédito",
        tax_rate=16.0
    )

    # 5) 24.01.02 - IVA a Entregar 5%  (Passivo / Crédito)
    _ensure_account(
        company,
        account_number="24.01.02",
        account_name="IVA a Entregar 5%",
        parent_account=parent_dt,
        root_type="Liability",
        balance_must_be="Crédito",
        tax_rate=5.0
    )


    # 6) 24.01.03 - Isento/Exportação
    _ensure_account(
        company,
        account_number="24.01.03",
        account_name="Isento/Exportação",
        parent_account=parent_dt,
        root_type="Liability",
        balance_must_be="Crédito",
        tax_rate=0.0
    )

    return "Contas de IVA criadas/atualizadas com sucesso."
