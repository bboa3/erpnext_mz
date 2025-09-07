# ERPNext Mozambique Compliance Roadmap (2025) — Checkable Checklist
> From zero to a fully built, tax-compliant, multi-tenant ERPNext SaaS for Mozambique.

## Phase 1 — Planning & Infrastructure
* [x] Team, scope, environments, security, backups, monitoring, DR.
  **Acceptance:** AWS account hardening + runbook exists; restore drill scheduled.
* [x] **Docker foundations (multi-service compose)** (🧩 CODE ops)
  * Mount `./apps` and `sites/` into all frappe services; add healthchecks.
  * Bake Node 18 + Yarn inside images or post-install step for asset builds.
    **Acceptance:** `bench build` works in `backend`; app code persists across restarts.
* [x] **S3 buckets** for files/backups with **Object Lock/WORM** for compliance (ops).
  **Acceptance:** lifecycle + cross-region replication configured; retention policy documented (10 years).

## Phase 2 — Core ERPNext Installation
* [x] Install ERPNext; create **dev/staging/prod** sites; enable DNS multi-tenant. (🖱️ UI + 🧩 CODE ops)
* [x] Language: **pt-MZ** (start from pt-BR CSV → adapt to pt-MZ) (🖱️ UI import).
  **Acceptance:** site shows PT; common labels localized to Moz context.
* [x] Email (SMTP), timezone **Africa/Maputo**, currency **MZN**, **fiscal year** (confirm with accountant; not fixed in report).
  **Note:** Fiscal year start/end **not specified in the report** → verify with AT/contador.

## Phase 3 — Mozambique Localization (Accounting & Tax)
* [X] **IFRS Chart of Accounts** (🖱️ UI or import template).
  **Acceptance:** COA ready; GL/BS/P\&L run clean.
* [X] **Company Setup Wizard** (🧩 CODE + 🖱️ UI)
  * **MZ Company Setup** Single DocType with comprehensive company configuration
  * **3-Step Onboarding Dialog**: Tax & Address → Contacts → Branding (optional)
  * **Auto-configuration**: Tax accounts, templates, categories, and rules based on selected tax regime
  * **Letter Head Generation**: Custom HTML with logo, company details, and NUIT
  * **Terms & Conditions**: Automatic creation and assignment to company
    **Acceptance:** Complete company setup in 3 steps; all tax infrastructure auto-created.
* [X] **VAT setup** (🧩 CODE + 🖱️ UI)
  * **Tax Accounts**: Auto-created under "Duties and Taxes" parent with company abbreviations
    * `13.01.01 - IVA Dedutível 16% - [COMPANY]` (Asset, 16%)
    * `13.01.02 - IVA Dedutível 5% - [COMPANY]` (Asset, 5%)
    * `13.01.03 - IVA Dedutível 0% - [COMPANY]` (Asset, 0%)
    * `24.01.01 - IVA a Entregar 16% - [COMPANY]` (Liability, 16%)
    * `24.01.02 - IVA a Entregar 5% - [COMPANY]` (Liability, 5%)
    * `24.01.03 - IVA a Entregar 0% - [COMPANY]` (Liability, 0%)
  * **Tax Categories**: `IVA 16%`, `IVA 5%`, `IVA 0% (Isento)`
  * **Sales/Purchase Templates**: Auto-created with correct accounts and rates
  * **Item Tax Templates**: Matching tax categories with appropriate rates
  * **Tax Rules**: Default rules for all customers/items with priority-based application
    **Acceptance:** Tax applied correctly on SO/SI/PI; reports reconcile; regime-based defaults.
* [ ] **Custom Fields** (🧩 CODE)
  * Customer/Supplier **NUIT**.
    **Acceptance:** Fields visible and required where specified.
* [ ] **Sequential numbering** (Naming Series) (🖱️ UI).
  **Acceptance:** "FT-YYYY-####" issues sequentially; no duplicates.

## Phase 4 — HR & Payroll Compliance
* [ ] **INSS**: Empregador 4%, Empregado 3% (🖱️ UI components/structures).
  **Acceptance:** Payslips compute correct INSS.
* [ ] **IRPS progressive** 10/15/20/25/32% (🖱️ UI tables; verify latest tables with contabilista)
  **Acceptance:** Payslips compute correct IRPS.
* [ ] **Benefits in kind** (vehicle, housing, insurance…) (🖱️ UI fields;)
  **Acceptance:** Valuation in **MZN**; included in gross and SAF-T mapping.
<!-- Removed: Leave policies for simplicity -->

## Phase 5 — Custom App: `erpnext_mz` (Compliance Logic)
* [X] App skeleton installed on all sites (🧩 CODE).
  **Acceptance:** `bench --site <site> list-apps` shows `erpnext_mz`.
* [X] **Company Setup Wizard Implementation** (🧩 CODE)
  * **DocType**: `MZ Company Setup` (Single DocType) with fields for tax, address, contacts, branding
  * **Frontend**: `mz_onboarding.js` with 3-step dialog system
  * **Backend**: `onboarding.py` with comprehensive configuration logic
  * **Features**:
    - **Step 1**: Tax regime selection, NUIT, company address
    - **Step 2**: Contact information (phone, email, website)
    - **Step 3**: Branding (logo, terms & conditions) - optional
    - **Auto-apply**: Complete ERPNext configuration based on wizard data
    - **Idempotent**: Safe to run multiple times, updates existing records
  **Acceptance:** System managers can complete company setup in guided wizard; all tax infrastructure auto-created.
* [X] **Comprehensive Professional Print Formats** (🧩 CODE)
  * **14 Professional Print Formats**: Complete coverage of all essential business documents
    - **Sales Documents**: Fatura (MZ), Encomenda de Venda (MZ), Guia de Remessa (MZ), Orçamento (MZ)
    - **Purchase Documents**: Factura de Compra (MZ), Encomenda de Compra (MZ), Recibo de Compra (MZ)
    - **Inventory Documents**: Entrada de Stock (MZ), Pedido de Material (MZ)
    - **Financial Documents**: Entrada de Pagamento (MZ), Lançamento Contabilístico (MZ)
    - **HR Documents**: Recibo de Vencimento (MZ)
    - **Master Data**: Cliente (MZ), Fornecedor (MZ)
  * **Advanced Features**:
    - **QR Code Integration**: Automatic QR code generation with document validation links
    - **Document Validation API**: Public endpoint for QR code validation (`/qr_validation`)
    - **Professional Design**: Clean, minimalist UI with consistent branding
    - **Bilingual Support**: Portuguese (MZ) and English labels
    - **Tax Compliance**: NUIT display, tax breakdown, Mozambique-specific formatting
    - **Responsive Layout**: Optimized for both screen and print
  * **Technical Implementation**:
    - **Modular Template System**: Base `PrintFormatTemplate` class for consistency
    - **Jinja2 Templates**: Dynamic content generation with macros and conditional rendering
    - **CSS Framework**: Professional styling with print-optimized layouts
    - **QR Code Generation**: `pyqrcode` library with HMAC-secured validation links
    - **Automatic Management**: Scripts to disable existing formats and enable Mozambique formats
  * **Integration & Management**:
    - **Auto-Creation**: All formats created during company setup wizard
    - **Exclusive Enablement**: Mozambique formats are the only enabled options (de facto defaults)
    - **Self-Maintaining**: Automatic enforcement of Mozambique-only policy
    - **Verification System**: Comprehensive scripts to verify setup integrity
  * **Security Features**:
    - **HMAC Validation**: Secure document validation with tamper-proof hashing
    - **Public API**: Whitelisted methods for document verification
    - **Audit Trail**: Complete logging of QR code generation and validation
  **Acceptance:** All 14 print formats created and enabled; QR codes working; validation API functional; Mozambique formats automatically selected as defaults.
<!-- Removed: Integrity / Checksums (anti-tamper) -->
* [ ] **SAF-T (Vendas & Folha) XML generator** (🧩 CODE Doctype + scheduler)
  * Implement schemas; validate; archive monthly file to S3 (WORM).
  * **Variance rule**: folha vs vendas **≤ 3%**; flag/block if exceeded.
    **Acceptance:** XML passes schema; monthly job produces files; variance job enforces rule.
* [ ] **AT Integration** (when API/format available) (🧩 CODE)
  * Post-submit hook transmits invoice/folha to AT or exports for **e-Declaração**.
  * Retry, error queue, status dashboard.
    **Acceptance:** Success/failure statuses tracked; re-tries; audit log. 
* [ ] **NUIT validation** (🖱️ UI Client Script or 🧩 CODE)
  **Acceptance:** Invalid NUIT blocked in form.

## Phase 6 — Data Integrity, Archiving & Backups
* [ ] **Immutable numbering & cancel policy** (🖱️ UI + 🧩 CODE guard)
  **Acceptance:** Posted invoices cannot be edited; only credit notes reverse.
* [ ] **Signed audit trail** for critical DocTypes (🧩 CODE: logging hash + metadata)
  **Acceptance:** Tamper-evident logs exist for SI/Payroll Entry.
* [X] **Monthly archives to S3** (SAF-T, audit logs) with **10-year retention** (ops).
  **Acceptance:** Glacier/locking verified; restore drill passes.

## Phase 7 — Certification with AT
* [ ] Dossier (arch, security, flows, sample invoices, SAF-T) (🧩 CODE + docs).
* [ ] Staging tenant for certification; iterate until pass.
* [ ] **Record AT Certification ID** and show on invoice print (🖱️ UI).
  **Acceptance:** ID displayed on all fiscal prints.

## Phase 8 — SaaS Readiness (Multi-Tenant Ops)
* [ ] **Automated site provisioning** (🧩 CODE ops)
  * Script: `bench new-site` + install apps.
    **Acceptance:** New tenant ready in <5 min, isolated DB/files.
* [ ] **Billing** (Stripe/MPesa/Bank) (🧩 CODE)
  **Acceptance:** Subscriptions created; usage tracked.
* [ ] **CI/CD** (tests, build, migrate per site) (🧩 CODE)
  **Acceptance:** Pipeline green; canary/blue-green works.
* [ ] **Observability** (metrics/alerts/logs) (ops)
  **Acceptance:** Alarms on queues, workers, request latency.

## Phase 9 — Go-Live & Continuous Compliance
* [ ] Tenant onboarding; opening balances, master data.
* [ ] Training (Accounting, Sales, HR/Payroll).
* [ ] **Monthly ops checklist** (🖱️ UI + 🧩 CODE jobs):
  * Transmit invoices to AT / verify ACK.
  * Close payroll; **≤ 3%** variance vs sales.
  * Generate & archive **SAF-T (Vendas & Folha)**; submit to portal if required.
* [ ] Update VAT/IRPS/INSS tables when government changes (UI).
* [ ] Quarterly: restore test, security review, cost/perf tuning.

---

## Company Setup Wizard - Technical Implementation

### Architecture Overview
The Company Setup Wizard is implemented as a comprehensive onboarding system that guides users through Mozambique-specific ERPNext configuration.

### Core Components

#### 1. **MZ Company Setup DocType** (`apps/erpnext_mz/erpnext_mz/doctype/mz_company_setup/`)
- **Type**: Single DocType (one record per site)
- **Purpose**: Stores all company configuration data collected during onboarding
- **Key Fields**:
  - Tax information: `tax_id` (NUIT), `tax_regime`
  - Address: `address_line1`, `address_line2`, `city`, `province`, `country`
  - Contacts: `phone`, `email`, `website`
  - Branding: `company_logo`, `terms_and_conditions_of_sale`
  - Progress tracking: `step1_complete`, `step2_complete`, `step3_skipped`, `is_applied`

#### 2. **Frontend Dialog System** (`apps/erpnext_mz/erpnext_mz/public/js/mz_onboarding.js`)
- **Framework**: Frappe UI Dialog API
- **Structure**: 3-step progressive dialog system
- **Features**:
  - Non-dismissable dialogs (except optional Step 3)
  - Real-time validation and data persistence
  - Automatic progression between steps
  - Error handling and user feedback

#### 3. **Backend Configuration Engine** (`apps/erpnext_mz/erpnext_mz/setup/onboarding.py`)
- **Main Function**: `apply_all()` - orchestrates complete ERPNext configuration
- **Key Methods**:
  - `_update_company_tax_id()`: Sets company NUIT
  - `_ensure_address()`: Creates/updates company address and contact info
  - `_apply_branding()`: Generates letterhead and terms & conditions
  - `_create_tax_masters()`: Creates complete tax infrastructure

#### 4. **Tax Infrastructure Auto-Creation**
The wizard automatically creates a complete tax setup based on the selected regime:

**Tax Accounts** (under "Duties and Taxes" parent):
- Asset accounts: `13.01.01-03` (IVA Dedutível 16%/5%/0%)
- Liability accounts: `24.01.01-03` (IVA a Entregar 16%/5%/0%)

**Tax Templates & Categories**:
- Sales/Purchase tax templates with correct rates and accounts
- Tax categories for different regimes
- Item tax templates for product categorization
- Tax rules for automatic tax application

#### 5. **Boot Session Integration** (`apps/erpnext_mz/erpnext_mz/setup/boot.py`)
- Exposes onboarding status to frontend
- Triggers wizard for System Managers/Administrators
- Provides real-time status updates

#### 6. **Comprehensive Professional Print Formats System** (`apps/erpnext_mz/erpnext_mz/setup/`)
- **Complete Print Format Coverage**: 14 professional formats for all business documents
- **Modular Architecture**: Base `PrintFormatTemplate` class with specialized implementations
- **QR Code Integration**: Automatic generation with document validation API
- **Template Engine**: Jinja2 with professional CSS and responsive design
- **Management System**: Automatic creation, exclusive enablement, and verification
- **Integration**: Auto-created during company setup wizard with self-maintaining enforcement

### Data Flow
1. **User Access**: System Manager/Administrator logs in
2. **Status Check**: Boot session checks if onboarding is complete
3. **Dialog Trigger**: If incomplete, wizard dialogs are shown
4. **Data Collection**: User fills forms, data saved to Single DocType
5. **Configuration**: `apply_all()` function configures ERPNext
   - Updates company information (NUIT, address, contacts)
   - Creates tax infrastructure (accounts, templates, rules)
   - Generates letterhead and terms & conditions
   - **Creates professional print formats**
6. **Completion**: Wizard marked as complete, no longer shown

### Key Features
- **Idempotent**: Safe to run multiple times, updates existing records
- **Resumable**: Progress saved after each step
- **Comprehensive**: Covers all essential Mozambique tax and company setup
- **User-Friendly**: Guided interface with clear instructions
- **Error-Resistant**: Handles edge cases and provides meaningful feedback

---

## Professional Print Formats System - Technical Implementation

### Architecture Overview
The Professional Print Formats System provides comprehensive coverage of all essential business documents with Mozambique-specific compliance requirements, QR code integration, and professional design.

### Core Components

#### 1. **Print Format Templates** (`apps/erpnext_mz/erpnext_mz/setup/print_format_templates.py`)
- **Base Class**: `PrintFormatTemplate` with common methods for consistency
- **Modular Design**: Reusable components for headers, footers, customer details, items tables, totals, and QR codes
- **CSS Framework**: Professional styling with print-optimized layouts
- **Macro System**: Jinja2 macros for dynamic content generation

#### 2. **Comprehensive Print Format Generator** (`apps/erpnext_mz/erpnext_mz/setup/comprehensive_print_formats.py`)
- **14 Specialized Classes**: Each inheriting from `PrintFormatTemplate`
- **Document Coverage**:
  - **Sales**: `SalesInvoicePrintFormat`, `SalesOrderPrintFormat`, `DeliveryNotePrintFormat`, `QuotationPrintFormat`
  - **Purchase**: `PurchaseInvoicePrintFormat`, `PurchaseOrderPrintFormat`, `PurchaseReceiptPrintFormat`
  - **Inventory**: `StockEntryPrintFormat`, `MaterialRequestPrintFormat`
  - **Financial**: `PaymentEntryPrintFormat`, `JournalEntryPrintFormat`
  - **HR**: `PayslipPrintFormat`
  - **Master Data**: `CustomerPrintFormat`, `SupplierPrintFormat`
- **Template Generation**: Each class provides customized HTML templates with Mozambique-specific content

#### 3. **Print Format Management System** (`apps/erpnext_mz/erpnext_mz/setup/disable_existing_print_formats.py`)
- **Preparation**: Disables all existing print formats to prevent conflicts
- **Exclusive Enablement**: Ensures only Mozambique formats are enabled
- **Default Selection**: Mozambique formats become de facto defaults by being the only available option
- **Self-Maintenance**: Automatic enforcement of Mozambique-only policy

#### 4. **QR Code Integration System** (`apps/erpnext_mz/erpnext_mz/qr_code/`)
- **QR Code Generator** (`qr_generator.py`):
  - Automatic generation on document submission
  - HMAC-secured validation links
  - Base64-encoded PNG images for HTML embedding
- **Document Validation API** (`api.py`):
  - Public endpoint for QR code validation
  - Whitelisted methods for security
  - Tamper-proof hash verification
- **QR Code Storage** (`doctype/qr_code/`):
  - Persistent storage of generated QR codes
  - Validation data and metadata
  - Audit trail for compliance

#### 5. **Verification & Testing System** (`apps/erpnext_mz/erpnext_mz/verify_mozambique_setup.py`)
- **Comprehensive Checks**: Verifies all aspects of print format setup
- **Status Reporting**: Detailed feedback on system health
- **Production Readiness**: Ensures system meets all requirements

### Key Features

#### **Professional Design**
- **Clean Layout**: Minimalist design with clear visual hierarchy
- **Consistent Branding**: Company logo, colors, and styling
- **Bilingual Support**: Portuguese (MZ) and English labels
- **Print Optimization**: CSS optimized for both screen and print

#### **Mozambique Compliance**
- **NUIT Display**: Company tax ID prominently shown
- **Tax Breakdown**: Detailed tax information with rates
- **Local Formatting**: Mozambique-specific date and number formats
- **Regulatory Requirements**: Meets all local business document standards

#### **QR Code System**
- **Automatic Generation**: QR codes created on document submission
- **Document Validation**: Public API for verification
- **Security**: HMAC hashing prevents tampering
- **User Experience**: Easy validation via mobile device scanning

#### **Integration & Automation**
- **Company Setup Wizard**: All formats created automatically during onboarding
- **Self-Maintaining**: System automatically enforces Mozambique-only policy
- **Error Handling**: Comprehensive error handling and logging
- **Idempotent Operations**: Safe to run multiple times

### Data Flow
1. **Document Submission**: User submits document (e.g., Sales Invoice)
2. **QR Code Generation**: Hook function generates QR code with validation link
3. **Print Format Selection**: User selects print format (only Mozambique options available)
4. **Template Rendering**: Jinja2 template renders with dynamic content and QR code
5. **Document Output**: Professional PDF/print with Mozambique compliance and QR code
---

## Quick "who does what" cheat-sheet
**Do in the UI (🖱️):** VAT templates 16/5/0; Tax Categories; COA/IFRS; Naming Series; Custom Fields (NUIT, AT Cert Nº); fiscal Print Formats (with QR); Payroll components (INSS/IRPS); Leave policies; Workspaces.
**Write in code (🧩):** SAF-T XML + scheduler; AT API client + post-submit hooks; NUIT validator (client/server); signed audit logs; after\_migrate guard; provisioning scripts; Company Setup Wizard.