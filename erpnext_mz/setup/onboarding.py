import frappe
from frappe import _
from frappe.utils.data import cint
from erpnext_mz.utils.account_utils import get_cost_center, require_account_by_number
from erpnext_mz.setup.terms_loader import ensure_terms_from_json
import os
import shutil


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
        3: ["logo"],
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

    # Ensure Terms & Conditions
    _ensure_terms_and_conditions(company_name)
    
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


def _ensure_logo_is_public(file_url: str) -> str:
    """
    Ensure a logo file is public (not private) for wkhtmltopdf access.
    
    Args:
        file_url: File URL (e.g., "/files/logo.png" or "/private/files/logo.png")
    
    Returns:
        str: Public file URL
    """
    if not file_url:
        return file_url
    
    # Already public
    if not file_url.startswith('/private/'):
        return file_url
    
    try:
        from frappe.utils import get_site_path
        
        # Try to get the File document with the private URL
        try:
            file_doc = frappe.get_doc("File", {"file_url": file_url})
        except frappe.DoesNotExistError:
            # File document doesn't exist with this URL
            # Maybe it was already converted - try to find with public URL
            public_url = file_url.replace("/private/files/", "/files/")
            try:
                file_doc = frappe.get_doc("File", {"file_url": public_url})
                # Found with public URL - it's already converted
                return public_url
            except frappe.DoesNotExistError:
                # File doesn't exist at all
                frappe.log_error(f"Logo file not found: {file_url}", "Logo Public Conversion")
                return file_url
        
        if not file_doc.is_private:
            # Already marked as public
            return file_doc.file_url
        
        # Get file paths
        private_path = get_site_path('private', 'files', file_doc.file_name)
        public_path = get_site_path('public', 'files', file_doc.file_name)
        
        # Check if file exists in private folder
        if not os.path.exists(private_path):
            frappe.log_error(f"Logo file not found at: {private_path}", "Logo Public Conversion")
            return file_url
        
        # Copy to public folder (don't delete from private in case it's referenced elsewhere)
        shutil.copy2(private_path, public_path)
        
        # Update File document
        file_doc.is_private = 0
        file_doc.file_url = "/files/" + file_doc.file_name
        file_doc.save(ignore_permissions=True)
        
        # Commit the change immediately to ensure it persists
        frappe.db.commit()

        return file_doc.file_url
        
    except Exception as e:
        frappe.log_error(
            f"Error making logo public: {str(e)}\n{frappe.get_traceback()}",
            "Logo Public Conversion Error"
        )
        return file_url


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

        company_doc = frappe.get_doc("Company", company_name)
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

        # Build header HTML to match mockup structure
        header_html = []
        header_html.append("<table class=\"hdr\" style=\"width:100%; border-collapse:collapse; font-family: Montserrat, Arial, sans-serif;\">")
        header_html.append("<tr>")
        # Left brand
        header_html.append("<td>")
        header_html.append("<div class=\"brand\">")
        # Logo (if any) else geometric mark
        if logo_url:
            header_html.append(f"<img src=\"{logo_url}\" style=\"max-height:88px; max-width:130px; object-fit:contain; margin-right:6px;\" alt=\"logo\"/>")
        header_html.append("</div>")
        header_html.append("</td>")
        # Right company meta
        header_html.append("<td class=\"right\" style=\"text-align:right;\">")
        header_html.append(f"<div class=\"company-name\" style=\"font-size:16pt; font-weight:700; letter-spacing:.08em; text-transform:uppercase; line-height:1.1; margin-bottom:1mm;\">{frappe.utils.escape_html(company_name)}</div>")
        meta_line = []
        if line1:
            meta_line.append(frappe.utils.escape_html(line1))
        if line2:
            meta_line.append(frappe.utils.escape_html(line2))
        loc = ", ".join([p for p in [city, province] if p])
        if loc:
            meta_line.append(frappe.utils.escape_html(loc))
        if meta_line:
            header_html.append(f"<div class=\"company-meta small\" style=\"font-size:9pt; letter-spacing:0.16em; padding-left:6em;\">{', '.join(meta_line)}</div>")
        if tax_id:
            header_html.append(f"<div class=\"nuit small\" style=\"margin-top:2mm; font-size:9pt; letter-spacing:0.16em;\">NUIT: {frappe.utils.escape_html(tax_id)}</div>")
        header_html.append("</td>")
        header_html.append("</tr>")
        header_html.append("</table>")
        header_html = "".join(header_html)

        # Build footer HTML (without terms and conditions)
        footer_html = []
        
        # Mockup footer: line + centered contacts + subtext
        footer_contact_parts = []
        if line1:
            footer_contact_parts.append(frappe.utils.escape_html(line1))
        if city or province:
            footer_contact_parts.append(" ".join([p for p in [frappe.utils.escape_html(city or ""), frappe.utils.escape_html(province or "")] if p]).strip())
        if phone:
            footer_contact_parts.append(frappe.utils.escape_html(phone))
        if email:
            footer_contact_parts.append(frappe.utils.escape_html(email))
        if website:
            footer_contact_parts.append(frappe.utils.escape_html(website))

        footer_html.append("<div class=\"footline\" style=\"height:0.6mm; background:#111; margin-bottom:3mm;\"></div>")
        if footer_contact_parts:
            footer_html.append(f"<div class=\"foot\" style=\"text-align:center; font-size:10pt; color:#111;\">{' | '.join([p for p in footer_contact_parts if p])}</div>")
        footer_html.append("<div class=\"sub\" style=\"text-align:center; font-size:9pt; color:rgba(0, 0, 0, .50); margin-top:1mm;\">Processado pelo programa MozEconomia Cloud</div>")

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

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Apply branding failed")


def _ensure_terms_and_conditions(company_name: str):
    """Load terms and conditions and set Factura as default selling terms.
    
    This function is idempotent - safe to call multiple times without causing duplicates.
    """
    try:
        from erpnext_mz.setup.terms_loader import ensure_terms_and_set_defaults
        
        result = ensure_terms_and_set_defaults(
            company_name,
            json_path=None,  # Use default packaged file
            commit=True,
            update_existing=False,  # Idempotent: don't update existing terms
            set_factura_as_default=True  # Set Factura as default
        )

        if result.get("ok"):
            print(
                f"Terms setup: created={result['terms_loading']['created']}, "
                f"updated={result['terms_loading']['updated']}, "
                f"skipped={result['terms_loading']['skipped']}"
            )
        else:
            print(f"Terms setup failed: {result.get('error')}")
            
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Ensure Terms from JSON failed during apply_all")
    return

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