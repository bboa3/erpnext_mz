import frappe
from frappe import _
from frappe.utils.data import cint


def _get_profile(create_if_missing: bool = True):
    """Return the Single doctype document. Singles are not inserted like normal docs."""
    try:
        # Ensure DocType exists (raises if not migrated on this site)
        frappe.get_meta("MZ Company Setup")
        # For Singles, use get_single
        return frappe.get_single("MZ Company Setup")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "MZ Company Setup load failed")
        return None


@frappe.whitelist()
def save_step(step: int | str, values=None):
    step_index = cint(step)
    profile = _get_profile()
    if not profile:
        frappe.throw(_("Unable to create or load MZ Company Setup"))

    # Handle values parameter - it might come as a string from the client
    if isinstance(values, str):
        import json
        try:
            values = json.loads(values)
        except (json.JSONDecodeError, TypeError):
            values = {}
    elif values is None:
        values = {}

    allowed_fields_by_step = {
        1: [
            "tax_id", 
            "tax_regime",
            "address_line1",
            "neighborhood_or_district", 
            "city",
            "province",
        ],
        2: [
            "phone",
            "email",
            "website",
        ],
        3: ["logo", "small_text_logz"],
    }

    fields = allowed_fields_by_step.get(step_index, [])
    for fieldname in fields:
        if fieldname in values:
            profile.set(fieldname, values[fieldname])

    if step_index == 1:
        profile.step1_complete = 1
    elif step_index == 2:
        profile.step2_complete = 1
    elif step_index == 3:
        # optional step - no completion flag needed
        pass

    profile.save(ignore_permissions=True)
    frappe.db.commit()
    return get_status()


@frappe.whitelist()
def skip_step(step: int | str):
    step_index = cint(step)
    profile = _get_profile()
    if not profile:
        frappe.throw(_("Unable to load MZ Company Setup"))

    if step_index == 3:
        profile.step3_skipped = 1  # Step 3 is the optional step (step3_skipped field)
    else:
        frappe.throw(_("Only optional steps can be skipped"))

    profile.save(ignore_permissions=True)
    frappe.db.commit()
    return get_status()


@frappe.whitelist()
def apply_all():
    """
    Idempotent application of configuration using values stored on the Single DocType.
    - Assumes Company already exists from ERPNext default wizard as per user's requirement.
    - Updates Company NUIT, creates address/contact, banking, branding, and tax defaults.
    """
    profile = _get_profile(create_if_missing=False)
    if not profile:
        frappe.throw(_("MZ Company Setup not found"))

    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        # Fallback: pick first Company
        company = frappe.get_all("Company", pluck="name", limit=1)
        company_name = company[0] if company else None
    if not company_name:
        frappe.throw(_("No Company found. Please create a Company first."))

    # A. Core updates
    _update_company_tax_id(company_name, profile.tax_id)
    _ensure_fiscal_year()
    _ensure_address(company_name, profile)
    _apply_branding(company_name, profile)

    # B. Taxes: copy from erp.local if present, else ensure minimal defaults
    _ensure_tax_infrastructure(company_name, profile)

    profile.is_applied = 1
    profile.save(ignore_permissions=True)
    frappe.db.commit()

    return {"ok": True, "message": _("Mozambique setup applied successfully."), "status": get_status()}


def _update_company_tax_id(company_name: str, nuit: str | None):
    if not nuit:
        return
    try:
        company = frappe.get_doc("Company", company_name)
        if company.tax_id != nuit:
            company.tax_id = nuit
            company.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Update Company NUIT failed")


def _ensure_fiscal_year():
    if frappe.db.exists("Fiscal Year", {"year_start_date": "2025-01-01", "year_end_date": "2025-12-31"}):
        return
    try:
        fy = frappe.new_doc("Fiscal Year")
        fy.year = "2025"
        fy.year_start_date = "2025-01-01"
        fy.year_end_date = "2025-12-31"
        fy.save(ignore_permissions=True)
    except Exception:
        # Ignore if duplicate
        pass


def _ensure_address(company_name: str, profile):
    existing = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Company", "link_name": company_name, "parenttype": "Address"},
        fields=["parent"],
        limit=1,
    )
    if existing:
        return
    try:
        addr = frappe.new_doc("Address")
        addr.address_title = company_name
        addr.address_type = "Billing"
        addr.address_line1 = profile.address_line1 or ""
        addr.address_line2 = profile.neighborhood_or_district or ""
        addr.city = profile.city or ""
        addr.state = profile.province or ""
        addr.country = "Mozambique"
        addr.phone = profile.phone or ""
        addr.email_id = profile.email or ""
        addr.append("links", {"link_doctype": "Company", "link_name": company_name})
        addr.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure Address failed")



def _apply_branding(company_name: str, profile):
    try:
        if profile.logo:
            lh_name = f"{company_name} - Default"
            if not frappe.db.exists("Letter Head", lh_name):
                lh = frappe.new_doc("Letter Head")
                lh.letter_head_name = lh_name
                lh.is_default = 1
                lh.content = (profile.small_text_logz or "")
                lh.is_header = 1
                lh.is_active = 1
                lh.company = company_name
                lh.insert(ignore_permissions=True)
            else:
                lh = frappe.get_doc("Letter Head", lh_name)
                lh.content = (profile.small_text_logz or lh.content or "")
                lh.save(ignore_permissions=True)
            frappe.db.set_single_value("Print Settings", "with_letterhead", 1)
        elif profile.small_text_logz:
            # Set global print footer if no letterhead provided
            frappe.db.set_single_value("Print Settings", "pdf_footer_html", profile.small_text_logz)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Apply branding failed")


def _ensure_tax_infrastructure(company_name: str, profile):
    """
    If templates exist (as per user's note), leave them. Otherwise, create minimal ones.
    Also set defaults based on tax_regime.
    """
    try:
        # Create all tax masters if missing (new sites will need them)
        _create_tax_masters(company_name)

        # Set defaults by regime
        regime = (profile.tax_regime or "Normal").lower()
        if regime.startswith("normal"):
            default_template = "Regime Normal (16%)"
        elif regime.startswith("isento"):
            default_template = "Isento/Exportação"
        else:
            default_template = "Isento/Exportação"

        # Note: ERPNext uses is_default flag on templates, not Company fields
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure tax infra failed")


def _create_tax_masters(company_name: str):
    # Create full set of masters as per wizard.md for new sites
    def ensure_account(name: str, root_type: str, account_type: str | None = None, parent_account: str | None = None, account_number: str | None = None):
        try:
            if frappe.db.exists("Account", {"company": company_name, "account_name": name}):
                return frappe.get_value("Account", {"company": company_name, "account_name": name}, "name")
            
            # Find or create parent account
            if parent_account:
                parent_acc = frappe.db.exists("Account", {"company": company_name, "account_name": parent_account})
                if not parent_acc:
                    # Create parent account as a group
                    parent_doc = frappe.new_doc("Account")
                    parent_doc.company = company_name
                    parent_doc.account_name = parent_account
                    parent_doc.root_type = root_type
                    parent_doc.is_group = 1
                    parent_doc.insert(ignore_permissions=True)
                    parent_acc = parent_doc.name
            
            acc = frappe.new_doc("Account")
            acc.company = company_name
            acc.account_name = name
            acc.root_type = root_type
            acc.is_group = 0  # Tax accounts should not be groups
            if account_type:
                acc.account_type = account_type
            if account_number:
                acc.account_number = account_number
            if parent_account and parent_acc:
                acc.parent_account = parent_acc
            acc.insert(ignore_permissions=True)
            return acc.name
        except Exception as e:
            frappe.log_error(f"Error creating account {name}: {str(e)}", "Account Creation Error")
            return None

    # Get company abbreviation for account naming
    company_abbr = frappe.get_value("Company", company_name, "abbr") or "MS"
    
    # Create tax accounts as per wizard.md with correct parent "Duties and Taxes" and account numbers
    a_output_16 = ensure_account(f"IVA a Entregar 16% - {company_abbr}", "Liability", "Tax", "Duties and Taxes", "24.01.01")
    a_output_5 = ensure_account(f"IVA a Entregar 5% - {company_abbr}", "Liability", "Tax", "Duties and Taxes", "24.01.02")
    a_output_0 = ensure_account(f"Isento/Exportação - {company_abbr}", "Liability", "Tax", "Duties and Taxes", "24.01.03")
    a_input_16 = ensure_account(f"IVA Dedutível 16% - {company_abbr}", "Asset", "Tax", "Duties and Taxes", "13.01.01")
    a_input_5 = ensure_account(f"IVA Dedutível 5% - {company_abbr}", "Asset", "Tax", "Duties and Taxes", "13.01.02")
    a_input_0 = ensure_account(f"IVA Dedutível 0% - {company_abbr}", "Asset", "Tax", "Duties and Taxes", "13.01.03")

    # Create tax categories first
    def ensure_tax_category(name: str):
        # Tax Category uses title field; name may differ based on autoname
        if frappe.db.exists("Tax Category", {"title": name}):
            return frappe.get_value("Tax Category", {"title": name}, "name")
        doc = frappe.new_doc("Tax Category")
        doc.title = name
        doc.insert(ignore_permissions=True)
        return doc.name

    tc_normal = ensure_tax_category("Regime Normal (16%)")
    tc_reduzida = ensure_tax_category("Taxa Reduzida (5%)")
    tc_isento = ensure_tax_category("Isento/Exportação")

    def ensure_sales_template(title: str, rate: float, account: str | None, tax_category: str | None = None, is_default: bool = False):
        if frappe.db.exists("Sales Taxes and Charges Template", {"title": title, "company": company_name}):
            return
        st = frappe.new_doc("Sales Taxes and Charges Template")
        st.title = title
        st.company = company_name
        st.is_default = 1 if is_default else 0 
        if tax_category:
            st.tax_category = tax_category
        
        # Get cost center
        cost_center = frappe.get_value("Company", company_name, "cost_center") or f"Main - {company_abbr}"
        
        st.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head": account,
                "account_currency": "MZN",
                "rate": rate,
                "description": title,
                "cost_center": cost_center,
                "row_id": None,
            },
        )
        st.insert(ignore_permissions=True)

    # Get the profile to determine which template should be default
    profile = _get_profile(create_if_missing=True)
    regime = (profile.tax_regime or "Normal").lower()
    
    ensure_sales_template("Regime Normal (16%)", 16.0, a_output_16, "Regime Normal (16%)", regime.startswith("normal"))
    ensure_sales_template("Taxa Reduzida (5%)", 5.0, a_output_5, "Taxa Reduzida (5%)", regime.startswith("reduzida"))
    ensure_sales_template("Isento/Exportação", 0.0, a_output_0, "Isento/Exportação", regime.startswith("isento"))

    def ensure_purchase_template(title: str, rate: float, account: str | None, tax_category: str | None = None, is_default: bool = False):
        if frappe.db.exists("Purchase Taxes and Charges Template", {"title": title, "company": company_name}):
            return
        pt = frappe.new_doc("Purchase Taxes and Charges Template")
        pt.title = title
        pt.company = company_name
        pt.is_default = 1 if is_default else 0
        if tax_category:
            pt.tax_category = tax_category
        
        # Get cost center
        cost_center = frappe.get_value("Company", company_name, "cost_center") or f"Main - {company_abbr}"
        
        pt.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head": account,
                "account_currency": "MZN",
                "rate": rate,
                "description": title,
                "cost_center": cost_center,
                "add_deduct_tax": "Add",
                "category": "Total",
                "row_id": None,
            },
        )
        pt.insert(ignore_permissions=True)

    ensure_purchase_template("Regime Normal (16%)", 16.0, a_input_16, "Regime Normal (16%)", regime.startswith("normal"))
    ensure_purchase_template("Taxa Reduzida (5%)", 5.0, a_input_5, "Taxa Reduzida (5%)", regime.startswith("reduzida"))
    ensure_purchase_template("Isento/Exportação", 0.0, a_input_0, "Isento/Exportação", regime.startswith("isento"))

    # Ensure only one template per company is marked as default
    def ensure_single_default_template(doctype: str, default_title: str):
        # Unset all defaults for this company
        frappe.db.sql(f"UPDATE `tab{doctype}` SET is_default = 0 WHERE company = %s", (company_name,))
        # Set the correct default
        frappe.db.sql(f"UPDATE `tab{doctype}` SET is_default = 1 WHERE company = %s AND title = %s", (company_name, default_title))
    
    ensure_single_default_template("Sales Taxes and Charges Template", default_template)
    ensure_single_default_template("Purchase Taxes and Charges Template", default_template)

    def ensure_item_tax_template(title: str, rate: float):
        if frappe.db.exists("Item Tax Template", {"title": title, "company": company_name}):
            return
        itt = frappe.new_doc("Item Tax Template")
        itt.title = title
        itt.company = company_name
        itt.append(
            "taxes",
            {
                "tax_type": a_output_16 if rate == 16 else a_output_5 if rate == 5 else a_output_0,
                "tax_rate": rate,
            },
        )
        itt.insert(ignore_permissions=True)

    ensure_item_tax_template("Regime Normal (16%)", 16.0)
    ensure_item_tax_template("Taxa Reduzida (5%)", 5.0)
    ensure_item_tax_template("Isento/Exportação", 0.0)

    # Create a single default Tax Rule for all clients and items based on regime
    def ensure_default_tax_rule():
        # Get the profile to determine the regime
        profile = _get_profile(create_if_missing=True)
        regime = (profile.tax_regime or "Normal").lower()
        
        if regime.startswith("normal"):
            template_title = "Regime Normal (16%)"
            category_title = "Regime Normal (16%)"
        elif regime.startswith("isento"):
            template_title = "Isento/Exportação"
            category_title = "Isento/Exportação"
        else:
            template_title = "Isento/Exportação"
            category_title = "Isento/Exportação"

        # Get template and category names
        sales_template = frappe.db.get_value(
            "Sales Taxes and Charges Template",
            {"title": template_title, "company": company_name},
            "name",
        )
        purchase_template = frappe.db.get_value(
            "Purchase Taxes and Charges Template",
            {"title": template_title, "company": company_name},
            "name",
        )
        tax_category_name = frappe.db.get_value("Tax Category", {"title": category_title}, "name")
        
        if not sales_template or not purchase_template or not tax_category_name:
            return

        # Check if default rule already exists
        exists = frappe.db.exists(
            "Tax Rule",
            {
                "company": company_name,
                "use_for": "Sales",
                "tax_category": tax_category_name,
                "sales_tax_template": sales_template,
            },
        )
        if exists:
            return

        # Create Sales Tax Rule
        tr_sales = frappe.new_doc("Tax Rule")
        tr_sales.company = company_name
        tr_sales.use_for = "Sales"
        tr_sales.tax_category = tax_category_name
        tr_sales.sales_tax_template = sales_template
        tr_sales.priority = 1
        tr_sales.insert(ignore_permissions=True)

        # Create Purchase Tax Rule
        tr_purchase = frappe.new_doc("Tax Rule")
        tr_purchase.company = company_name
        tr_purchase.use_for = "Purchase"
        tr_purchase.tax_category = tax_category_name
        tr_purchase.purchase_tax_template = purchase_template
        tr_purchase.priority = 1
        tr_purchase.insert(ignore_permissions=True)

    ensure_default_tax_rule()


@frappe.whitelist()
def get_status():
    profile = _get_profile(create_if_missing=True)
    if not profile:
        return {"exists": False}
    return {
        "exists": True,
        "step1_complete": cint(profile.step1_complete),
        "step2_complete": cint(profile.step2_complete),
        "step3_skipped": cint(profile.step3_skipped),
        "applied": cint(profile.is_applied),
    }


@frappe.whitelist()
def get_profile_values():
    profile = _get_profile(create_if_missing=True)
    if not profile:
        return {}
    fields = [
        "tax_id",
        "tax_regime",
        "address_line1",
        "neighborhood_or_district",
        "city",
        "province",
        "phone",
        "email",
        "website",
        "logo",
        "small_text_logz",
    ]
    return {f: profile.get(f) for f in fields}

import frappe
from erpnext_mz.setup.language import ensure_language_pt_mz


def complete_mz_setup(args: dict | None = None):
    """
    Hooked into setup_wizard_complete.

    Runs after the main wizard completes. Applies Mozambique basics if requested
    on our custom slide. Keep it idempotent and side-effect free beyond updates.
    """
    args = args or {}

    try:
        if frappe.flags.in_test:
            # Avoid side-effects in tests
            return

        # Always ensure pt-MZ language exists so users can pick it post-install too
        ensure_language_pt_mz()

        if args.get("enable_mz_defaults"):
            # Do not override what the core wizard already set for the user, just
            # make sure language availability is correct (handled above). Any further
            # defaults can be applied by user via provided settings wizards.
            pass

        if args.get("create_demo"):
            # Placeholder: In the future we could enqueue demo data creation here
            # frappe.enqueue(erpnext_mz.demo.create_demo_data, enqueue_after_commit=True)
            frappe.logger().info("ERPNext MZ: Demo data creation requested (not implemented)")

    except Exception:
        frappe.log_error(title="ERPNext MZ Setup Wizard Completion Failed", message=frappe.get_traceback())
        # Do not raise; let the main wizard finish


