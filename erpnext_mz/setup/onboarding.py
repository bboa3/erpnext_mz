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

    # C. Create print formats
    _create_print_formats()

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
        company_abbr = company_doc.abbr
        tax_id = company_doc.tax_id or (profile.tax_id or "")
        phone = profile.phone or ""
        email = profile.email or ""
        website = (getattr(profile, "website", None) or getattr(company_doc, "website", None) or "")
        line1 = profile.address_line1 or ""
        line2 = profile.neighborhood_or_district or ""
        city = profile.city or ""
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

        # Build header HTML with three sections: Logo (left), Company Info (center), Address (right)
        header_html = [
            "<table style=\"width:100%; border-collapse:collapse; margin-bottom:20px;\">",
            "<tr>",
        ]
        
        # Left section: Logo and NUIT
        header_html.append("<td style=\"width:150px; vertical-align:top; text-align:left;\">")
        if logo_url:
            header_html.append(f"<img src=\"{logo_url}\" style=\"max-height:80px; max-width:140px; object-fit:contain; margin-bottom:5px;\"/>")
        if tax_id:
            header_html.append(f"<div style=\"font-size:10pt; font-weight:bold; background-color:#f0f0f0; padding:3px; border:1px solid #ccc; text-align:center; margin-top:5px;\">NUIT: {frappe.utils.escape_html(tax_id)}</div>")
        header_html.append("</td>")
        
        # Center section: Company name and contact details
        header_html.append("<td style=\"vertical-align:top; text-align:center; padding:0 20px;\">")
        header_html.append(f"<div style=\"font-weight:bold; font-size:14pt; margin-bottom:8px;\">{frappe.utils.escape_html(company_name)}</div>")
        
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
            header_html.append(f"<div style=\"font-size:10pt; line-height:1.4;\">{'<br>'.join(contact_details)}</div>")
        header_html.append("</td>")
        
        # Right section: Company address
        header_html.append("<td style=\"width:200px; vertical-align:top; text-align:right;\">")
        address_parts = [p for p in [line1, line2, f"{city} {province}".strip()] if p]
        if address_parts:
            for part in address_parts:
                header_html.append(f"<div style=\"font-size:10pt; line-height:1.3;\">{frappe.utils.escape_html(part)}</div>")
        header_html.append(f"<div style=\"font-size:10pt; line-height:1.3; font-weight:bold;\">Mozambique</div>")
        header_html.append("</td>")
        
        header_html.append("</tr>")
        header_html.append("</table>")
        header_html = "".join(header_html)

        # Get terms and conditions text
        terms_text = getattr(profile, "terms_and_conditions_of_sale", None) or ""

        # Build footer HTML (without terms and conditions)
        footer_html = []
        
        # Add "Processado pelo programa ERPNext Moçambique" (almost invisible)
        footer_html.append("<div style=\"color:#e0e0e0; font-size:8pt; margin-bottom:8px;\">Processado pelo programa ERPNext Moçambique</div>")
        
        # Add company address and contacts in line
        footer_contact_parts = []
        if line1:
            footer_contact_parts.append(frappe.utils.escape_html(line1))
        if line2:
            footer_contact_parts.append(frappe.utils.escape_html(line2))
        if city and province:
            footer_contact_parts.append(f"{frappe.utils.escape_html(city)}, {frappe.utils.escape_html(province)}")
        if phone:
            footer_contact_parts.append(f"Tel: {frappe.utils.escape_html(phone)}")
        if email:
            footer_contact_parts.append(f"Email: {frappe.utils.escape_html(email)}")
        
        if footer_contact_parts:
            footer_html.append(f"<div style=\"font-size:9pt; color:#666;\">{' | '.join(footer_contact_parts)}</div>")
        
        footer_content = "".join(footer_html)

        # Create or update Letter Head
        if not frappe.db.exists("Letter Head", lh_name):
            lh = frappe.new_doc("Letter Head")
            lh.letter_head_name = lh_name
            lh.company = company_name
            lh.is_default = 1
            lh.disabled = 0
            lh.source = "HTML"
            lh.footer_source = "HTML"
            lh.content = header_html
            lh.footer = footer_content
            lh.insert(ignore_permissions=True)
        else:
            lh = frappe.get_doc("Letter Head", lh_name)
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
            if getattr(company_doc, "default_letter_head", None) != lh_name:
                company_doc.db_set("default_letter_head", lh_name, commit=True)
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
        
        # Create HR tax masters for Mozambique
        _create_hr_tax_masters(company_name)

        # Set defaults by regime
        regime = (profile.tax_regime or "Normal").lower()
        if regime.startswith("normal"):
            default_template = "Regime Normal (16%)"
        elif regime.startswith("isento"):
            default_template = "IVA a Entregar 0%"
        else:
            default_template = "IVA a Entregar 0%"

        # Note: ERPNext uses is_default flag on templates, not Company fields
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure tax infra failed")


def _create_tax_masters(company_name: str):
    # Create full set of masters as per wizard.md for new sites
    def ensure_account(name: str, root_type: str, account_type: str | None = None, parent_account: str | None = None, account_number: str | None = None):
        try:
            if frappe.db.exists("Account", {"company": company_name, "account_name": name}):
                return frappe.get_value("Account", {"company": company_name, "account_name": name}, "name")
            
            # Find parent account
            parent_acc = None
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
                else:
                    # Get the existing parent account name
                    parent_acc = frappe.get_value("Account", {"company": company_name, "account_name": parent_account}, "name")
            
            acc = frappe.new_doc("Account")
            acc.company = company_name
            acc.account_name = name
            acc.root_type = root_type
            acc.is_group = 0  # Tax accounts should not be groups
            if account_type:
                acc.account_type = account_type
            if account_number:
                acc.account_number = account_number
            if parent_acc:
                acc.parent_account = parent_acc
            acc.insert(ignore_permissions=True)
            return acc.name
        except Exception as e:
            frappe.log_error(f"Error creating account {name}: {str(e)}", "Account Creation Error")
            return None

    # Get company abbreviation for account naming
    company_abbr = frappe.get_value("Company", company_name, "abbr") or "MS"
    
    # Find the existing parent tax account (language-dependent name)
    def find_parent_tax_account():
        """Find the existing parent tax account for tax accounts"""
        # ERPNext creates a VAT account during company setup, we'll use its parent
        vat_account_name = "VAT"
        vat_account = frappe.db.exists("Account", {"company": company_name, "account_name": vat_account_name})
        
        if vat_account:
            # Get the parent account of the VAT account
            parent_account = frappe.get_value("Account", vat_account, "parent_account")
            if parent_account:
                # Get the account name without company abbreviation
                parent_account_name = frappe.get_value("Account", parent_account, "account_name")
                return parent_account_name
        
        # If no VAT account found, return None
        return None
    
    # Find the parent tax account (same for both Liability and Asset)
    tax_parent = find_parent_tax_account()
    
    # If no parent tax account found, log error and return
    if not tax_parent:
        frappe.log_error(f"Could not find parent tax account for company {company_name}. Looking for VAT - {company_abbr} account and its parent.", "Tax Account Parent Error")
        return
    
    # Create tax accounts with the same parent account for both Liability and Asset
    a_output_16 = ensure_account(f"IVA a Entregar 16% - {company_abbr}", "Liability", "Tax", tax_parent, "24.01.01")
    a_output_5 = ensure_account(f"IVA a Entregar 5% - {company_abbr}", "Liability", "Tax", tax_parent, "24.01.02")
    a_output_0 = ensure_account(f"IVA a Entregar 0% - {company_abbr}", "Liability", "Tax", tax_parent, "24.01.03")
    a_input_16 = ensure_account(f"IVA Dedutível 16% - {company_abbr}", "Asset", "Tax", tax_parent, "13.01.01")
    a_input_5 = ensure_account(f"IVA Dedutível 5% - {company_abbr}", "Asset", "Tax", tax_parent, "13.01.02")
    a_input_0 = ensure_account(f"IVA Dedutível 0% - {company_abbr}", "Asset", "Tax", tax_parent, "13.01.03")
    
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


def _create_hr_tax_masters(company_name: str):
    """Create HR tax masters for Mozambique including Income Tax Slab and other HR tax structures"""
    try:
        # Create Income Tax Slab for Mozambique (IRPS)
        _ensure_income_tax_slab(company_name)
        
        # Create other HR tax structures as needed
        # TODO: Add other HR tax masters like INSS, etc.
        
        print("✅ HR Tax Masters created successfully")
        
    except Exception as e:
        frappe.log_error(f"Error creating HR tax masters: {str(e)}", "HR Tax Masters Creation Error")


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
    ]
    return {f: profile.get(f) for f in fields}


@frappe.whitelist()
def create_hr_tax_masters_manually():
    """Manual function to create HR tax masters for testing"""
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"error": "No company found"}
    
    try:
        _create_hr_tax_masters(company_name)
        return {"success": True, "message": "HR tax masters created successfully"}
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def create_income_tax_slab_manually():
    """Manual function to create Income Tax Slab for testing"""
    company_name = frappe.defaults.get_user_default("company") or frappe.db.get_default("company")
    if not company_name:
        return {"error": "No company found"}
    
    try:
        _ensure_income_tax_slab(company_name)
        return {"success": True, "message": "Income Tax Slab created successfully"}
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
            "status": status.get("message", {}),
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
        from erpnext_mz.setup.create_print_formats import create_mozambique_sales_invoice_print_format
        
        # Create Sales Invoice print format if it doesn't exist
        if not frappe.db.exists("Print Format", "Mozambique Sales Invoice"):
            create_mozambique_sales_invoice_print_format()
            frappe.log_error("Created Mozambique Sales Invoice print format", "Print Format Creation")
        
    except Exception as e:
        frappe.log_error(f"Error creating print formats: {str(e)}", "Print Format Creation")
