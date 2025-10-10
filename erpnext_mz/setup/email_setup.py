import os
import re
from typing import Dict, Optional, Tuple

import frappe
from frappe import _


def _to_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y", "on"}


def _to_int(value: object, default: Optional[int] = None) -> Optional[int]:
    try:
        if value is None or value == "":
            return default
        return int(str(value).strip())
    except Exception:
        return default


def _read_env_file(path: str) -> Dict[str, str]:
    """Lightweight .env reader. Supports KEY=VALUE with optional quotes; ignores comments and blank lines."""
    data: Dict[str, str] = {}
    if not path:
        return data
    try:
        if not os.path.exists(path):
            return data
        with open(path, "r", encoding="utf-8") as f:
            for raw in f.readlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                # strip inline comments that start with space then #
                if " #" in line:
                    line = line.split(" #", 1)[0].strip()
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                data[key] = val
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Read .env for SMTP failed")
    return data


def _apply_placeholders(text: Optional[str], *, company_name: str) -> Optional[str]:
    if not text:
        return text
    return text.replace("{{Company Name}}", company_name)


def _normalize_encryption(value: Optional[str]) -> str:
    v = (value or "").strip().upper()
    if v in {"SSL", "TLS", "STARTTLS"}:
        return v
    return ""  # none


def _guess_protocol_from_host(host: Optional[str]) -> str:
    h = (host or "").lower()
    if "imap" in h:
        return "IMAP"
    if "pop" in h:
        return "POP3"
    return "IMAP"  # safer default


def _default_port(protocol: str, encryption: str, *, outgoing: bool = False) -> int:
    if outgoing:
        # SMTP
        if encryption == "SSL":
            return 465
        if encryption in {"TLS", "STARTTLS"}:
            return 587
        return 25
    # Incoming
    if protocol == "IMAP":
        if encryption == "SSL":
            return 993
        return 143
    # POP3
    if encryption == "SSL":
        return 995
    return 110


def _collect_smtp_settings(company_name: str) -> Dict[str, object]:
    """Collect SMTP settings from precedence: OS env > site config > .env file.

    .env path precedence: MZ_SMTP_ENV_PATH > <app>/erpnext_mz/env
    """
    site_conf = frappe.local.conf or {}
    env_path = os.environ.get("MZ_SMTP_ENV_PATH") or site_conf.get("mz_smtp_env_path")
    if not env_path:
        # Try two common locations: apps/erpnext_mz/.env and apps/erpnext_mz/erpnext_mz/.env
        try:
            candidate1 = frappe.get_app_path("erpnext_mz", "..", ".env")
            print(f"Candidate1: {candidate1}")
        except Exception:
            candidate1 = None
        env_path = candidate1 if candidate1 and os.path.exists(candidate1) else None

    file_env = _read_env_file(env_path) if env_path else {}

    def pick(key: str) -> Optional[str]:
        return (
            os.environ.get(key)
            or site_conf.get(key)
            or file_env.get(key)
        )

    data: Dict[str, object] = {
        "domain_name": pick("MZ_SMTP_DOMAIN_NAME"),
        "email": pick("MZ_SMTP_EMAIL"),
        "username": pick("MZ_SMTP_USERNAME"),
        "password": pick("MZ_SMTP_PASSWORD"),
        "account_name": pick("MZ_SMTP_ACCOUNT_NAME"),
        "auth_method": (pick("MZ_SMTP_AUTH_METHOD") or "Basic").strip(),
        # Incoming
        "enable_incoming": _to_bool(pick("MZ_SMTP_ENABLE_INCOMING"), False),
        "incoming_server": pick("MZ_SMTP_INCOMING_SERVER"),
        "incoming_port": _to_int(pick("MZ_SMTP_INCOMING_PORT")),
        "incoming_encryption": _normalize_encryption(pick("MZ_SMTP_INCOMING_ENCRYPTION")),
        "incoming_protocol": (pick("MZ_SMTP_INCOMING_PROTOCOL") or "").strip().upper(),
        # Outgoing
        "enable_outgoing": _to_bool(pick("MZ_SMTP_ENABLE_OUTGOING"), True),
        "outgoing_server": pick("MZ_SMTP_OUTGOING_SERVER"),
        "outgoing_port": _to_int(pick("MZ_SMTP_OUTGOING_PORT")),
        "outgoing_encryption": _normalize_encryption(pick("MZ_SMTP_OUTGOING_ENCRYPTION")),
        # Options
        "attachment_limit": _to_int(pick("MZ_SMTP_ATTACHMENT_LIMIT")),
        "use_imap": None,  # may be inferred
        "append_to": pick("MZ_SMTP_APPEND_TO"),
        "append_sent": _to_bool(pick("MZ_SMTP_APPEND_TO_SENT_FOLDER")),
        "sent_folder_name": pick("MZ_SMTP_SENT_FOLDER_NAME") or "Sent",
        "always_use_account_email": _to_bool(pick("MZ_SMTP_ALWAYS_USE_ACCOUNT_EMAIL_AS_SENDER"), True),
        "always_use_account_name": _to_bool(pick("MZ_SMTP_ALWAYS_USE_ACCOUNT_NAME_AS_SENDER_NAME"), True),
        "default_outgoing": _to_bool(pick("MZ_SMTP_DEFAULT_OUTGOING"), True),
        "default_incoming": _to_bool(pick("MZ_SMTP_DEFAULT_INCOMING"), False),
        "test_recipient": pick("MZ_SMTP_TEST_RECIPIENT"),
    }

    # Fill missing domain by deriving from email address
    if not data["domain_name"] and data["email"] and "@" in str(data["email"]):
        data["domain_name"] = str(data["email"]).split("@", 1)[1]

    # Protocol inference
    if not data["incoming_protocol"]:
        data["incoming_protocol"] = _guess_protocol_from_host(data["incoming_server"])  # type: ignore[arg-type]
    data["use_imap"] = data["incoming_protocol"] == "IMAP"

    # Ports
    if data["incoming_port"] is None:
        data["incoming_port"] = _default_port(
            protocol=str(data["incoming_protocol"]),
            encryption=str(data["incoming_encryption"]),
            outgoing=False,
        )
    if data["outgoing_port"] is None:
        data["outgoing_port"] = _default_port(
            protocol="SMTP",
            encryption=str(data["outgoing_encryption"]),
            outgoing=True,
        )

    # Placeholders in account name
    data["account_name"] = _apply_placeholders(data["account_name"], company_name=company_name)

    return data


def _ensure_email_domain(settings: Dict[str, object]) -> Tuple[str, bool]:
    """Create or update Email Domain. Returns (name, created)."""
    domain_name = str(settings["domain_name"] or "").strip()
    if not domain_name:
        raise ValueError("MZ_SMTP_DOMAIN_NAME or email domain is required")

    doc = None
    created = False
    try:
        if frappe.db.exists("Email Domain", domain_name):
            doc = frappe.get_doc("Email Domain", domain_name)
        else:
            doc = frappe.new_doc("Email Domain")
            doc.domain_name = domain_name
            created = True

        # Incoming
        doc.email_server = settings.get("incoming_server") or doc.email_server
        doc.use_imap = 1 if settings.get("use_imap") else 0
        doc.use_ssl = 1 if settings.get("incoming_encryption") == "SSL" else 0
        # STARTTLS applies to IMAP and when not SSL
        doc.use_starttls = 1 if (settings.get("incoming_encryption") in {"TLS", "STARTTLS"} and settings.get("use_imap")) and not doc.use_ssl else 0
        doc.incoming_port = settings.get("incoming_port")
        if settings.get("attachment_limit") is not None:
            doc.attachment_limit = settings.get("attachment_limit")

        # Outgoing
        doc.smtp_server = settings.get("outgoing_server") or doc.smtp_server
        doc.use_tls = 1 if settings.get("outgoing_encryption") in {"TLS", "STARTTLS"} else 0
        doc.use_ssl_for_outgoing = 1 if settings.get("outgoing_encryption") == "SSL" else 0
        doc.smtp_port = settings.get("outgoing_port")

        # Sent folder (IMAP)
        if settings.get("use_imap") and settings.get("append_sent"):
            doc.append_emails_to_sent_folder = 1
            doc.sent_folder_name = settings.get("sent_folder_name") or "Sent"
        else:
            doc.append_emails_to_sent_folder = 0
            doc.sent_folder_name = None

        if created:
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)

        return doc.name, created
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Create/Update Email Domain failed")
        raise


def _ensure_email_account(company_name: str, settings: Dict[str, object], domain_name: str) -> Tuple[str, bool]:
    """Create or update Email Account linked to Email Domain. Returns (name, created)."""
    email_id = str(settings.get("email") or "").strip()
    if not email_id:
        raise ValueError("MZ_SMTP_EMAIL is required")

    account_name = str(settings.get("account_name") or email_id.split("@", 1)[0]).strip()
    
    # IMPORTANT: Remove commas from account name as they break email validation
    # Email format is: "Display Name" <email@example.com>
    if "," in account_name:
        account_name = account_name.replace(",", "").strip()
        # Clean up double spaces
        while "  " in account_name:
            account_name = account_name.replace("  ", " ")

    # Find existing by email_id OR by account_name (to avoid PRIMARY KEY conflicts)
    existing_name = frappe.db.get_value("Email Account", {"email_id": email_id})
    
    # Also check if an Email Account with this name already exists
    if not existing_name and frappe.db.exists("Email Account", account_name):
        existing_name = account_name
    
    created = False
    try:
        if existing_name:
            acc = frappe.get_doc("Email Account", existing_name)
        else:
            acc = frappe.new_doc("Email Account")
            acc.email_id = email_id
            created = True

        # Basic properties
        acc.email_account_name = account_name
        acc.domain = domain_name
        acc.auth_method = (settings.get("auth_method") or "Basic")

        # If a domain is linked, copy domain values into the account fields so
        # server-side operations (sendmail_config/get_incoming_server) have concrete values.
        if acc.domain:
            domain_values = frappe.db.get_value(
                "Email Domain", domain_name, [
                    "email_server",
                    "use_imap",
                    "use_ssl",
                    "use_starttls",
                    "attachment_limit",
                    "smtp_server",
                    "smtp_port",
                    "use_ssl_for_outgoing",
                    "use_tls",
                    "incoming_port",
                    "append_emails_to_sent_folder",
                    "sent_folder_name",
                ],
                as_dict=True,
            ) or {}

            acc.email_server = domain_values.get("email_server")
            acc.use_imap = 1 if domain_values.get("use_imap") else 0
            acc.use_ssl = 1 if domain_values.get("use_ssl") else 0
            acc.use_starttls = 1 if domain_values.get("use_starttls") else 0
            if domain_values.get("attachment_limit") is not None:
                acc.attachment_limit = domain_values.get("attachment_limit")

            acc.smtp_server = domain_values.get("smtp_server")
            acc.smtp_port = domain_values.get("smtp_port")
            acc.use_ssl_for_outgoing = 1 if domain_values.get("use_ssl_for_outgoing") else 0
            acc.use_tls = 1 if domain_values.get("use_tls") else 0

            acc.incoming_port = domain_values.get("incoming_port")
            acc.append_emails_to_sent_folder = 1 if domain_values.get("append_emails_to_sent_folder") else 0
            # sent_folder_name is present on Email Domain and Email Account
            acc.sent_folder_name = domain_values.get("sent_folder_name")

        # Login
        username = str(settings.get("username") or "").strip()
        if username and username != email_id:
            acc.login_id_is_different = 1
            acc.login_id = username
        else:
            acc.login_id_is_different = 0
            acc.login_id = None

        password = settings.get("password")
        if acc.auth_method == "Basic":
            if not password:
                raise ValueError("MZ_SMTP_PASSWORD is required for Basic authentication")
            acc.password = password  # Frappe stores encrypted
            acc.awaiting_password = 0

        # Incoming
        acc.enable_incoming = 1 if settings.get("enable_incoming") else 0
        # If not using domain, configure incoming fields explicitly
        if not acc.domain and acc.enable_incoming:
            use_imap = 1 if settings.get("use_imap") else 0
            acc.use_imap = use_imap
            acc.email_server = settings.get("incoming_server")
            acc.incoming_port = settings.get("incoming_port")
            acc.use_ssl = 1 if settings.get("incoming_encryption") == "SSL" else 0
            acc.use_starttls = 1 if (settings.get("incoming_encryption") in {"TLS", "STARTTLS"} and use_imap and not acc.use_ssl) else 0

        acc.default_incoming = 1 if settings.get("default_incoming") else 0
        if settings.get("append_to") and not settings.get("use_imap"):
            acc.append_to = settings.get("append_to")

        # Outgoing
        acc.enable_outgoing = 1 if settings.get("enable_outgoing") else 0
        acc.default_outgoing = 1 if settings.get("default_outgoing") else 0
        acc.always_use_account_email_id_as_sender = 1 if settings.get("always_use_account_email") else 0
        acc.always_use_account_name_as_sender_name = 1 if settings.get("always_use_account_name") else 0

        if not acc.domain and acc.enable_outgoing:
            enc = settings.get("outgoing_encryption")
            acc.smtp_server = settings.get("outgoing_server")
            acc.smtp_port = settings.get("outgoing_port")
            acc.use_tls = 1 if enc in {"TLS", "STARTTLS"} else 0
            acc.use_ssl_for_outgoing = 1 if enc == "SSL" else 0

        # Save and validate connectivity
        if created:
            acc.insert(ignore_permissions=True)
        else:
            acc.save(ignore_permissions=True)

        # Explicitly validate connections if enabled
        try:
            if acc.enable_outgoing:
                acc.validate_smtp_conn()
            if acc.enable_incoming:
                acc.get_incoming_server()
        except Exception:
            # Connection failed; surface error to caller as ValidationError
            raise

        return acc.name, created
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Create/Update Email Account failed")
        raise


def ensure_smtp_setup(company_name: str) -> Dict[str, object]:
    """Ensure Email Domain and Email Account are configured from .env / environment variables.

    Returns a dict with details and success flag.
    """
    settings = _collect_smtp_settings(company_name)

    # Quick sanity checks
    missing = []
    for key in ["email", "password", "outgoing_server", "domain_name"]:
        if not settings.get(key):
            missing.append(key)
    if settings.get("enable_incoming") and not settings.get("incoming_server"):
        missing.append("incoming_server")

    if missing:
        msg = ", ".join(missing)
        return {"ok": False, "message": f"SMTP setup skipped, missing: {msg}", "details": settings}

    # Create / update
    domain, domain_created = _ensure_email_domain(settings)
    account, account_created = _ensure_email_account(company_name, settings, domain)

    return {
        "ok": True,
        "message": _("SMTP configured successfully"),
        "domain": domain,
        "domain_created": domain_created,
        "account": account,
        "account_created": account_created,
    }



