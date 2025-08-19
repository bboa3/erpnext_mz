#!/usr/bin/env python3
import csv
import os
from datetime import datetime
import argparse


CLIENTS_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "clients.csv"))
TEMPLATE_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "Erpnext-Lead-template.csv"))
OUTPUT_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "leads_import.csv"))


def normalize_country(country_value: str) -> str:
    if not country_value:
        return ""
    value = country_value.strip()
    # Common normalizations for ERPNext Country names
    replacements = {
        "Republic of Mozambique": "Mozambique",
        "República de Moçambique": "Mozambique",
        "Mocambique": "Mozambique",
        "Moçambique": "Mozambique",
    }
    return replacements.get(value, value)


def build_notes(source: dict) -> str:
    notes = []
    def add(label: str, key: str):
        value = source.get(key, "").strip()
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
    address_parts = []
    for k in ("Rua", "Apto/Suíte", "Cidade", "Estado/Província", "Código postal", "País"):
        v = source.get(k, "").strip()
        if v:
            address_parts.append(v)
    if address_parts:
        notes.append("Endereço: " + ", ".join(address_parts))

    classification = source.get("Classificação", "").strip()
    if classification:
        notes.append(f"Classificação: {classification}")

    # Timestamp for traceability
    notes.append(f"Gerado por migração em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return " \n".join(notes)


def choose_phone(row: dict, keys: list[str]) -> str:
    for key in keys:
        value = row.get(key, "").strip()
        if value:
            return value
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Invoice Ninja clients to ERPNext Lead import CSV")
    parser.add_argument("--set-lead-source", dest="lead_source", default="", help="Set a fixed value for Origem (Lead Source). Leave empty to skip.")
    parser.add_argument("--set-company", dest="company", default="", help="Set a fixed value for Empresa (Company). Leave empty to skip.")
    parser.add_argument("--company-from-source", dest="company_from_source", action="store_true", help="Populate Empresa using 'Cliente Utilizador' field from source.")
    args = parser.parse_args()
    # Read template headers
    with open(TEMPLATE_CSV, "r", encoding="utf-8", newline="") as tf:
        template_reader = csv.reader(tf)
        template_headers = next(template_reader)

    # Prepare output
    with open(CLIENTS_CSV, "r", encoding="utf-8", newline="") as cf, \
         open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as of:

        clients_reader = csv.DictReader(cf)
        writer = csv.DictWriter(of, fieldnames=template_headers)
        writer.writeheader()

        for row in clients_reader:
            lead_row = {header: "" for header in template_headers}

            company_name = (row.get("Nome", "") or "").strip()
            first_name = (row.get("Primeiro nome", "") or "").strip()
            last_name = (row.get("Sobrenome", "") or "").strip()
            email = (row.get("E-mail", "") or "").strip()
            website = (row.get("Site", "") or "").strip()

            # Names
            lead_row["Nome"] = first_name
            lead_row["Nome do Meio"] = ""
            lead_row["Sobrenome"] = last_name
            if company_name:
                lead_row["Nome da Organização"] = company_name
            full_name = " ".join(p for p in [first_name, last_name] if p)
            lead_row["Nome Completo"] = full_name or company_name

            # Contact details
            phone_mobile = choose_phone(row, ["Contato Telefónico", "Telefone do Cliente"])  # prefer contact phone
            phone_main = choose_phone(row, ["Telefone do Cliente", "Contato Telefónico"])    # prefer company phone
            lead_row["Telefone Celular"] = phone_mobile
            lead_row["Telefone"] = phone_main
            lead_row["Whatsapp"] = phone_mobile
            lead_row["Phone Ext."] = ""
            lead_row["Fax"] = ""

            # Web & Email
            lead_row["Email"] = email
            lead_row["Site"] = website

            # Company and classification
            lead_row["Indústria"] = (row.get("Indústria", "") or "").strip()

            # Geography
            lead_row["Cidade"] = (row.get("Cidade", "") or "").strip()
            lead_row["Estado / Província"] = (row.get("Estado/Província", "") or "").strip()
            lead_row["País"] = normalize_country(row.get("País", "") or "")

            # Campaign / Source
            campaign = (row.get("Notas Públicas", "") or "").strip()
            lead_row["Nome da Campanha"] = campaign
            # Lead Source optional
            if args.lead_source:
                lead_row["Origem"] = args.lead_source

            # ERPNext Company (optional)
            if args.company:
                lead_row["Empresa"] = args.company
            elif args.company_from_source:
                company_link = (row.get("Cliente Utilizador", "") or "").strip()
                if company_link:
                    lead_row["Empresa"] = company_link

            # Notes with extra identifiers
            lead_row["Nota (Notas)"] = build_notes(row)

            # Leave other fields blank by default; ERPNext will fill defaults on import

            # Ensure we only write keys present in template
            writer.writerow(lead_row)

    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()


