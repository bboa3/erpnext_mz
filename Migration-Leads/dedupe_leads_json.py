#!/usr/bin/env python3
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

INPUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "leads_import.json"))
OUTPUT_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "leads_import_dedup.json"))


def is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def looks_like_url(text: str) -> bool:
    t = (text or "").strip().lower()
    return t.startswith("http://") or t.startswith("https://") or t.startswith("www.")


def looks_like_email(text: str) -> bool:
    return "@" in (text or "")


def sanitize_phone(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    if looks_like_url(raw) or looks_like_email(raw):
        return ""
    digits = []
    for ch in raw:
        if ch.isdigit():
            digits.append(ch)
    has_plus = raw.startswith("+")
    core = "".join(digits)
    if len(core) < 7:
        return ""
    return ("+" if has_plus else "") + core


def quality_score(doc: Dict[str, Any]) -> int:
    keys = [
        "first_name", "last_name", "company_name", "email_id",
        "mobile_no", "phone", "website", "country", "notes"
    ]
    score = 0
    for k in keys:
        if not is_empty(doc.get(k)):
            score += 1
    # bonus if both first and last name
    if doc.get("first_name") and doc.get("last_name"):
        score += 1
    # bonus for longer notes
    score += min(len((doc.get("notes") or "")), 200) // 50
    return score


def merge_notes(notes_list: List[str]) -> str:
    seen = set()
    lines_out: List[str] = []
    for text in notes_list:
        if is_empty(text):
            continue
        for line in str(text).splitlines():
            line_s = line.rstrip()
            if line_s and line_s not in seen:
                seen.add(line_s)
                lines_out.append(line_s)
    return "\n".join(lines_out)


def pick_longer(a: str, b: str) -> str:
    a = a or ""
    b = b or ""
    return a if len(a) >= len(b) else b


def merge_group(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Choose base by quality
    base = max(docs, key=quality_score)
    merged = dict(base)

    # Normalize/sanitize phones from all docs
    phones = set()
    mobiles = set()
    whatsapps = set()
    for d in docs:
        for key, target in (("phone", phones), ("mobile_no", mobiles), ("whatsapp_no", whatsapps)):
            val = sanitize_phone(d.get(key) or "")
            if val:
                target.add(val)

    # Reassign phones deterministically: prefer the longest as mobile, next as phone
    def longest_first(values: set) -> List[str]:
        return sorted(values, key=lambda s: (len(s), s), reverse=True)

    all_numbers = []
    all_numbers.extend(longest_first(mobiles))
    all_numbers.extend(x for x in longest_first(whatsapps) if x not in all_numbers)
    all_numbers.extend(x for x in longest_first(phones) if x not in all_numbers)

    merged["mobile_no"] = all_numbers[0] if all_numbers else merged.get("mobile_no")
    merged["phone"] = all_numbers[1] if len(all_numbers) > 1 else merged.get("phone")
    merged["whatsapp_no"] = merged.get("whatsapp_no") or merged.get("mobile_no")

    # Merge scalar fields if missing in base
    scalar_fields = [
        "first_name", "last_name", "company_name", "website", "country",
        "source", "company", "status", "type", "request_type", "title"
    ]
    for field in scalar_fields:
        if is_empty(merged.get(field)):
            for d in docs:
                if not is_empty(d.get(field)):
                    merged[field] = d[field]
                    break

    # Lead name: rebuild from first/last/company
    names = []
    if not is_empty(merged.get("first_name")):
        names.append(merged["first_name"])
    if not is_empty(merged.get("last_name")):
        names.append(merged["last_name"])
    lead_name = " ".join(names).strip()
    if not lead_name:
        lead_name = merged.get("company_name") or merged.get("lead_name")
    merged["lead_name"] = lead_name

    # Title: prefer company_name else lead_name
    merged["title"] = merged.get("company_name") or merged.get("title") or merged["lead_name"]

    # Merge notes
    merged["notes"] = merge_notes([d.get("notes") for d in docs])

    # Ensure doctype is correct
    merged["doctype"] = "Lead"

    # Remove empties
    merged = {k: v for k, v in merged.items() if not is_empty(v)}
    return merged


def main() -> None:
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        items: List[Dict[str, Any]] = json.load(f)

    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    no_email: List[Dict[str, Any]] = []

    for doc in items:
        email = (doc.get("email_id") or "").strip().lower()
        if email:
            groups[email].append(doc)
        else:
            no_email.append(doc)

    result: List[Dict[str, Any]] = []
    merged_count = 0
    for email, docs in groups.items():
        if len(docs) == 1:
            result.append(docs[0])
        else:
            merged = merge_group(docs)
            result.append(merged)
            merged_count += (len(docs) - 1)

    # Append no-email docs unchanged
    result.extend(no_email)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)

    print(json.dumps({
        "input_items": len(items),
        "output_items": len(result),
        "duplicates_removed": merged_count,
        "output_path": OUTPUT_JSON,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()


