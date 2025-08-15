ERPNext Mozambique Compliance Roadmap (2025) — Checkable Checklist
> From zero to a fully built, tax‑compliant, multi‑tenant ERPNext SaaS for Mozambique.  

## Phase 1 — Planning & Infrastructure
- [X] Form the core team (Frappe/ERPNext devs, fiscal expert, AWS DevOps, support).
- [X] Define scope: Accounting, Sales, Inventory, Purchase, HR/Payroll, Projects, CRM.
- [X] Choose AWS architecture (EC2/ECS, RDS MariaDB, S3 files, CloudFront optional).
- [X] Define environments: **dev**, **staging**, **prod**.
- [X] Security baseline: HTTPS (ACM/Let’s Encrypt), WAF, IAM least privilege, VPC subnets.
- [X] Backups: S3 with cross‑region replication; daily + weekly retention plan.
- [X] Monitoring: CloudWatch metrics/alarms; ERPNext health endpoint; log retention.
- [X] DR plan: RTO/RPO targets, restore rehearsal scheduled quarterly.

## Phase 2 — Core ERPNext Installation
- [X] Provision Ubuntu LTS instance(s) for **dev/staging/prod**.
- [X] Install system deps (Python, Node.js, Yarn, Redis, wkhtmltopdf).
- [X] Install MariaDB and harden (bind‑address, strong root, utf8mb4).
- [X] Install Bench CLI and ERPNext apps.
- [X] Create first site and enable ERPNext
- [X] Production setup (Supervisor + Nginx).
- [X] Enable multi‑tenancy: create one site per tenant.
- [X] setup pt-MZ language pack.
- [X] Email setup (SMTP), timezone, currency (MZN), fiscal year.

## Phase 3 — Mozambique Localization (Accounting & Tax)
- [ ] Load Mozambique **Chart of Accounts** aligned to IFRS.
- [ ] VAT templates:
  - [ ] VAT 16% (standard).
  - [ ] VAT 5% (reduced: health/education).
  - [ ] VAT 0% (exports/exempt with legal note).
- [ ] Configure **Tax Categories** and link to Items/Customers as needed.
- [ ] Withholding/retentions (if applicable for your sector).
- [ ] Custom fields:
  - [ ] Customer/Supplier **NUIT** (validate length/format).
  - [ ] Invoice **Fiscal Series** and **Sequential Number**.
  - [ ] **AT Certification Number** (to print on invoices).
- [ ] Print Formats:
  - [ ] Add **QR Code** with key fiscal data.
  - [ ] Show sequence, series, certification text.
  - [ ] Multi‑language labels (PT primary).
- [ ] Multi‑currency rules (if needed).

## Phase 4 — HR & Payroll Compliance
- [ ] Salary components and structures:
  - [ ] **INSS**: Employer 4%, Employee 3%.
  - [ ] **IRPS** progressive: 10%, 15%, 20%, 25%, 32%.
- [ ] Benefits in kind:
  - [ ] Add fields for vehicle, housing, insurance, etc.
  - [ ] Ensure valuation in **MZN** and inclusion in **gross**.
- [ ] Leave policies per law:
  - [ ] Maternity 90 days (60 paid by INSS).
  - [ ] Paternity 7 days.
  - [ ] Annual leave (12 days 1º ano; 30 dias após 1 ano).
- [ ] Payroll calendar, journals, and posting rules verified.
- [ ] Payroll reports: monthly INSS & IRPS summaries validated.

## Phase 5 — Custom App: `erpnext_mz` (Compliance Logic)
- [ ] Create app skeleton and install on all sites:
  - [ ] `bench new-app erpnext_mz`
  - [ ] `bench --site <site> install-app erpnext_mz`
- [ ] **SAF‑T XML (Vendas & Folha)** generators:
  - [ ] Implement XML schemas + unit tests.
  - [ ] Export, validate, and archive monthly files.
- [ ] **Checksum/Hash** routines for invoices (anti‑tampering).
- [ ] **AT Integration** (when API available):
  - [ ] Server **hooks**: on submit Sales Invoice ⇒ transmit payload to AT.
  - [ ] Retry & error queue; status dashboard.
- [ ] **Validations**:
  - [ ] NUIT format client‑side check.
  - [ ] SAF‑T variance rule (Vendas vs Folha) **≤ 3%** — block if exceeded.
- [ ] **Print formats** packaged in app (QR, certification no., legal mentions).
- [ ] Settings doctype for AT endpoints/keys and toggles.

## Phase 6 — Data Integrity, Archiving & Backups
- [ ] Immutable numbering: lock posted invoices; cancellation via credit note only.
- [ ] Signed audit trail for critical DocTypes (Sales Invoice, Payroll Entry).
- [ ] Monthly SAF‑T/JSON snapshots shipped to S3 (WORM bucket/Glacier).
- [ ] Retention policy: 10 years for fiscal docs.
- [ ] Scheduled restore drills (semi‑annual).

## Phase 7 — Certification with AT
- [ ] Prepare dossier: architecture, security, data flows, sample invoices, SAF‑T files.
- [ ] Stand‑alone **staging** tenant for certification tests.
- [ ] Iterate per AT feedback until pass.
- [ ] Receive **AT Certification ID** and record it in system settings.
- [ ] Update invoice print format to display certification ID.

## Phase 8 — SaaS Readiness (Multi‑Tenant Ops)
- [ ] Automated site provisioning:
  - [ ] Script: `bench new-site` + install apps + seed defaults.
  - [ ] Domain mapping and SSL.
- [ ] Subscription & billing integration (Stripe/MPesa/Bank — as applicable).
- [ ] Tenant isolation checks (db/files separation, S3 prefixes).
- [ ] CI/CD (GitHub Actions/GitLab):
  - [ ] Lint + tests (unit + Cypress for UI if used).
  - [ ] Build artifacts and deploy with `bench migrate` per site.
  - [ ] Blue/green or canary strategy for app updates.
- [ ] Observability:
  - [ ] App metrics (requests, queue, workers), Celery/RQ health.
  - [ ] Error tracking (Sentry).
- [ ] Cost controls (rightsizing, auto‑scaling policies, storage lifecycle).

## Phase 9 — Go‑Live & Continuous Compliance
- [ ] Onboard first tenants; import opening balances and master data.
- [ ] User training (Accounting, Sales, HR/Payroll, Reporting).
- [ ] Monthly operations checklist:
  - [ ] Transmit invoices to AT / verify acknowledgements.
  - [ ] Close payroll; verify **≤ 3%** variance vs sales.
  - [ ] Generate and archive SAF‑T (Vendas & Folha); submit to portal if needed.
- [ ] Update rules when VAT/IRPS/INSS tables change.
- [ ] Quarterly review: restore test, security review, costs, and performance.