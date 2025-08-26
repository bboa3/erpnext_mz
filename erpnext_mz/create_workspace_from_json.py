#!/usr/bin/env python3
"""
Create workspaces from mozambique_workspaces.json
Usage examples:
- bench --site erp.local execute erpnext_mz.create_workspace_from_json.create_relatorios_declaracoes
- bench --site erp.local execute erpnext_mz.create_workspace_from_json.create_workspace_by_title --kwargs '{"title": "Stock"}'
- bench --site erp.local execute erpnext_mz.create_workspace_from_json.verify_workspace --kwargs '{"title": "Relatórios & Declarações"}'
- bench --site erp.local execute erpnext_mz.create_workspace_from_json.recreate_all
"""

import json
import os
from typing import Any, Dict, List

import frappe

try:
	from erpnext_mz.workspace_utils import generate_workspace_content, get_next_sequence_id
except Exception:
	# Fallbacks if utils are not available
	def get_next_sequence_id() -> int:
		existing = frappe.get_all(
			"Workspace",
			filters={"public": 1},
			fields=["sequence_id"],
			order_by="sequence_id desc",
			limit=1,
		)
		return (existing[0].sequence_id + 1) if existing else 1

	def generate_workspace_content(workspace):
		content: List[Dict[str, Any]] = []
		# number cards
		for i, card in enumerate(workspace.number_cards):
			# default to 4 columns when not set
			col_value = getattr(card, "col", None) or 4
			content.append({
				"id": f"number_card_{i}",
				"type": "number_card",
				"data": {"number_card_name": getattr(card, "number_card_name", getattr(card, "label", "")), "col": col_value},
			})
		# charts
		for i, chart in enumerate(workspace.charts):
			col = 6 if getattr(chart, "width", "") == "Half" else 12
			content.append({
				"id": f"chart_{i}",
				"type": "chart",
				"data": {"chart_name": chart.chart_name, "col": col},
			})
		# shortcuts header
		if workspace.shortcuts:
			content.append({"id": "shortcuts_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Quick Access</b></span>", "col": 12}})
			for i, shortcut in enumerate(workspace.shortcuts):
				content.append({"id": f"shortcut_{i}", "type": "shortcut", "data": {"shortcut_name": shortcut.label, "col": 3}})
		# links groups as cards
		if workspace.links:
			content.append({"id": "spacer_before_links", "type": "spacer", "data": {"col": 12}})
			content.append({"id": "links_header", "type": "header", "data": {"text": "<span class=\"h4\"><b>Masters & Reports</b></span>", "col": 12}})
			for link in workspace.links:
				if link.type == "Card Break":
					content.append({"id": f"card_{link.label}", "type": "card", "data": {"card_name": link.label, "col": 4}})
		return content


def _config_path() -> str:
	# Point to apps/erpnext_mz/mozambique_workspaces.json
	return os.path.join(frappe.get_app_path("erpnext_mz"), "mozambique_workspaces.json")


def _load_config() -> Dict[str, Any]:
	with open(_config_path(), "r", encoding="utf-8") as f:
		return json.load(f)


def _find_workspace_config(config: Dict[str, Any], title: str) -> Dict[str, Any] | None:
	for ws in config.get("workspaces", []):
		if ws.get("title") == title:
			return ws
	return None

# Fallback names for known report naming differences across versions
_REPORT_FALLBACKS = {
	"Profit and Loss": ["Profit and Loss Statement", "Income Statement"],
}


def _resolve_report_name(name: str) -> str | None:
	"""Return a valid report name if exists, trying fallbacks if needed."""
	if frappe.db.exists("Report", name):
		return name
	for alt in _REPORT_FALLBACKS.get(name, []):
		if frappe.db.exists("Report", alt):
			return alt
	return None


def _append_shortcuts(workspace, shortcuts: List[Dict[str, Any]]) -> None:
	allowed = {"label", "type", "link_to", "color", "format", "stats_filter", "doc_view", "url", "report_ref_doctype"}
	for sc in shortcuts:
		ltype = sc.get("type")
		lto = sc.get("link_to")
		# validate
		if ltype == "DocType":
			try:
				frappe.get_meta(lto, cached=True)
			except Exception:
				# try alias resolution
				alias = _resolve_doctype_alias(lto)
				if alias:
					sc["link_to"] = alias
				else:
					frappe.logger().info(f"Skipping missing DocType shortcut: {lto}")
					continue
		elif ltype == "Report":
			resolved = _resolve_report_name(lto)
			if not resolved:
				frappe.logger().info(f"Skipping missing Report shortcut: {lto}")
				continue
			else:
				sc["link_to"] = resolved
		elif ltype == "Page" and not frappe.db.exists("Page", lto):
			frappe.logger().info(f"Skipping missing Page shortcut: {lto}")
			continue
		elif ltype == "Dashboard" and not frappe.db.exists("Dashboard", lto):
			# dashboards optional; keep or skip
			continue
		row = workspace.append("shortcuts", {})
		for key, value in sc.items():
			if key in allowed:
				setattr(row, key, value)


def _append_links(workspace, links: List[Dict[str, Any]]) -> None:
	allowed = {"type", "label", "link_type", "link_to", "onboard", "is_query_report", "report_ref_doctype", "icon", "dependencies", "hidden"}
	for lk in links:
		row = workspace.append("links", {})
		for key, value in lk.items():
			if key in allowed:
				setattr(row, key, value)


def _append_charts(workspace, charts: List[Dict[str, Any]]) -> None:
	for ch in charts:
		name = ch.get("chart_name")
		if not name:
			continue
		# ensure chart exists
		if not frappe.db.exists("Dashboard Chart", name):
			frappe.logger().info(f"Skipping missing Dashboard Chart: {name}")
			continue
		row = workspace.append("charts", {})
		row.chart_name = name
		if ch.get("width") in ("Half", "Full"):
			row.width = ch.get("width")


def _append_number_cards(workspace, cards: List[Dict[str, Any]]) -> None:
	for card in cards:
		name = card.get("number_card_name") or card.get("label")
		if not name:
			continue
		if not frappe.db.exists("Number Card", name):
			frappe.logger().info(f"Skipping missing Number Card: {name}")
			continue
		row = workspace.append("number_cards", {})
		row.number_card_name = name
		if card.get("col"):
			row.col = card.get("col")


def _validate_links_exist(links: List[Dict[str, Any]]) -> List[str]:
	missing: List[str] = []
	for lk in links:
		if lk.get("type") == "Card Break":
			continue
		ltype = lk.get("link_type")
		lto = lk.get("link_to")
		if not ltype or not lto:
			continue
		if ltype == "DocType":
			try:
				frappe.get_meta(lto, cached=True)
			except Exception:
				alias = _resolve_doctype_alias(lto)
				if alias:
					lk["link_to"] = alias
				else:
					missing.append(f"DocType: {lto}")
		elif ltype == "Report":
			resolved = _resolve_report_name(lto)
			if not resolved:
				missing.append(f"Report: {lto}")
			else:
				lk["link_to"] = resolved
		elif ltype == "Page" and not frappe.db.exists("Page", lto):
			missing.append(f"Page: {lto}")
		elif ltype == "Dashboard" and not frappe.db.exists("Dashboard", lto):
			# Not critical; dashboards are optional
			pass
	return missing


# Aliases/fallbacks for DocType names which vary across versions/modules
_DOCTYPE_ALIAS_CANDIDATES: Dict[str, List[str]] = {
	"Job Position": ["Designation", "Job Opening"],
	"Time Tracking": ["Timesheet"],
	"Work Schedule": ["Shift Type", "Shift Assignment"],
}


def _resolve_doctype_alias(name: str) -> str | None:
	"""Try to resolve a DocType name to an existing alternative using aliases."""
	for candidate in _DOCTYPE_ALIAS_CANDIDATES.get(name, []):
		try:
			frappe.get_meta(candidate, cached=True)
			return candidate
		except Exception:
			continue
	return None


def create_workspace_by_title(title: str):
	"""Create a workspace defined in mozambique_workspaces.json by title."""
	config = _load_config()
	ws_conf = _find_workspace_config(config, title)
	if not ws_conf:
		print(f"❌ Workspace '{title}' not found in mozambique_workspaces.json")
		return None

	if frappe.db.exists("Workspace", title):
		print(f"⏭️  Workspace '{title}' already exists, skipping.")
		return frappe.get_doc("Workspace", title)

	workspace = frappe.new_doc("Workspace")
	workspace.title = ws_conf.get("title")
	workspace.label = ws_conf.get("label") or ws_conf.get("title")
	workspace.icon = ws_conf.get("icon") or "star"
	workspace.indicator_color = ws_conf.get("indicator_color") or "blue"
	workspace.public = 1
	workspace.hide_custom = 0
	workspace.is_hidden = 0
	workspace.sequence_id = get_next_sequence_id()

	# append children
	_append_shortcuts(workspace, ws_conf.get("shortcuts", []))
	missing_links = _validate_links_exist(ws_conf.get("links", []))
	if missing_links:
		print(f"⚠️  Skipping {len(missing_links)} missing links: {missing_links}")
		filtered_links = [lk for lk in ws_conf.get("links", []) if not (
			(lk.get("link_type") == "DocType" and f"DocType: {lk.get('link_to')}" in missing_links) or
			(lk.get("link_type") == "Report" and f"Report: {lk.get('link_to')}" in missing_links) or
			(lk.get("link_type") == "Page" and f"Page: {lk.get('link_to')}" in missing_links)
		)]
		_append_links(workspace, filtered_links)
	else:
		_append_links(workspace, ws_conf.get("links", []))

	_append_charts(workspace, ws_conf.get("charts", []))
	_append_number_cards(workspace, ws_conf.get("number_cards", []))

	# content json
	workspace.content = json.dumps(generate_workspace_content(workspace))

	workspace.insert(ignore_permissions=True)
	frappe.clear_cache()
	print(f"✅ Created workspace: {title}")
	return workspace


def create_inicio():
	return create_workspace_by_title("Início")

def create_clientes_crm():
	return create_workspace_by_title("Clientes & CRM")

def create_stock():
	return create_workspace_by_title("Stock")

def create_vendas_faturacao():
	return create_workspace_by_title("Vendas & Faturação")

def create_compras_fornecedores():
	return create_workspace_by_title("Compras & Fornecedores")

def create_tesouraria_bancos():
	return create_workspace_by_title("Tesouraria & Bancos")

def create_contabilidade_impostos():
	return create_workspace_by_title("Contabilidade & Impostos")

def create_rh_folha():
	return create_workspace_by_title("RH & Folha")

def create_relatorios_declaracoes():
	"""Create the 'Relatórios & Declarações' workspace from mozambique_workspaces.json."""
	return create_workspace_by_title("Relatórios & Declarações")

def create_configuracoes():
	return create_workspace_by_title("Configurações")


def verify_workspace(title: str):
	"""Print a summary of a workspace if it exists."""
	if not frappe.db.exists("Workspace", title):
		print(f"❌ Workspace '{title}' not found")
		return None
	ws = frappe.get_doc("Workspace", title)
	print(f"✅ Workspace '{ws.title}' exists | Shortcuts: {len(ws.shortcuts or [])} | Links: {len(ws.links or [])} | Charts: {len(ws.charts or [])} | Number Cards: {len(ws.number_cards or [])}")
	return {
		"title": ws.title,
		"shortcuts": len(ws.shortcuts or []),
		"links": len(ws.links or []),
		"charts": len(ws.charts or []),
		"number_cards": len(ws.number_cards or []),
	}


def recreate_all():
	"""Delete and recreate all Mozambique workspaces as per JSON."""
	titles = [
		"Início", "Clientes & CRM", "Stock", "Vendas & Faturação",
		"Compras & Fornecedores", "Tesouraria & Bancos", "Contabilidade & Impostos",
		"RH & Folha", "Relatórios & Declarações", "Configurações",
	]
	for t in titles:
		if frappe.db.exists("Workspace", t):
			frappe.delete_doc("Workspace", t, ignore_permissions=True)
			print(f"🗑️  Deleted: {t}")
	for t in titles:
		create_workspace_by_title(t)
	print("✅ Recreated all Mozambique workspaces")


def sync_workspace_by_title(title: str):
	"""Update an existing workspace to match mozambique_workspaces.json; create if missing."""
	config = _load_config()
	ws_conf = _find_workspace_config(config, title)
	if not ws_conf:
		print(f"❌ Workspace '{title}' not found in mozambique_workspaces.json")
		return None

	if not frappe.db.exists("Workspace", title):
		print(f"➕ Workspace '{title}' not found. Creating new...")
		return create_workspace_by_title(title)

	workspace = frappe.get_doc("Workspace", title)
	print(f"🔄 Syncing workspace: {title}")

	# Preserve ordering/visibility but update metadata
	workspace.label = ws_conf.get("label") or ws_conf.get("title") or workspace.label
	workspace.icon = ws_conf.get("icon") or workspace.icon
	workspace.indicator_color = ws_conf.get("indicator_color") or workspace.indicator_color
	workspace.public = 1
	workspace.hide_custom = 0
	workspace.is_hidden = 0

	# Replace child tables with config-driven content
	workspace.set("shortcuts", [])
	workspace.set("links", [])
	workspace.set("charts", [])
	workspace.set("number_cards", [])

	_append_shortcuts(workspace, ws_conf.get("shortcuts", []))
	missing_links = _validate_links_exist(ws_conf.get("links", []))
	if missing_links:
		print(f"⚠️  Skipping {len(missing_links)} missing links: {missing_links}")
		filtered_links = [lk for lk in ws_conf.get("links", []) if not (
			(lk.get("link_type") == "DocType" and f"DocType: {lk.get('link_to')}" in missing_links) or
			(lk.get("link_type") == "Report" and f"Report: {lk.get('link_to')}" in missing_links) or
			(lk.get("link_type") == "Page" and f"Page: {lk.get('link_to')}" in missing_links)
		)]
		_append_links(workspace, filtered_links)
	else:
		_append_links(workspace, ws_conf.get("links", []))

	_append_charts(workspace, ws_conf.get("charts", []))
	_append_number_cards(workspace, ws_conf.get("number_cards", []))

	# Regenerate content json
	workspace.content = json.dumps(generate_workspace_content(workspace))
	workspace.save(ignore_permissions=True)
	frappe.clear_cache()
	print(f"✅ Synced workspace: {title}")
	return workspace


def dump_workspace(title: str):
	"""Dump a workspace's structure as JSON (shortcuts, links, charts, number cards)."""
	if not frappe.db.exists("Workspace", title):
		print(f"❌ Workspace '{title}' not found")
		return None
	ws = frappe.get_doc("Workspace", title)
	data: Dict[str, Any] = {
		"title": ws.title,
		"icon": getattr(ws, "icon", None),
		"indicator_color": getattr(ws, "indicator_color", None),
		"shortcuts": [],
		"links": [],
		"charts": [],
		"number_cards": [],
	}
	for s in (ws.shortcuts or []):
		data["shortcuts"].append({
			"label": getattr(s, "label", None),
			"type": getattr(s, "type", None),
			"link_to": getattr(s, "link_to", None),
			"doc_view": getattr(s, "doc_view", None),
			"report_ref_doctype": getattr(s, "report_ref_doctype", None),
			"url": getattr(s, "url", None),
			"color": getattr(s, "color", None),
			"stats_filter": getattr(s, "stats_filter", None),
			"format": getattr(s, "format", None),
		})
	for l in (ws.links or []):
		data["links"].append({
			"type": getattr(l, "type", None),
			"label": getattr(l, "label", None),
			"link_type": getattr(l, "link_type", None),
			"link_to": getattr(l, "link_to", None),
			"is_query_report": getattr(l, "is_query_report", None),
			"report_ref_doctype": getattr(l, "report_ref_doctype", None),
			"icon": getattr(l, "icon", None),
			"dependencies": getattr(l, "dependencies", None),
			"hidden": getattr(l, "hidden", None),
		})
	for c in (ws.charts or []):
		data["charts"].append({
			"chart_name": getattr(c, "chart_name", None),
			"width": getattr(c, "width", None),
		})
	for n in (ws.number_cards or []):
		data["number_cards"].append({
			"number_card_name": getattr(n, "number_card_name", None),
			"col": getattr(n, "col", None),
		})
	print(json.dumps(data, indent=2, ensure_ascii=False))
	return data


def dump_accounting():
	"""Dump the default Accounting workspace (tries 'Accounting' then 'Accounts')."""
	for t in ("Accounting", "Accounts"):
		if frappe.db.exists("Workspace", t):
			return dump_workspace(t)
	print("❌ Could not find a workspace titled 'Accounting' or 'Accounts'")
	return None


def _copy_links(src_ws, dst_ws) -> None:
	"""Replace dst_ws.links with a copy of src_ws.links (allowed fields only)."""
	allowed = {
		"type",
		"label",
		"link_type",
		"link_to",
		"onboard",
		"is_query_report",
		"report_ref_doctype",
		"icon",
		"dependencies",
		"hidden",
	}
	dst_ws.set("links", [])
	for lk in (src_ws.links or []):
		row = dst_ws.append("links", {})
		for key in allowed:
			if hasattr(lk, key):
				setattr(row, key, getattr(lk, key))


def restore_stock_links_from_default():
	"""
	Restore the 'Stock' workspace link cards from a default-like source.
	Prefers an existing workspace named 'Stockstock' (if present).
	Regenerates content to show the link cards.
	"""
	source_candidates = ["Stockstock"]
	source_title = None
	for cand in source_candidates:
		if frappe.db.exists("Workspace", cand):
			source_title = cand
			break

	if not source_title:
		print("❌ No default Stock source workspace found (expected 'Stockstock').")
		return None

	dest_title = "Stock"
	if not frappe.db.exists("Workspace", dest_title):
		print("➕ Destination 'Stock' not found. Creating from JSON definition...")
		create_stock()

	src = frappe.get_doc("Workspace", source_title)
	dst = frappe.get_doc("Workspace", dest_title)

	print(f"🔄 Restoring links on '{dest_title}' from '{source_title}' ...")
	_copy_links(src, dst)

	# Regenerate minimal content so link cards appear
	dst.content = json.dumps(generate_workspace_content(dst))
	dst.save(ignore_permissions=True)
	frappe.clear_cache()
	print(f"✅ Restored link cards on '{dest_title}' from '{source_title}'")
	return dump_workspace(dest_title)


def enrich_stockstock_links_from_json():
	"""
	Enrich the 'Stockstock' workspace with the Stock links defined in mozambique_workspaces.json.
	- Reads the 'Stock' workspace links from JSON
	- Applies them to 'Stockstock' (creating it if missing)
	- Regenerates content so the link cards appear
	"""
	config = _load_config()
	ws_conf = _find_workspace_config(config, "Stock")
	if not ws_conf:
		print("❌ Could not find 'Stock' config in mozambique_workspaces.json")
		return None

	links = ws_conf.get("links", [])
	# Ensure destination exists
	dest_title = "Stockstock"
	if not frappe.db.exists("Workspace", dest_title):
		ws = frappe.new_doc("Workspace")
		ws.title = dest_title
		ws.label = dest_title
		ws.icon = ws_conf.get("icon") or "stock"
		ws.indicator_color = ws_conf.get("indicator_color") or "blue"
		ws.public = 1
		ws.hide_custom = 0
		ws.is_hidden = 0
		ws.sequence_id = get_next_sequence_id()
		ws.insert(ignore_permissions=True)

	ws = frappe.get_doc("Workspace", dest_title)
	print(f"🔧 Enriching links on '{dest_title}' from JSON definition of 'Stock' ...")

	# Replace links with validated/filtered ones
	ws.set("links", [])
	missing_links = _validate_links_exist(links)
	if missing_links:
		print(f"⚠️  Skipping {len(missing_links)} missing links: {missing_links}")
		filtered_links = [lk for lk in links if not (
			(lk.get("link_type") == "DocType" and f"DocType: {lk.get('link_to')}" in missing_links) or
			(lk.get("link_type") == "Report" and f"Report: {lk.get('link_to')}" in missing_links) or
			(lk.get("link_type") == "Page" and f"Page: {lk.get('link_to')}" in missing_links)
		)]
		_append_links(ws, filtered_links)
	else:
		_append_links(ws, links)

	# Regenerate minimal content to show link cards
	ws.content = json.dumps(generate_workspace_content(ws))
	ws.save(ignore_permissions=True)
	frappe.clear_cache()
	print(f"✅ Enriched link cards on '{dest_title}' from JSON")
	return dump_workspace(dest_title)
