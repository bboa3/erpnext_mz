#!/usr/bin/env python3
import argparse
import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List


CLIENTS_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "clients.csv"))
OUTPUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "leads_import.json"))


def normalize_country(country_value: str) -> str:
    if not country_value:
        return ""
    value = country_value.strip()
    replacements = {
        "Republic of Mozambique": "Mozambique",
        "República de Moçambique": "Mozambique",
        "Mocambique": "Mozambique",
        "Moçambique": "Mozambique",
    }
    return replacements.get(value, value)


def sanitize_website(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    for prefix in ("https://", "http://"):
        if url.lower().startswith(prefix):
            return url[len(prefix):]
    return url


def looks_like_url(text: str) -> bool:
    t = (text or "").strip().lower()
    return t.startswith("http://") or t.startswith("https://") or t.startswith("www.") or "." in t


def looks_like_email(text: str) -> bool:
    return "@" in (text or "")


def sanitize_phone(raw: str) -> str:
    if not raw:
        return ""
    # Keep digits and at most one leading plus
    raw = raw.strip()
    # Skip if value is actually a url/email
    if looks_like_url(raw) or looks_like_email(raw):
        return ""
    digits = []
    for ch in raw:
        if ch.isdigit():
            digits.append(ch)
    # Detect leading plus anywhere in string
    has_plus = raw.strip().startswith("+")
    core = "".join(digits)
    if len(core) < 7:  # too short to be a valid phone
        return ""
    return ("+" if has_plus else "") + core


def build_notes(source: Dict[str, str]) -> str:
    notes: List[str] = []

    def add(label: str, key: str):
        value = (source.get(key, "") or "").strip()
        if value:
            notes.append(f"{label}: {value}")

    add("Invoice Ninja Número", "Número")
    add("Notas Privadas", "Notas Privadas")
    add("Notas Públicas", "Notas Públicas")
    add("Indústria (cliente)", "Indústria")
    add("Cliente Tamanho", "Cliente Tamanho")
    add("Cliente Moeda", "Cliente Moeda")
    add("Termos de Pagamento", "Cliente Termos de pagamento")
    add("NIF", "NIF")
    add("NUIT", "NUIT")
    add("NUEL", "NUEL")
    add("Número de Identificação", "Número de Identificação")

    # Address roll-up
    address_parts: List[str] = []
    for k in ("Rua", "Apto/Suíte", "Cidade", "Estado/Província", "Código postal", "País"):
        v = (source.get(k, "") or "").strip()
        if v:
            address_parts.append(v)
    if address_parts:
        notes.append("Endereço: " + ", ".join(address_parts))

    classification = (source.get("Classificação", "") or "").strip()
    if classification:
        notes.append(f"Classificação: {classification}")

    notes.append(f"Gerado por migração em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return " \n".join(notes)


def choose_phone(row: Dict[str, str], keys: List[str]) -> str:
    for key in keys:
        value = (row.get(key, "") or "").strip()
        if not value:
            continue
        phone = sanitize_phone(value)
        if phone:
            return phone
    return ""


def build_lead_doc(row: Dict[str, str], default_source: str = "", default_company: str = "", allow_company_from_source: bool = False) -> Dict[str, Any]:
    company_name = (row.get("Nome", "") or "").strip()
    first_name = (row.get("Primeiro nome", "") or "").strip()
    last_name = (row.get("Sobrenome", "") or "").strip()
    job_title = (row.get("Cargo", "") or "").strip()
    email = (row.get("E-mail", "") or "").strip()
    website = sanitize_website((row.get("Site", "") or "").strip())

    # Phones
    phone_mobile = choose_phone(row, ["Contato Telefónico", "Telefone do Cliente"])  # prefer contact
    phone_main = choose_phone(row, ["Telefone do Cliente", "Contato Telefónico"])    # prefer company

    # Lead name
    # Avoid numbers/emails in display name
    safe_last_name = last_name if not sanitize_phone(last_name) and not looks_like_email(last_name) and not looks_like_url(last_name) else ""
    safe_first_name = first_name if not looks_like_email(first_name) and not looks_like_url(first_name) else ""
    full_name = " ".join(p for p in [safe_first_name, safe_last_name] if p)
    lead_name = full_name or company_name or email or phone_mobile or phone_main or "Imported Lead"

    doc: Dict[str, Any] = {
        "doctype": "Lead",
        "first_name": first_name,
        "last_name": last_name,
        "lead_name": lead_name,
        "job_title": job_title,
        "email_id": email,
        "website": website,
        "mobile_no": phone_mobile,
        "whatsapp_no": phone_mobile,
        "phone": phone_main,
        "company_name": company_name,
        "country": normalize_country(row.get("País", "") or ""),
        # Safe defaults
        "status": "Lead",
        "type": "Client",
        "request_type": "Request for Information",
        "title": company_name or lead_name,
        "notes": build_notes(row),
    }

    if default_source:
        doc["source"] = default_source

    if default_company:
        doc["company"] = default_company
    elif allow_company_from_source:
        company_link = (row.get("Cliente Utilizador", "") or "").strip()
        if company_link:
            doc["company"] = company_link

    # If first_name/last_name are actually emails or numbers, drop them
    if looks_like_email(doc.get("first_name", "")) or sanitize_phone(doc.get("first_name", "")):
        doc.pop("first_name", None)
    if looks_like_email(doc.get("last_name", "")) or sanitize_phone(doc.get("last_name", "")):
        doc.pop("last_name", None)

    # Drop empty values
    doc = {k: v for k, v in doc.items() if v not in (None, "")}
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Invoice Ninja clients to ERPNext Lead JSON for n8n")
    parser.add_argument("--clients-csv", dest="clients_csv", default=CLIENTS_CSV, help="Path to clients.csv")
    parser.add_argument("--output", dest="output_json", default=OUTPUT_JSON, help="Path to write leads_import.json")
    parser.add_argument("--set-lead-source", dest="lead_source", default="", help="Set a fixed value for source (Lead Source). Leave empty to omit.")
    parser.add_argument("--set-company", dest="company", default="", help="Set a fixed value for company (Company link). Leave empty to omit.")
    parser.add_argument("--company-from-source", dest="company_from_source", action="store_true", help="Populate company using 'Cliente Utilizador' from CSV")
    args = parser.parse_args()

    with open(args.clients_csv, "r", encoding="utf-8", newline="") as cf:
        reader = csv.DictReader(cf)
        output: List[Dict[str, Any]] = []
        for row in reader:
            doc = build_lead_doc(row, default_source=args.lead_source, default_company=args.company, allow_company_from_source=args.company_from_source)
            output.append(doc)

    with open(args.output_json, "w", encoding="utf-8") as out:
        json.dump(output, out, ensure_ascii=False, indent=2)

    print(f"Wrote {args.output_json} with {len(output)} leads")


if __name__ == "__main__":
    main()


