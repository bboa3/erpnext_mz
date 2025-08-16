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
* [ ] **IFRS Chart of Accounts** (🖱️ UI or import template).
  **Acceptance:** COA ready; GL/BS/P\&L run clean.
* [ ] **VAT setup** (🖱️ UI)
  * Templates: **IVA 16%**, **IVA 5%** (setores reduzidos), **IVA 0%** (export/isentos + menção legal).
  * **Tax Categories** and per-item/per-customer mappings where needed.
    **Acceptance:** Tax applied correctly on SO/SI/PI; reports reconcile.
* [ ] **Custom Fields** (🖱️ UI then export fixtures 🧩 CODE)
  * Customer/Supplier **NUIT**; Company **AT Certification Nº**; SI fields for hash/QR as needed.
    **Acceptance:** Fields visible and required where specified.
* [ ] **Sequential numbering** (Naming Series) (🖱️ UI).
  **Acceptance:** “FT-YYYY-####” issues sequentially; no duplicates.
* [ ] **Print Formats (fiscal)** (🖱️ UI)
  * Show NUIT (empresa/cliente), série+nº, **Nº**, **QR** payload.
    **Acceptance:** Printed PDF shows all fiscal elements.
* [ ] **Withholdings/retentions** if applicable (🖱️ UI).
  **Acceptance:** Correct net values and reports.

## Phase 4 — HR & Payroll Compliance
* [ ] **INSS**: Empregador 4%, Empregado 3% (🖱️ UI components/structures).
  **Acceptance:** Payslips compute correct INSS.
* [ ] **IRPS progressive** 10/15/20/25/32% (🖱️ UI tables; verify latest tables with contabilista)
  **Acceptance:** Payslips compute correct IRPS.
* [ ] **Benefits in kind** (vehicle, housing, insurance…) (🖱️ UI fields;)
  **Acceptance:** Valuation in **MZN**; included in gross and SAF-T mapping.
* [ ] **Leave policies** (maternity/paternity/annual) (🖱️ UI)
  **Acceptance:** Policies match law; balances accrue correctly.

## Phase 5 — Custom App: `erpnext_mz` (Compliance Logic)
* [ ] App skeleton installed on all sites; fixtures enabled (🧩 CODE).
  **Acceptance:** `bench --site <site> list-apps` shows `erpnext_mz`.
* [ ] **Integrity / Checksums (anti-tamper)** (🧩 CODE hook or Server Script)
  * `Sales Invoice.on_submit` → compute **SHA-256** over key fields + **chain to previous**.
    **Acceptance:** `mz_hash` and `mz_prev_hash` filled; chain consistent across invoices.
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
* [ ] **Workspace (single branded home)** “Mozambique ERP” (🖱️ UI then fixtures 🧩 CODE)
  **Acceptance:** Users land on your curated workspace; ERPNext defaults hidden.

## Phase 6 — Data Integrity, Archiving & Backups
* [ ] **Immutable numbering & cancel policy** (🖱️ UI + 🧩 CODE guard)
  **Acceptance:** Posted invoices cannot be edited; only credit notes reverse.
* [ ] **Signed audit trail** for critical DocTypes (🧩 CODE: logging hash + metadata)
  **Acceptance:** Tamper-evident logs exist for SI/Payroll Entry.
* [ ] **Monthly archives to S3** (SAF-T, hash chain, audit logs) with **10-year retention** (ops).
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

## Quick “who does what” cheat-sheet
**Do in the UI (🖱️):** VAT templates 16/5/0; Tax Categories; COA/IFRS; Naming Series; Custom Fields (NUIT, AT Cert Nº); fiscal Print Formats (with QR); Payroll components (INSS/IRPS); Leave policies; Workspaces.
**Write in code (🧩):** Hash chain on SI; SAF-T XML + scheduler; AT API client + post-submit hooks; NUIT validator (client/server); signed audit logs; fixtures (to persist UI work); after\_migrate guard; provisioning scripts.