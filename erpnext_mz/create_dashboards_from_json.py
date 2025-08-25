#!/usr/bin/env python3
"""
Create/Update Dashboards from mozambique_dashboad.json

Usage examples:
- bench --site erp.local execute erpnext_mz.create_dashboards_from_json.create_all
- bench --site erp.local execute erpnext_mz.create_dashboards_from_json.create_one --kwargs '{"dashboard_name": "Accounting & Taxes Dashboard"}'
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import frappe


def _config_path() -> str:
    return os.path.join(frappe.get_app_path("erpnext_mz"), "mozambique_dashboad.json")


def _load_config() -> Dict[str, Any]:
    with open(_config_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_dashboard(dash_conf: Dict[str, Any]):
    name = dash_conf.get("dashboard_name")
    if not name:
        return

    # Create or load dashboard
    if frappe.db.exists("Dashboard", name):
        dashboard = frappe.get_doc("Dashboard", name)
        dashboard.cards = []
        dashboard.charts = []
    else:
        dashboard = frappe.new_doc("Dashboard")
        dashboard.dashboard_name = name
        dashboard.module = dash_conf.get("module") or "Accounts"

    # Add cards
    for card in dash_conf.get("cards", []):
        card_name = card.get("card")
        if not card_name:
            continue
        # Number Cards are stored as "Number Card" DocType
        if not frappe.db.exists("Number Card", card_name):
            frappe.logger().info(f"Skipping missing Number Card: {card_name}")
            continue
        row = dashboard.append("cards", {})
        row.card = card_name

    # Add charts
    for ch in dash_conf.get("charts", []):
        chart_name = ch.get("chart")
        if not chart_name:
            continue
        if not frappe.db.exists("Dashboard Chart", chart_name):
            frappe.logger().info(f"Skipping missing Dashboard Chart: {chart_name}")
            continue
        row = dashboard.append("charts", {})
        row.chart = chart_name
        if ch.get("width") in ("Half", "Full"):
            row.width = ch.get("width")

    # Save
    dashboard.is_default = 0
    dashboard.is_standard = 0
    dashboard.save(ignore_permissions=True)
    frappe.clear_cache()
    print(f"✅ Dashboard ensured: {name}")


def create_one(dashboard_name: str):
    config = _load_config()
    for dash in config.get("dashboards", []):
        if dash.get("dashboard_name") == dashboard_name:
            _ensure_dashboard(dash)
            return
    print(f"❌ Dashboard not found in config: {dashboard_name}")


def create_all():
    config = _load_config()
    for dash in config.get("dashboards", []):
        _ensure_dashboard(dash)
    print("✅ All dashboards processed")


if __name__ == "__main__":
    create_all()


