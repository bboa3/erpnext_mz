import frappe
from erpnext_mz.utils.account_utils import get_account_by_number, require_account_by_number


def ensure_payroll_chart_of_accounts(company_name: str) -> dict:
	"""Locate Mozambican payroll accounts from IFRS MZ CoA. Returns mapping keys -> Account.name.

	Expense (Gastos > Despesas com Pessoal 50.02):
	- 50.02.01 - Salários e Ordenados
	- 50.02.02 - INSS - Empregador
	- 50.02.04 - Benefícios em Espécie - Habitação
	- 50.02.05 - Benefícios em Espécie - Veículo
	- 50.02.06 - Benefícios em Espécie - Seguro Saúde

	Liability (Passivos Correntes):
	- 21.02.05 - INSS a Pagar
	- 21.02.05 - INSS a Pagar
	- 21.02.04 - IRPS Retido na Fonte
	- 21.05.01 - Salários a Pagar
	- 21.05.02 - Férias e Subsídios a Pagar
	"""
	result: dict[str, str] = {}

	# Expense accounts by number
	result["expense_salaries"] = require_account_by_number(company_name, "50.02.01", "Salários e Ordenados")
	result["expense_inss_employer"] = require_account_by_number(company_name, "50.02.02", "INSS - Empregador")
	result["expense_habitacao"] = require_account_by_number(company_name, "50.02.04", "Benefícios em Espécie - Habitação")
	result["expense_viatura"] = require_account_by_number(company_name, "50.02.05", "Benefícios em Espécie - Veículo")
	result["expense_seguro_saude"] = require_account_by_number(company_name, "50.02.06", "Benefícios em Espécie - Seguro Saúde")

	# Liability accounts by number
	result["liab_salarios_pagar"] = require_account_by_number(company_name, "21.05.01", "Salários a Pagar")
	result["liab_ferias_pagar"] = require_account_by_number(company_name, "21.05.02", "Férias e Subsídios a Pagar")
	result["liab_inss_pagar"] = require_account_by_number(company_name, "21.02.05", "INSS a Pagar")
	result["liab_irps_pagar"] = require_account_by_number(company_name, "21.02.04", "IRPS Retido na Fonte")

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
		accounts["expense_habitacao"],
		abbr="HBE",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_ben_viatura"] = upsert_salary_component(
		"Viatura (Benefício em Espécie)",
		"Earning",
		company_name,
		accounts["expense_viatura"],
		abbr="VBE",
		formula=None,
		depends_on_payment_days=1,
	)
	result["c_ben_seguro"] = upsert_salary_component(
		"Seguro (Benefício em Espécie)",
		"Earning",
		company_name,
		accounts["expense_seguro_saude"],
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
		acc = get_account_by_number(company_name, "21.05.01")
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

