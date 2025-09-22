import frappe
from frappe import _
from frappe.utils.data import cint
from erpnext_mz.utils.account_utils import get_cost_center, require_account_by_number


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
            "payment_method_cash",
            "payment_method_bci", 
            "payment_method_millenium",
            "payment_method_standard_bank",
            "payment_method_absa",
            "payment_method_emola",
            "payment_method_mpesa",
            "payment_method_fnb",
            "payment_method_moza",
            "payment_method_letshego",
            "payment_method_first_capital",
            "payment_method_nedbank",
        ],
        3: ["logo", "terms_and_conditions_of_sale"],
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

    # C. Banking infrastructure: bank accounts and payment methods
    _ensure_banking_infrastructure(company_name, profile)

    # D. HR & Payroll infrastructure
    _ensure_hr_payroll_infrastructure(company_name)

    # E. Create print formats
    _create_print_formats()

    # F. SMTP infrastructure
    _ensure_smtp_infrastructure(company_name)

    # Reload profile to avoid timestamp mismatch
    profile.reload()
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
    # Update Company document with contact information
    try:
        company_doc = frappe.get_doc("Company", company_name)
        updated = False
        
        # Update phone if provided and different
        if profile.phone and company_doc.phone_no != profile.phone:
            company_doc.phone_no = profile.phone
            updated = True
            
        # Update email if provided and different
        if profile.email and company_doc.email != profile.email:
            company_doc.email = profile.email
            updated = True
            
        # Update website if provided and different
        if profile.website and company_doc.website != profile.website:
            company_doc.website = profile.website
            updated = True
            
        if updated:
            company_doc.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Update Company contact info failed")

    # Create or update Address document
    existing = frappe.get_all(
        "Dynamic Link",
        filters={"link_doctype": "Company", "link_name": company_name, "parenttype": "Address"},
        fields=["parent"],
        limit=1,
    )
    
    try:
        if existing:
            # Update existing address
            addr = frappe.get_doc("Address", existing[0].parent)
            addr.address_line1 = profile.address_line1 or ""
            addr.address_line2 = profile.neighborhood_or_district or ""
            addr.city = profile.city or ""
            addr.state = profile.province or ""
            addr.country = "Mozambique"
            addr.phone = profile.phone or ""
            addr.email_id = profile.email or ""
            addr.save(ignore_permissions=True)
        else:
            # Create new address
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
    """Create or update a default letter head for the company using profile data.

    - Builds an HTML header that includes the company logo (if provided) and company contact info
    - Sets footer with ERPNext branding and company contact details
    - Enables letterhead in Print Settings and sets Company's default letter head
    - Creates Terms and Conditions for Sales if provided
    - Updates company website if provided
    """
    try:
        lh_name = f"{company_name} - Default"

        # Collect info
        company_doc = frappe.get_doc("Company", company_name)
        tax_id = company_doc.tax_id or (profile.tax_id or "")
        phone = profile.phone or ""
        email = profile.email or ""
        website = (getattr(profile, "website", None) or getattr(company_doc, "website", None) or "")
        line1 = profile.address_line1 or ""
        lne2 = profile.neighborhood_or_district or ""
        ciity = profile.city or ""
        province = profile.province or ""
        logo_url = None

        # Update company website if provided in profile
        if getattr(profile, "website", None) and company_doc.website != profile.website:
            company_doc.website = profile.website
            company_doc.save(ignore_permissions=True)

        # Prefer profile logo; fallback to company logo
        if getattr(profile, "logo", None):
            logo_url = profile.logo
        elif getattr(company_doc, "company_logo", None):
            logo_url = company_doc.company_logo

        # Build header HTML with consistent design system matching print formats
        header_html = [
            "<div style=\"font-family: 'Arial', 'Helvetica', sans-serif; margin-bottom: 20px;\">",
            "<div style=\"display: flex; align-items: flex-start; gap: 20px; margin-bottom: 12px;\">",
        ]
        
        # Left section: Logo and NUIT
        header_html.append("<div style=\"flex: 0 0 150px;\">")
        if logo_url:
            header_html.append(f"<img src=\"{logo_url}\" style=\"max-height: 80px; max-width: 150px; object-fit: contain; margin-bottom: 8px;\"/>")
        if tax_id:
            header_html.append(f"<div style=\"font-size: 11px; font-weight: 600; background-color: #f8f9fa; padding: 4px 8px; border: 1px solid #e5e5e5; text-align: center; color: #2c3e50; border-radius: 3px;\">NUIT: {frappe.utils.escape_html(tax_id)}</div>")
        header_html.append("</div>")
        
        # Center section: Company name and contact details
        header_html.append("<div style=\"flex: 1; text-align: center; padding: 0 20px;\">")
        header_html.append(f"<h1 style=\"font-weight: 600; font-size: 20px; margin: 0 0 8px 0; color: #2c3e50; text-transform: uppercase; letter-spacing: 0.5px;\">{frappe.utils.escape_html(company_name)}</h1>")
        
        # Contact details in center
        contact_details = []
        if email:
            contact_details.append(frappe.utils.escape_html(email))
        if phone:
            contact_details.append(frappe.utils.escape_html(phone))
        if website:
            contact_details.append(frappe.utils.escape_html(website))
        if tax_id:
            contact_details.append(frappe.utils.escape_html(tax_id))

        
        if contact_details:
            header_html.append(f"<div style=\"font-size: 12px; line-height: 1.4; color: #7f8c8d;\">{'<br>'.join(contact_details)}</div>")
        header_html.append("</div>")
        
        # Right section: Company address
        header_html.append("<div style=\"flex: 0 0 200px; text-align: right;\">")
        address_parts = [p for p in [line1, lne2, f"{ciity} {province}".strip()] if p]
        if address_parts:
            for part in address_parts:
                header_html.append(f"<div style=\"font-size: 12px; line-height: 1.3; color: #555; margin-bottom: 2px;\">{frappe.utils.escape_html(part)}</div>")
        header_html.append(f"<div style=\"font-size: 12px; line-height: 1.3; font-weight: 600; color: #2c3e50;\">Mozambique</div>")
        header_html.append("</div>")
        
        header_html.append("</div>")
        header_html.append("</div>")
        header_html = "".join(header_html)

        # Get terms and conditions text
        terms_text = getattr(profile, "terms_and_conditions_of_sale", None) or ""

        # Build footer HTML with consistent design system
        footer_html = []
        
        # Add "Processado pelo programa ERPNext Moçambique" (subtle branding)
        footer_html.append("<div style=\"color: #f0f0f0; font-size: 8px; margin-bottom: 8px; font-family: 'Arial', 'Helvetica', sans-serif;\">Processado pelo programa MozEconomia Cloud</div>")
        
        # Add company address and contacts in line with consistent styling
        footer_contact_parts = []
        if line1:
            footer_contact_parts.append(frappe.utils.escape_html(line1))
        if lne2:
            footer_contact_parts.append(frappe.utils.escape_html(lne2))
        if ciity and province:
            footer_contact_parts.append(f"{frappe.utils.escape_html(ciity)}, {frappe.utils.escape_html(province)}")
        if phone:
            footer_contact_parts.append(f"Tel: {frappe.utils.escape_html(phone)}")
        if email:
            footer_contact_parts.append(f"Email: {frappe.utils.escape_html(email)}")
        
        if footer_contact_parts:
            footer_html.append(f"<div style=\"font-size: 9px; color: #7f8c8d; font-family: 'Arial', 'Helvetica', sans-serif; line-height: 1.3;\">{' | '.join(footer_contact_parts)}</div>")
        
        footer_content = "".join(footer_html)

        # Create or update Letter Head
        if not frappe.db.exists("Letter Head", 'MozEconomia Cloud - Default'):
            lh = frappe.new_doc("Letter Head")
            lh.letter_head_name = 'MozEconomia Cloud - Default'
            lh.company = company_name
            lh.is_default = 1
            lh.disabled = 0
            lh.source = "HTML"
            lh.footer_source = "HTML"
            lh.content = header_html
            lh.footer = footer_content
            lh.insert(ignore_permissions=True)
        else:
            lh = frappe.get_doc("Letter Head", 'MozEconomia Cloud - Default')
            lh.company = company_name
            lh.is_default = 1
            lh.disabled = 0
            lh.source = "HTML"
            lh.footer_source = "HTML"
            lh.content = header_html
            lh.footer = footer_content
            lh.save(ignore_permissions=True)

        # Ensure letterhead is enabled in Print Settings
        frappe.db.set_single_value("Print Settings", "with_letterhead", 1)

        # Set as company's default letter head
        try:
            if getattr(company_doc, "default_letter_head", None) != 'MozEconomia Cloud - Default':
                company_doc.db_set("default_letter_head", 'MozEconomia Cloud - Default', commit=True)
        except Exception:
            pass

        # Create Terms and Conditions for Sales if provided
        if terms_text:
            _create_terms_and_conditions(company_name, terms_text)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Apply branding failed")


def _create_terms_and_conditions(company_name: str, terms_text: str):
    """Create Terms and Conditions for Sales transactions."""
    try:
        tc_name = f"{company_name} - Terms and Conditions"
        
        # Check if Terms and Conditions already exists
        if frappe.db.exists("Terms and Conditions", tc_name):
            return

        # Create new Terms and Conditions
        tc = frappe.new_doc("Terms and Conditions")
        tc.title = tc_name
        tc.terms = terms_text
        tc.insert(ignore_permissions=True)
        
        # Set as default for the company
        try:
            company_doc = frappe.get_doc("Company", company_name)
            if getattr(company_doc, "default_selling_terms", None) != tc_name:
                company_doc.db_set("default_selling_terms", tc_name, commit=True)
        except Exception:
            # Company might not have this field, that's okay
            pass
            
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Create Terms and Conditions failed")


def _ensure_tax_infrastructure(company_name: str, profile):
    """
    If templates exist (as per user's note), leave them. Otherwise, create minimal ones.
    Also set defaults based on tax_regime.
    """
    try:
        # Create all tax masters if missing (new sites will need them)
        _create_tax_masters(company_name)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure tax infra failed")


def _create_tax_masters(company_name: str):
    """Create tax masters for Mozambique including VAT accounts and tax templates"""

    # With IFRS MZ CoA present, these accounts should already exist via mozambique_coa.json.
    # Fetch by definitive account numbers instead of creating or guessing parents.
    a_output_16 = require_account_by_number(company_name, "21.02.01", "IVA a Entregar 16%")
    a_output_5  = require_account_by_number(company_name, "21.02.02", "IVA a Entregar 5%")
    a_output_0  = require_account_by_number(company_name, "21.02.03", "IVA a Entregar 0%")
    a_input_16  = require_account_by_number(company_name, "11.04.01", "IVA Dedutível 16%")
    a_input_5   = require_account_by_number(company_name, "11.04.02", "IVA Dedutível 5%")
    a_input_0   = require_account_by_number(company_name, "11.04.03", "IVA Dedutível 0%")

    
    def ensure_tax_category(title: str):
        if frappe.db.exists("Tax Category", {"title": title}):
            return frappe.get_value("Tax Category", {"title": title}, "name")
        doc = frappe.new_doc("Tax Category")
        doc.title = title
        doc.insert(ignore_permissions=True)
        return doc.name

    tc_normal   = ensure_tax_category("IVA 16%")
    tc_reduzida = ensure_tax_category("IVA 5%")
    tc_isento   = ensure_tax_category("IVA 0% (Isento)")

    def ensure_sales_template(title: str, rate: float, account: str | None, tax_category_name: str | None = None, is_default: bool = False):
        if frappe.db.exists("Sales Taxes and Charges Template", {"title": title, "company": company_name}):
            return
        st = frappe.new_doc("Sales Taxes and Charges Template")
        st.title = title
        st.company = company_name
        st.is_default = 1 if is_default else 0 
        if tax_category_name:
            st.tax_category = tax_category_name
        
        # Get cost center
        cost_center = get_cost_center(company_name)
        
        if not cost_center:
            frappe.log_error(f"Could not find cost center for company {company_name}", "Cost Center Creation Error")
            print(f"⚠️ Skipping sales template creation for {title} due to missing cost center")
            return
        
        if not account:
            frappe.log_error(f"Account is None for sales template {title}", "Account Creation Error")
            print(f"⚠️ Skipping sales template creation for {title} due to missing account")
            return
        
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
    # Determine default template title by regime
    if regime.startswith("normal"):
        default_title = "IVA 16%"
    elif regime.startswith("reduzida") or regime.startswith("reducida"):
        default_title = "IVA 5%"
    elif regime.startswith("isento"):
        default_title = "IVA 0% (Isento)"
    else:
        default_title = "IVA 0% (Isento)"
    
    ensure_sales_template("IVA 16%",16.0, a_output_16, "IVA 16%",   regime.startswith("normal"))
    ensure_sales_template("IVA 5%",5.0, a_output_5,  "IVA 5%", regime.startswith("reduzida"))
    ensure_sales_template("IVA 0% (Isento)",  0.0, a_output_0,  "IVA 0% (Isento)",   regime.startswith("isento"))

    def ensure_purchase_template(title: str, rate: float, account: str | None, tax_category_name: str | None = None, is_default: bool = False):
        if frappe.db.exists("Purchase Taxes and Charges Template", {"title": title, "company": company_name}):
            return
        pt = frappe.new_doc("Purchase Taxes and Charges Template")
        pt.title = title
        pt.company = company_name
        pt.is_default = 1 if is_default else 0
        if tax_category_name:
            pt.tax_category = tax_category_name
        
        # Get cost center
        cost_center = get_cost_center(company_name)
        
        if not cost_center:
            frappe.log_error(f"Could not find cost center for company {company_name}", "Cost Center Creation Error")
            print(f"⚠️ Skipping purchase template creation for {title} due to missing cost center")
            return
        
        if not account:
            frappe.log_error(f"Account is None for purchase template {title}", "Account Creation Error")
            print(f"⚠️ Skipping purchase template creation for {title} due to missing account")
            return
        
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

    ensure_purchase_template("IVA 16%",16.0, a_input_16, "IVA 16%",   regime.startswith("normal"))
    ensure_purchase_template("IVA 5%",5.0, a_input_5,  "IVA 5%", regime.startswith("reduzida"))
    ensure_purchase_template("IVA 0% (Isento)",  0.0, a_input_0,  "IVA 0% (Isento)",   regime.startswith("isento"))

    # Ensure only one template per company is marked as default
    def ensure_single_default_template(doctype: str, default_title: str):
        try:
            # Unset all defaults for this company
            frappe.db.sql(f"UPDATE `tab{doctype}` SET is_default = 0 WHERE company = %s", (company_name,))
            frappe.db.commit()
            
            # Set the correct default
            frappe.db.sql(f"UPDATE `tab{doctype}` SET is_default = 1 WHERE company = %s AND title = %s", (company_name, default_title))
            frappe.db.commit()
            
            # Verify the default was set
            default_exists = frappe.db.get_value(doctype, {"company": company_name, "title": default_title, "is_default": 1}, "name")
            if not default_exists:
                frappe.log_error(f"Failed to set default {doctype} for company {company_name}", "Tax Template Default Error")
        except Exception as e:
            frappe.log_error(f"Error setting default {doctype}: {str(e)}", "Tax Template Default Error")
    
    ensure_single_default_template("Sales Taxes and Charges Template", default_title)
    ensure_single_default_template("Purchase Taxes and Charges Template", default_title)

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

    ensure_item_tax_template("IVA 16%",16.0)
    ensure_item_tax_template("IVA 5%",5.0)
    ensure_item_tax_template("IVA 0% (Isento)",0.0)

    def ensure_default_tax_rule():
        # Get the profile to determine the regime
        profile = _get_profile(create_if_missing=True)
        regime = (profile.tax_regime or "Normal").lower()
        
        # Determine default template title by regime
        if regime.startswith("normal"):
            template_title = "IVA 16%"
            category_title = "IVA 16%"
        elif regime.startswith("isento"):
            template_title = "IVA 0% (Isento)"
            category_title = "IVA 0% (Isento)"
        elif regime.startswith("reduzida") or regime.startswith("reducida"):
            template_title = "IVA 5%"
            category_title = "IVA 5%"
        else:
            template_title = "IVA 0% (Isento)"
            category_title = "IVA 0% (Isento)"

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

        # Check if Sales Tax Rule already exists
        sales_exists = frappe.db.exists(
            "Tax Rule",
            {
                "company": company_name,
                "tax_type": "Sales",
                "tax_category": tax_category_name,
                "sales_tax_template": sales_template,
            },
        )
        
        if not sales_exists:
            # Create Sales Tax Rule
            tr_sales = frappe.new_doc("Tax Rule")
            tr_sales.company = company_name
            tr_sales.tax_type = "Sales"
            tr_sales.tax_category = tax_category_name
            tr_sales.sales_tax_template = sales_template
            tr_sales.priority = 1
            tr_sales.insert(ignore_permissions=True)
            print(f"✅ Created Sales Tax Rule for {template_title}")

        # Check if Purchase Tax Rule already exists
        purchase_exists = frappe.db.exists(
            "Tax Rule",
            {
                "company": company_name,
                "tax_type": "Purchase",
                "tax_category": tax_category_name,
                "purchase_tax_template": purchase_template,
            },
        )
        
        if not purchase_exists:
            # Create Purchase Tax Rule
            tr_purchase = frappe.new_doc("Tax Rule")
            tr_purchase.company = company_name
            tr_purchase.tax_type = "Purchase"
            tr_purchase.tax_category = tax_category_name
            tr_purchase.purchase_tax_template = purchase_template
            tr_purchase.priority = 1
            tr_purchase.insert(ignore_permissions=True)
            print(f"✅ Created Purchase Tax Rule for {template_title}")

    ensure_default_tax_rule()


def _ensure_banking_infrastructure(company_name: str, profile):
    """
    Unified function to create banking infrastructure including:
    - Mozambican bank accounts
    - Payment Methods based on user selection
    """
    try:
        # Create payment methods based on user selection
        _create_payment_methods(company_name, profile)
        
        print("✅ Banking infrastructure setup completed successfully")
        
    except Exception as e:
        frappe.log_error(f"Error setting up banking infrastructure: {str(e)}", "Banking Infrastructure Setup Error")


def _create_payment_methods(company_name: str, profile):
    """Create Mode of Payment records based on selected payment methods in the profile"""
    try:
        # Map profile fields directly to Mode of Payment name and IFRS MZ account numbers
        payment_method_number_map = {
            "payment_method_cash": ("Dinheiro (Cash)", "11.01.01"),
            "payment_method_bci": ("Banco BCI", "11.01.03"),
            "payment_method_millenium": ("Banco Millenium BIM", "11.01.04"),
            "payment_method_standard_bank": ("Banco Standard Bank", "11.01.05"),
            "payment_method_absa": ("Banco ABSA", "11.01.02"),
            "payment_method_emola": ("E-Mola", "11.01.12"),
            "payment_method_mpesa": ("M-Pesa", "11.01.11"),
            "payment_method_fnb": ("Banco FNB", "11.01.06"),
            "payment_method_moza": ("Moza Banco", "11.01.07"),
            "payment_method_letshego": ("Banco Letshego", "11.01.08"),
            "payment_method_first_capital": ("First Capital Bank", "11.01.09"),
            "payment_method_nedbank": ("Nedbank", "11.01.10"),
        }

        # Build selected set from profile
        selected_methods = []
        for field_name, (payment_method_name, account_number) in payment_method_number_map.items():
            if getattr(profile, field_name, 0):
                selected_methods.append((payment_method_name, account_number))
        
        if not selected_methods:
            print("ℹ️ No payment methods selected, skipping Payment Method creation")
            return
        
        print(f"🔄 Creating Payment Methods for: {', '.join([method[0] for method in selected_methods])}")
        

        for payment_method_name, account_number in selected_methods:
            # Determine Mode of Payment type
            if "Dinheiro" in payment_method_name or "Cash" in payment_method_name:
                mop_type = "Cash"
            elif "E-Mola" in payment_method_name or "M-Pesa" in payment_method_name:
                mop_type = "Bank"
            else:
                mop_type = "Bank"

            # Resolve account strictly by IFRS MZ number
            account = require_account_by_number(company_name, account_number, f"Mode of Payment: {payment_method_name}")

            # Create or update Mode of Payment idempotently
            existing_mop = frappe.db.exists("Mode of Payment", {"mode_of_payment": payment_method_name})
            if existing_mop:
                mop_doc = frappe.get_doc("Mode of Payment", existing_mop)
                mop_doc.enabled = 1
                mop_doc.type = mop_type
                # Ensure company-specific account row exists/updated
                updated = False
                for row in mop_doc.accounts:
                    if row.company == company_name:
                        if row.default_account != account:
                            row.default_account = account
                        updated = True
                        break
                if not updated:
                    mop_doc.append("accounts", {"company": company_name, "default_account": account})
                mop_doc.save(ignore_permissions=True)
                print(f"✅ Updated Mode of Payment: {payment_method_name} -> {account}")
                continue

            mop_doc = frappe.new_doc("Mode of Payment")
            mop_doc.mode_of_payment = payment_method_name
            mop_doc.enabled = 1
            mop_doc.type = mop_type
            mop_doc.append("accounts", {"company": company_name, "default_account": account})
            mop_doc.insert(ignore_permissions=True)
            print(f"✅ Created Mode of Payment: {payment_method_name} -> {account}")
        
        print(f"✅ Successfully created {len(selected_methods)} Modes of Payment")
        
    except Exception as e:
        frappe.log_error(f"Error creating Modes of Payment: {str(e)}", "Mode of Payment Creation Error")

def _ensure_hr_payroll_infrastructure(company_name: str):
    """Orchestrate payroll accounts, components, structure and IRPS slab linkage (idempotent)."""
    try:
        # 1) Ensure accounts/components/structure
        from erpnext_mz.setup.payroll import (
            ensure_payroll_chart_of_accounts,
            ensure_salary_components,
            ensure_salary_structure,
            link_irps_slab_to_component,
        )

        accounts = ensure_payroll_chart_of_accounts(company_name)
        components = ensure_salary_components(company_name, accounts)

        # 2) Ensure Income Tax Slab (IRPS) exists
        _ensure_income_tax_slab(company_name)

        # 3) Link IRPS slab to IRPS Salary Component
        link_irps_slab_to_component(company_name, "IRPS (Progressivo)")

        # 4) Ensure salary structure and attach all components
        ensure_salary_structure(company_name, components, structure_name="Folha Moçambique")

    except Exception as e:
        frappe.log_error(f"Error ensuring HR payroll infrastructure: {str(e)}", "HR Payroll Infra Error")


def _ensure_income_tax_slab(company_name: str):
    """Create Income Tax Slab for Mozambique (IRPS) if it doesn't exist"""
    try:
        # Validate company exists
        if not frappe.db.exists("Company", company_name):
            raise ValueError(f"Company '{company_name}' does not exist")
        
        # Check if Income Tax Slab already exists
        if frappe.db.exists("Income Tax Slab", "IRPS Moçambique (2025)"):
            print("✅ Income Tax Slab already exists: IRPS Moçambique (2025)")
            return
        
        # Validate MZN currency exists
        if not frappe.db.exists("Currency", "MZN"):
            raise ValueError("MZN currency does not exist. Please ensure MZN currency is created first.")
        
        # Create Income Tax Slab
        income_tax_slab = frappe.new_doc("Income Tax Slab")
        income_tax_slab.name = "IRPS Moçambique (2025)"
        income_tax_slab.company = company_name
        income_tax_slab.currency = "MZN"
        income_tax_slab.effective_from = "2025-01-01"
        income_tax_slab.allow_tax_exemption = 0
        income_tax_slab.standard_tax_exemption_amount = 0.0
        income_tax_slab.tax_relief_limit = 0.0
        income_tax_slab.disabled = 0
        income_tax_slab.docstatus = 1
        
        # Add tax slabs according to Mozambique IRPS rates for 2025
        # Source: Mozambique Tax Authority rates for 2025
        slabs_data = [
            {"from_amount": 0.0, "to_amount": 42000.0, "percent_deduction": 10.0},
            {"from_amount": 42001.0, "to_amount": 168000.0, "percent_deduction": 15.0},
            {"from_amount": 168001.0, "to_amount": 504000.0, "percent_deduction": 20.0},
            {"from_amount": 504001.0, "to_amount": 1512000.0, "percent_deduction": 25.0},
            {"from_amount": 1512001.0, "to_amount": 10000000000.0, "percent_deduction": 32.0}
        ]
        
        # Add slabs to the document
        for i, slab_data in enumerate(slabs_data):
            if slab_data["from_amount"] >= slab_data["to_amount"]:
                raise ValueError(f"Invalid slab {i+1}: from_amount ({slab_data['from_amount']}) must be less than to_amount ({slab_data['to_amount']})")
            
            income_tax_slab.append("slabs", {
                "from_amount": slab_data["from_amount"],
                "to_amount": slab_data["to_amount"],
                "percent_deduction": slab_data["percent_deduction"],
                "condition": ""
            })
        
        # Validate the document before inserting
        income_tax_slab.validate()
        
        # Insert the document
        income_tax_slab.insert(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error creating Income Tax Slab: {str(e)}", "Income Tax Slab Creation Error")


def _ensure_smtp_infrastructure(company_name: str):
    """Orchestrate SMTP infrastructure (idempotent)."""
    try:
        from erpnext_mz.setup.email_setup import ensure_smtp_setup
        email_result = ensure_smtp_setup(company_name)
        if not email_result.get("ok"):
            print(f"ℹ️ SMTP setup skipped: {email_result.get('message')}")
        else:
            print(f"✅ SMTP configured (Email Account: {email_result.get('account')})")
    except Exception as e:
        frappe.log_error(f"Error applying SMTP setup: {str(e)}", "SMTP Setup Error")

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
        "terms_and_conditions_of_sale",
        "payment_method_cash",
        "payment_method_bci",
        "payment_method_millenium",
        "payment_method_standard_bank",
        "payment_method_absa",
        "payment_method_emola",
        "payment_method_mpesa",
        "payment_method_fnb",
        "payment_method_moza",
        "payment_method_letshego",
        "payment_method_first_capital",
        "payment_method_nedbank",
    ]
    return {f: profile.get(f) for f in fields}


@frappe.whitelist()
def create_tax_masters_manually():
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"error": "No company found"}
    try:
        _create_tax_masters(company_name)
        return {"success": True, "message": "Tax masters created successfully"}
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def create_hr_payroll_infrastructure_manually():
    """Manual function to create HR tax masters for testing"""
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"error": "No company found"}
    
    try:
        _ensure_hr_payroll_infrastructure(company_name)
        return {"success": True, "message": "HR & Payroll infrastructure created successfully"}
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def ensure_cost_center_manually():
    """Manual function to ensure cost center exists for the company"""
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"error": "No company found"}
    
    try:
        cost_center = get_cost_center(company_name)
        if cost_center:
            return {"success": True, "message": f"Cost center ensured: {cost_center}"}
        else:
            return {"error": "Could not find or create cost center"}
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def create_banking_infrastructure_manually():
    """Manual function to create banking infrastructure for testing"""
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"error": "No company found"}
    
    try:
        profile = _get_profile(create_if_missing=True)
        if not profile:
            return {"error": "MZ Company Setup not found"}
        
        _ensure_banking_infrastructure(company_name, profile)
        return {"success": True, "message": "Banking infrastructure created successfully"}
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def trigger_onboarding_manually():
    """Manual function to trigger onboarding for testing"""
    try:
        # Set the trigger flag
        frappe.db.set_single_value("MZ Company Setup", "trigger_onboarding", 1)
        frappe.db.commit()
        
        return {"success": True, "message": "Onboarding trigger flag set. Refresh the page to see the onboarding dialog."}
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def ensure_smtp_infrastructure_manually():
    """Manual function to ensure SMTP infrastructure exists for the company"""
    try:
        company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
        if not company_name:
            return {"error": "No company found"}
        _ensure_smtp_infrastructure(company_name)
        return {"success": True, "message": "SMTP infrastructure ensured successfully"}
    except Exception as e:
        return {"error": str(e)}

@frappe.whitelist()
def should_trigger_onboarding():
    """Check if onboarding should be triggered after setup wizard completion"""
    try:
        # Check if MZ Company Setup exists
        if not frappe.db.exists("MZ Company Setup", "MZ Company Setup"):
            return {"should_trigger": False, "reason": "MZ Company Setup not found"}
        
        mz_setup = frappe.get_single("MZ Company Setup")
        
        # Check if already applied
        if mz_setup.is_applied:
            return {"should_trigger": False, "reason": "Already applied"}
        
        # Check if trigger flag is set
        trigger_flag = getattr(mz_setup, 'trigger_onboarding', False)
        
        if not trigger_flag:
            return {"should_trigger": False, "reason": "Trigger flag not set"}
        
        # Get current status
        status = get_status()
        
        # Clear the trigger flag
        frappe.db.set_single_value("MZ Company Setup", "trigger_onboarding", 0)
        frappe.db.commit()
        
        return {
            "should_trigger": True,
            "status": status,
            "reason": "Setup wizard completed, triggering onboarding"
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking onboarding trigger: {str(e)}", "MZ Onboarding Trigger Check Error")
        return {"should_trigger": False, "reason": f"Error: {str(e)}"}



def trigger_onboarding_after_setup(args=None):
    """Trigger onboarding after setup wizard is completed"""
    try:
        # Check if company exists (setup wizard should have created it)
        company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
        if not company_name:
            frappe.log_error("No company found after setup wizard completion", "MZ Onboarding Trigger Error")
            return
        
        # Check if MZ Company Setup already exists and is applied
        if frappe.db.exists("MZ Company Setup", "MZ Company Setup"):
            mz_setup = frappe.get_single("MZ Company Setup")
            if mz_setup.is_applied:
                # Already completed, no need to trigger onboarding
                return
        
        # Set a flag to trigger onboarding on next app load
        frappe.db.set_single_value("MZ Company Setup", "trigger_onboarding", 1)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error triggering MZ onboarding after setup: {str(e)}", "MZ Onboarding Trigger Error")


def _create_print_formats():
    """Create Mozambique-specific print formats"""
    try:
        # Step 1: Disable existing print formats to avoid conflicts
        from erpnext_mz.setup.disable_existing_print_formats import prepare_for_mozambique_print_formats
        preparation_result = prepare_for_mozambique_print_formats()
        
        # Step 2: Create all professional print formats
        from erpnext_mz.setup.comprehensive_print_formats import create_all_mozambique_print_formats
        created_formats = create_all_mozambique_print_formats()
        frappe.log_error(f"Criados {len(created_formats)} formatos de impressão para Moçambique.", "Print Format Creation")
        
    except Exception as e:
        frappe.log_error(f"Erro ao criar formatos de impressão: {str(e)}", "Print Format Creation")
