import frappe
from erpnext_mz.utils.account_utils import ensure_account


def _find_parent_account(company_name: str, root_type: str, candidates: list[str]) -> str | None:
	"""Find a sensible parent account by account_name among candidates. Falls back to the first
	group account under the given root_type if no candidate matches. Returns the account_name
	(not the full name with company abbreviation) suitable for ensure_account's parent_account argument.
	"""
	# Try explicit candidates by account_name
	for candidate in candidates:
		acc = frappe.db.exists("Account", {"company": company_name, "account_name": candidate})
		if acc:
			return candidate
	# Fallback: pick any top-level group for root_type
	rows = frappe.get_all(
		"Account",
		filters={"company": company_name, "root_type": root_type, "is_group": 1},
		fields=["account_name"],
		limit=1,
	)
	if rows:
		return rows[0].account_name
	return None


def ensure_payroll_chart_of_accounts(company_name: str) -> dict:
	"""Create Mozambican payroll accounts (idempotent). Returns mapping keys -> Account.name.

	Expense:
	- 53.01.01 - Salários e Ordenados
	- 53.01.02 - Contribuição INSS Empregador
	- 53.01.03 - Benefícios em Espécie

	Liability:
	- 23.01.01 - Salários a Pagar (Payable)
	- 23.01.02 - INSS a Pagar (Tax)
	- 23.01.03 - IRPS a Pagar (Tax)
	"""
	# Parent discovery
	expense_parent = _find_parent_account(
		company_name,
		"Expense",
		candidates=[
			"Expenses",
			"Despesas",
			"Operating Expenses",
			"Despesas Operacionais",
			"Indirect Expenses",
			"Gastos",
		],
	)
	liability_parent = _find_parent_account(
		company_name,
		"Liability",
		candidates=[
			"Current Liabilities",
			"Liabilities",
			"Passivo Corrente",
			"Passivo",
		],
	)

	result: dict[str, str] = {}

	# Expense accounts
	result["expense_salaries"] = ensure_account(
		company_name,
		"Salários e Ordenados",
		"Expense",
		None,
		expense_parent,
		"53.01.01",
	)
	result["expense_inss_employer"] = ensure_account(
		company_name,
		"Contribuição INSS Empregador",
		"Expense",
		None,
		expense_parent,
		"53.01.02",
	)
	result["expense_beneficios"] = ensure_account(
		company_name,
		"Benefícios em Espécie",
		"Expense",
		None,
		expense_parent,
		"53.01.03",
	)

	# Liability accounts
	result["liab_salarios_pagar"] = ensure_account(
		company_name,
		"Salários a Pagar",
		"Liability",
		"Payable",
		liability_parent,
		"23.01.01",
	)
	result["liab_inss_pagar"] = ensure_account(
		company_name,
		"INSS a Pagar",
		"Liability",
		"Tax",
		liability_parent,
		"23.01.02",
	)
	result["liab_irps_pagar"] = ensure_account(
		company_name,
		"IRPS a Pagar",
		"Liability",
		"Tax",
		liability_parent,
		"23.01.03",
	)

	return result


def _set_component_account(doc, company_name: str, default_account: str) -> None:
	"""Ensure Salary Component Account row for company points to default_account (Account.name)."""
	updated = False
	for row in getattr(doc, "accounts", []) or []:
		if row.company == company_name:
			if row.default_account != default_account:
				row.default_account = default_account
			updated = True
			break
	if not updated:
		doc.append("accounts", {"company": company_name, "default_account": default_account})


def upsert_salary_component(
	name: str,
	type_: str,
	company_name: str,
	default_account: str,
	*,
	abbr: str | None = None,
	formula: str | None = None,
	is_employer_contribution: int = 0,
	is_income_tax_component: int = 0,
	depends_on_payment_days: int = 1,
	statistical_component: int = 0,
	do_not_include_in_net_pay: int = 0,
) -> str:
	"""Create/update a Salary Component and bind company account. Returns component name."""
	comp_name = name
	comp_id = frappe.db.exists("Salary Component", comp_name)
	if comp_id:
		doc = frappe.get_doc("Salary Component", comp_id)
	else:
		doc = frappe.new_doc("Salary Component")
		doc.salary_component = comp_name

	# Core fields
	doc.type = type_
	if abbr and hasattr(doc, "abbr"):
		doc.abbr = abbr
	if hasattr(doc, "depends_on_payment_days"):
		doc.depends_on_payment_days = depends_on_payment_days
	if hasattr(doc, "is_income_tax_component"):
		doc.is_income_tax_component = is_income_tax_component
	if hasattr(doc, "statistical_component"):
		doc.statistical_component = statistical_component
	# Prefer native employer contribution flag if present
	if hasattr(doc, "is_employer_contribution"):
		doc.is_employer_contribution = is_employer_contribution
	else:
		# Fallback: try to avoid affecting net pay if intended
		if is_employer_contribution:
			if hasattr(doc, "do_not_include_in_net_pay"):
				doc.do_not_include_in_net_pay = 1
			if hasattr(doc, "statistical_component"):
				doc.statistical_component = 1

	# Formula settings
	if formula:
		if hasattr(doc, "amount_based_on_formula"):
			doc.amount_based_on_formula = 1
		if hasattr(doc, "formula"):
			doc.formula = formula

	# Ensure company account row
	_set_component_account(doc, company_name, default_account)

	if comp_id:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)

	return doc.name


def ensure_salary_components(company_name: str, accounts: dict) -> dict:
	"""Create earnings, deductions and employer contribution components. Returns mapping keys->names."""
	result: dict[str, str] = {}

	# Handle renames for legacy names to enforce uniform naming
	try:
		old = "Seguro/Outros (Benefício em Espécie)"
		new = "Seguro (Benefício em Espécie)"
		if frappe.db.exists("Salary Component", old) and not frappe.db.exists("Salary Component", new):
			frappe.rename_doc("Salary Component", old, new, force=True, ignore_permissions=True)
	except Exception:
		pass
	try:
		old = "IRPS (Progressivo)"
		new = "IRPS (progressivo)"
		if frappe.db.exists("Salary Component", old) and not frappe.db.exists("Salary Component", new):
			frappe.rename_doc("Salary Component", old, new, force=True, ignore_permissions=True)
	except Exception:
		pass

	# Earnings
	result["c_base"] = upsert_salary_component(
		"Salário Base",
		"Earning",
		company_name,
		accounts["expense_salaries"],
		abbr="SB",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_sub_transporte"] = upsert_salary_component(
		"Subsídio de Transporte",
		"Earning",
		company_name,
		accounts["expense_salaries"],
		abbr="SDT",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_sub_alimentacao"] = upsert_salary_component(
		"Subsídio de Alimentação",
		"Earning",
		company_name,
		accounts["expense_salaries"],
		abbr="SDA",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_ben_habitacao"] = upsert_salary_component(
		"Habitação (Benefício em Espécie)",
		"Earning",
		company_name,
		accounts["expense_beneficios"],
		abbr="HBE",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_ben_viatura"] = upsert_salary_component(
		"Viatura (Benefício em Espécie)",
		"Earning",
		company_name,
		accounts["expense_beneficios"],
		abbr="VBE",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_ben_seguro"] = upsert_salary_component(
		"Seguro (Benefício em Espécie)",
		"Earning",
		company_name,
		accounts["expense_beneficios"],
		abbr="SBE",
		formula=None,
		depends_on_payment_days=1,
	)

	# Deductions
	result["c_inss_3"] = upsert_salary_component(
		"INSS Trabalhador (3%)",
		"Deduction",
		company_name,
		accounts["liab_inss_pagar"],
		abbr="INSS-TRAB",
		formula="base * 0.03",
		depends_on_payment_days=1,
	)
	result["c_irps_prog"] = upsert_salary_component(
		"IRPS (progressivo)",
		"Deduction",
		company_name,
		accounts["liab_irps_pagar"],
		abbr="IRPS",
		formula=None,
		is_income_tax_component=1,
		depends_on_payment_days=1,
	)

	# Employer contribution (expense only, not in net pay)
	result["c_inss_empregador_4"] = upsert_salary_component(
		"INSS Empregador (4%)",
		"Earning",
		company_name,
		accounts["expense_inss_employer"],
		abbr="INSS-EMP",
		formula="base * 0.04",
		is_employer_contribution=1,
		depends_on_payment_days=1,
		statistical_component=0,
	)

	return result


def _append_structure_row(table: list, component_name: str, *, depends_on_payment_days: int | None = None, statistical_component: int | None = None) -> None:
	row = {"salary_component": component_name}
	if depends_on_payment_days is not None:
		row["depends_on_payment_days"] = depends_on_payment_days
	if statistical_component is not None:
		row["statistical_component"] = statistical_component
	table.append(row)


def ensure_salary_structure(company_name: str, component_map: dict, *, structure_name: str = "Folha Moçambique") -> str:
	"""Create/Update Salary Structure and attach all components."""
	ss_name = frappe.db.exists("Salary Structure", {"name": structure_name})
	if ss_name:
		ss = frappe.get_doc("Salary Structure", ss_name)
	else:
		ss = frappe.new_doc("Salary Structure")
		# Try naming it directly; if naming rules prevent it, ERPNext will assign a new name
		try:
			ss.name = structure_name
		except Exception:
			pass
		ss.company = company_name
		if hasattr(ss, "payroll_frequency"):
			ss.payroll_frequency = "Monthly"
		ss.is_active = 1

	# Reset details idempotently (keep doc but rebuild rows)
	ss.set("earnings", [])
	ss.set("deductions", [])

	# Earnings
	_append_structure_row(ss.earnings, component_map["c_base"], depends_on_payment_days=1)
	_append_structure_row(ss.earnings, component_map["c_sub_transporte"], depends_on_payment_days=1)
	_append_structure_row(ss.earnings, component_map["c_sub_alimentacao"], depends_on_payment_days=1)
	_append_structure_row(ss.earnings, component_map["c_ben_habitacao"], depends_on_payment_days=1)
	_append_structure_row(ss.earnings, component_map["c_ben_viatura"], depends_on_payment_days=1)
	_append_structure_row(ss.earnings, component_map["c_ben_seguro"], depends_on_payment_days=1)
	# Employer contribution as statistical earning to avoid net pay effect (engine may handle employer flag too)
	_append_structure_row(ss.earnings, component_map["c_inss_empregador_4"], statistical_component=1)

	# Deductions
	_append_structure_row(ss.deductions, component_map["c_inss_3"], depends_on_payment_days=1)
	_append_structure_row(ss.deductions, component_map["c_irps_prog"], depends_on_payment_days=1)

	# Link IRPS slab on structure if field exists
	if hasattr(ss, "income_tax_slab") and frappe.db.exists("Income Tax Slab", "IRPS Moçambique (2025)"):
		ss.income_tax_slab = "IRPS Moçambique (2025)"

	if ss_name:
		ss.save(ignore_permissions=True)
	else:
		ss.insert(ignore_permissions=True)
		# Ensure docname matches desired structure_name
		try:
			if ss.name != structure_name and not frappe.db.exists("Salary Structure", structure_name):
				frappe.rename_doc("Salary Structure", ss.name, structure_name, force=True, ignore_permissions=True)
				ss = frappe.get_doc("Salary Structure", structure_name)
		except Exception:
			pass

	# Ensure Company default payroll payable account
	try:
		company = frappe.get_doc("Company", company_name)
		acc = frappe.db.get_value(
			"Account",
			{"company": company_name, "account_name": "Salários a Pagar"},
			"name",
		)
		if hasattr(company, "default_payroll_payable_account") and acc and company.default_payroll_payable_account != acc:
			company.db_set("default_payroll_payable_account", acc, commit=True)
	except Exception:
		pass

	return ss.name


def link_irps_slab_to_component(company_name: str, irps_component_name: str) -> None:
	"""Ensure default Income Tax Slab is set and IRPS component is flagged properly."""
	# Ensure slab exists
	if not frappe.db.exists("Income Tax Slab", "IRPS Moçambique (2025)"):
		from erpnext_mz.setup.onboarding import _ensure_income_tax_slab
		_ensure_income_tax_slab(company_name)

	# Set Payroll Settings default slab if field exists
	try:
		if frappe.get_meta("Payroll Settings").has_field("default_income_tax_slab"):
			frappe.db.set_single_value("Payroll Settings", "default_income_tax_slab", "IRPS Moçambique (2025)")
	except Exception:
		pass

	# Ensure component has the flag
	try:
		comp_id = frappe.db.exists("Salary Component", irps_component_name)
		if comp_id:
			comp = frappe.get_doc("Salary Component", comp_id)
			if hasattr(comp, "is_income_tax_component") and not comp.is_income_tax_component:
				comp.is_income_tax_component = 1
				comp.save(ignore_permissions=True)
	except Exception:
		pass


def validate_salary_setup(company_name: str, structure_name: str) -> dict:
	"""Return a brief validation report for accounts, components, and structure composition."""
	report = {"accounts": {}, "components": {}, "structure": {}}

	# Accounts
	needed_accounts = [
		("Salários e Ordenados", "Expense"),
		("Contribuição INSS Empregador", "Expense"),
		("Benefícios em Espécie", "Expense"),
		("Salários a Pagar", "Liability"),
		("INSS a Pagar", "Liability"),
		("IRPS a Pagar", "Liability"),
	]
	for acc_name, _rt in needed_accounts:
		acc = frappe.db.exists("Account", {"company": company_name, "account_name": acc_name})
		report["accounts"][acc_name] = True if acc else False

	# Components
	component_names = [
		"Salário Base",
		"Subsídio de Transporte",
		"Subsídio de Alimentação",
		"Habitação (Benefício em Espécie)",
		"Viatura (Benefício em Espécie)",
		"Seguro (Benefício em Espécie)",
		"INSS Trabalhador (3%)",
		"IRPS (progressivo)",
		"INSS Empregador (4%)",
	]
	for c in component_names:
		cid = frappe.db.exists("Salary Component", c)
		report["components"][c] = True if cid else False

	# Structure
	ss_id = frappe.db.exists("Salary Structure", {"name": structure_name})
	if not ss_id:
		report["structure"]["exists"] = False
		return report
	ss = frappe.get_doc("Salary Structure", ss_id)
	report["structure"]["exists"] = True
	# Check presence of components in rows
	def _names(rows):
		return {row.salary_component for row in rows}
	all_earnings = _names(ss.earnings or [])
	all_deductions = _names(ss.deductions or [])
	must_earnings = {
		"Salário Base",
		"Subsídio de Transporte",
		"Subsídio de Alimentação",
		"Habitação (Benefício em Espécie)",
		"Viatura (Benefício em Espécie)",
		"Seguro/Outros (Benefício em Espécie)",
		"INSS Empregador (4%)",
	}
	must_deductions = {"INSS Trabalhador (3%)", "IRPS (Progressivo)"}
	report["structure"]["earnings_ok"] = must_earnings.issubset(all_earnings)
	report["structure"]["deductions_ok"] = must_deductions.issubset(all_deductions)

	return report


