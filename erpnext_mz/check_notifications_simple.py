#!/usr/bin/env python3
"""
Simple Email Notification Checker
Usage: bench --site SITE_NAME console < check_notifications_simple.py
"""

import frappe
from frappe.utils import now, add_minutes

def check():
    print("\n" + "=" * 80)
    print("EMAIL NOTIFICATION QUICK CHECK")
    print("=" * 80)

    # 1. Check SMTP
    print("\n1. SMTP Configuration:")
    email_accounts = frappe.get_all("Email Account", 
        filters={"enable_outgoing": 1},
        fields=["name", "email_id", "default_outgoing"]
    )
    if email_accounts:
        for acc in email_accounts:
            print(f"   ✅ {acc.name} ({acc.email_id}) - Default: {acc.default_outgoing}")
    else:
        print("   ❌ No outgoing email account configured")

    # 2. Check Notifications
    print("\n2. Enabled Notifications:")
    notifications = frappe.get_all("Notification",
        filters={"enabled": 1, "channel": "Email"},
        fields=["name", "document_type", "event"]
    )
    if notifications:
        for notif in notifications:
            print(f"   ✅ {notif.name} ({notif.document_type} - {notif.event})")
    else:
        print("   ⚠️  No enabled email notifications")

    # 3. Check Scheduler
    print("\n3. Scheduler Status:")
    scheduler_enabled = frappe.db.get_single_value("System Settings", "enable_scheduler")
    print(f"   Scheduler Enabled: {'✅ Yes' if scheduler_enabled else '❌ NO'}")

    # Check last job
    last_job = frappe.db.sql("""
        SELECT creation 
        FROM `tabScheduled Job Log` 
        ORDER BY creation DESC 
        LIMIT 1
    """, as_dict=True)

    if last_job:
        from frappe.utils import get_datetime
        last_run = get_datetime(last_job[0].creation)
        minutes_ago = (get_datetime(now()) - last_run).total_seconds() / 60
        print(f"   Last Job: {minutes_ago:.1f} minutes ago")
        
        if minutes_ago > 10:
            print(f"   ❌ CRITICAL: No jobs in {minutes_ago:.1f} minutes - Workers NOT running!")
        else:
            print(f"   ✅ Workers are running")
    else:
        print("   ❌ No scheduled job logs found")

    # 4. Check Email Queue
    print("\n4. Email Queue:")
    queue_stats = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabEmail Queue`
        GROUP BY status
    """, as_dict=True)

    if queue_stats:
        for stat in queue_stats:
            icon = "✅" if stat.status == "Sent" else "⚠️" if stat.status == "Not Sent" else "❌"
            print(f"   {icon} {stat.status}: {stat.count}")
    else:
        print("   ℹ️  Email queue is empty")

    # 5. Check recent errors
    print("\n5. Recent Email Errors:")
    errors = frappe.db.sql("""
        SELECT name, status, error 
        FROM `tabEmail Queue`
        WHERE status = 'Error'
        ORDER BY creation DESC
        LIMIT 3
    """, as_dict=True)

    if errors:
        for err in errors:
            print(f"   ❌ {err.name}: {err.error[:100] if err.error else 'No error message'}")
    else:
        print("   ✅ No recent email errors")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)

    if not email_accounts:
        print("❌ CRITICAL: Configure Email Account")
    elif not scheduler_enabled:
        print("❌ CRITICAL: Enable scheduler")
    elif last_job and minutes_ago > 10:
        print("❌ CRITICAL: Start background workers")
        print("\n   Fix: bench restart (dev) or sudo supervisorctl restart frappe-bench-workers: (prod)")
    else:
        print("✅ Configuration looks good")
        
    print("=" * 80 + "\n")

