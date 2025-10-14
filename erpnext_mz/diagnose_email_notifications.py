#!/usr/bin/env python3
"""
Comprehensive Email Notification Diagnostic Script for ERPNext
Diagnoses why notifications work locally but fail in production

Usage: bench --site SITE_NAME console < diagnose_email_notifications.py
"""

import frappe
from frappe.utils import now, get_datetime
import json

def diagnose_email_notifications():
    """
    Comprehensive diagnostic for email notification issues
    """
    
    print("\n" + "=" * 100)
    print("EMAIL NOTIFICATION DIAGNOSTIC REPORT")
    print("=" * 100)
    print(f"Site: {frappe.local.site}")
    print(f"Time: {now()}")
    print("=" * 100)
    
    # ============================================================================
    # 1. SMTP CONFIGURATION
    # ============================================================================
    print("\n" + "=" * 100)
    print("1. SMTP / EMAIL ACCOUNT CONFIGURATION")
    print("=" * 100)
    
    email_accounts = frappe.get_all("Email Account", 
        filters={"enable_outgoing": 1},
        fields=["name", "email_id", "smtp_server", "smtp_port", "use_tls", 
                "use_ssl", "enable_outgoing", "default_outgoing", "awaiting_password"]
    )
    
    if not email_accounts:
        print("❌ CRITICAL: No outgoing email accounts configured!")
        print("   Action: Configure at least one Email Account with 'Enable Outgoing' checked")
    else:
        print(f"✅ Found {len(email_accounts)} outgoing email account(s):")
        for acc in email_accounts:
            print(f"\n   Account: {acc.name}")
            print(f"   - Email: {acc.email_id}")
            print(f"   - SMTP Server: {acc.smtp_server}:{acc.smtp_port}")
            print(f"   - TLS: {acc.use_tls}, SSL: {acc.use_ssl}")
            print(f"   - Default Outgoing: {'✅' if acc.default_outgoing else '❌'}")
            print(f"   - Awaiting Password: {'⚠️ YES - Password not set!' if acc.awaiting_password else '✅ No'}")
            
            # Test connection
            try:
                email_account = frappe.get_doc("Email Account", acc.name)
                # Check if password exists
                if email_account.password:
                    print(f"   - Password: ✅ Set")
                else:
                    print(f"   - Password: ❌ NOT SET")
                    
            except Exception as e:
                print(f"   - Error loading account: {e}")
    
    # ============================================================================
    # 2. NOTIFICATION CONFIGURATION
    # ============================================================================
    print("\n" + "=" * 100)
    print("2. NOTIFICATION CONFIGURATION")
    print("=" * 100)
    
    notifications = frappe.get_all("Notification",
        filters={"enabled": 1, "channel": ["in", ["Email", "System Notification"]]},
        fields=["name", "document_type", "event", "enabled", "channel", 
                "send_to_all_assignees", "is_standard"]
    )
    
    if not notifications:
        print("⚠️  No enabled notifications found")
    else:
        print(f"✅ Found {len(notifications)} enabled notification(s):")
        for notif in notifications:
            print(f"\n   Notification: {notif.name}")
            print(f"   - Document Type: {notif.document_type}")
            print(f"   - Event: {notif.event}")
            print(f"   - Channel: {notif.channel}")
            print(f"   - Standard: {'Yes' if notif.is_standard else 'Custom'}")
            
            # Get detailed config
            try:
                notif_doc = frappe.get_doc("Notification", notif.name)
                
                # Check recipients
                recipients = []
                if notif_doc.send_to_all_assignees:
                    recipients.append("All Assignees")
                
                for recipient in notif_doc.recipients:
                    if hasattr(recipient, 'email_by_document_field') and recipient.email_by_document_field:
                        recipients.append(f"Field: {recipient.email_by_document_field}")
                    elif hasattr(recipient, 'receiver_by_document_field') and recipient.receiver_by_document_field:
                        recipients.append(f"Field: {recipient.receiver_by_document_field}")
                    elif hasattr(recipient, 'receiver_by_role') and recipient.receiver_by_role:
                        recipients.append(f"Role: {recipient.receiver_by_role}")
                    elif hasattr(recipient, 'email') and recipient.email:
                        recipients.append(f"Email: {recipient.email}")
                
                if recipients:
                    print(f"   - Recipients: {', '.join(recipients)}")
                else:
                    print(f"   - Recipients: ⚠️ NONE CONFIGURED!")
                
                # Check conditions
                if notif_doc.condition:
                    print(f"   - Condition: {notif_doc.condition[:80]}...")
                else:
                    print(f"   - Condition: None (always triggers)")
                
                # Check subject and message
                if notif_doc.subject:
                    print(f"   - Subject: {notif_doc.subject[:60]}...")
                else:
                    print(f"   - Subject: ⚠️ NOT SET!")
                
                if notif_doc.message:
                    print(f"   - Message: {len(notif_doc.message)} chars")
                else:
                    print(f"   - Message: ⚠️ EMPTY!")
                    
            except Exception as e:
                print(f"   - Error loading notification: {e}")
    
    # ============================================================================
    # 3. EMAIL QUEUE STATUS
    # ============================================================================
    print("\n" + "=" * 100)
    print("3. EMAIL QUEUE STATUS")
    print("=" * 100)
    
    # Count by status
    queue_stats = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabEmail Queue`
        GROUP BY status
    """, as_dict=True)
    
    if queue_stats:
        print("Email Queue Statistics:")
        for stat in queue_stats:
            icon = "✅" if stat.status == "Sent" else "⚠️" if stat.status == "Not Sent" else "❌"
            print(f"   {icon} {stat.status}: {stat.count}")
    else:
        print("   ℹ️  Email queue is empty")
    
    # Recent failed emails
    try:
        failed_emails = frappe.db.sql("""
            SELECT name, status, error, sender, creation
            FROM `tabEmail Queue`
            WHERE status IN ('Error', 'Expired')
            ORDER BY creation DESC
            LIMIT 5
        """, as_dict=True)
        
        if failed_emails:
            print(f"\n   ❌ Recent Failed Emails ({len(failed_emails)}):")
            for email in failed_emails:
                print(f"\n   Email: {email.name}")
                print(f"   - Status: {email.status}")
                print(f"   - From: {email.sender}")
                print(f"   - Created: {email.creation}")
                if email.error:
                    print(f"   - Error: {email.error[:200]}")
    except Exception as e:
        print(f"\n   ⚠️  Could not check failed emails: {e}")
    
    # Stuck emails (Not Sent for > 1 hour)
    try:
        stuck_emails = frappe.db.sql("""
            SELECT name, sender, creation, modified
            FROM `tabEmail Queue`
            WHERE status = 'Not Sent'
            AND creation < DATE_SUB(NOW(), INTERVAL 1 HOUR)
            ORDER BY creation DESC
            LIMIT 10
        """, as_dict=True)
        
        if stuck_emails:
            print(f"\n   ⚠️  Stuck Emails (Not Sent > 1 hour): {len(stuck_emails)}")
            for email in stuck_emails:
                print(f"   - {email.name}: {email.sender} (Created: {email.creation})")
    except Exception as e:
        print(f"\n   ⚠️  Could not check stuck emails: {e}")
    
    # ============================================================================
    # 4. BACKGROUND WORKERS & SCHEDULER
    # ============================================================================
    print("\n" + "=" * 100)
    print("4. BACKGROUND WORKERS & SCHEDULER STATUS")
    print("=" * 100)
    
    # Check scheduler status
    try:
        scheduler_enabled = frappe.db.get_single_value("System Settings", "enable_scheduler")
        print(f"   Scheduler Enabled: {'✅ Yes' if scheduler_enabled else '❌ NO - CRITICAL!'}")
        
        if not scheduler_enabled:
            print("   Action: Enable scheduler with: bench --site SITE_NAME scheduler enable")
    except Exception as e:
        print(f"   ⚠️  Could not check scheduler status: {e}")
        scheduler_enabled = None
    
    # Check if scheduler is actually running (last job execution)
    try:
        last_job = frappe.db.sql("""
            SELECT name, creation
            FROM `tabScheduled Job Log`
            ORDER BY creation DESC
            LIMIT 1
        """, as_dict=True)
        
        if last_job:
            last_run = get_datetime(last_job[0].creation)
            minutes_ago = (get_datetime(now()) - last_run).total_seconds() / 60
            print(f"   Last Scheduled Job: {minutes_ago:.1f} minutes ago")
            
            if minutes_ago > 10:
                print(f"   ⚠️  WARNING: No scheduled jobs in {minutes_ago:.1f} minutes!")
                print(f"   Action: Check if workers are running: bench doctor")
        else:
            print("   ⚠️  No scheduled job logs found")
    except Exception as e:
        print(f"   ℹ️  Cannot check scheduled jobs: {e}")
    
    # Check email queue processing job
    try:
        email_jobs = frappe.db.sql("""
            SELECT name, creation, status
            FROM `tabScheduled Job Log`
            WHERE job_name LIKE '%email%'
            ORDER BY creation DESC
            LIMIT 5
        """, as_dict=True)
        
        if email_jobs:
            print(f"\n   Recent Email Queue Jobs:")
            for job in email_jobs:
                print(f"   - {job.name}: {job.status} ({job.creation})")
    except:
        pass
    
    # ============================================================================
    # 5. SYSTEM PERMISSIONS & SETTINGS
    # ============================================================================
    print("\n" + "=" * 100)
    print("5. SYSTEM PERMISSIONS & SETTINGS")
    print("=" * 100)
    
    # Check Email Settings
    try:
        email_settings = frappe.get_single("Email Settings")
        print(f"   Email Settings:")
        print(f"   - Auto Email ID: {email_settings.auto_email_id or '❌ Not set'}")
        print(f"   - Send Print in Body: {'Yes' if email_settings.send_print_in_body_and_attachment else 'No'}")
        print(f"   - Email Limit: {email_settings.email_limit or 'Unlimited'}")
    except Exception as e:
        print(f"   ⚠️  Cannot load Email Settings: {e}")
    
    # Check System Settings
    try:
        system_settings = frappe.get_single("System Settings")
        print(f"\n   System Settings:")
        print(f"   - Enable Scheduler: {'✅ Yes' if system_settings.enable_scheduler else '❌ NO'}")
        print(f"   - Setup Complete: {'Yes' if system_settings.setup_complete else 'No'}")
    except Exception as e:
        print(f"   ⚠️  Cannot load System Settings: {e}")
    
    # ============================================================================
    # 6. RECENT ERROR LOGS
    # ============================================================================
    print("\n" + "=" * 100)
    print("6. RECENT ERROR LOGS (Email/Notification Related)")
    print("=" * 100)
    
    error_logs = frappe.get_all("Error Log",
        filters={
            "creation": [">", frappe.utils.add_days(now(), -1)],
            "error": ["like", "%email%"]
        },
        fields=["name", "method", "error", "creation"],
        order_by="creation desc",
        limit=10
    )
    
    if error_logs:
        print(f"   Found {len(error_logs)} email-related errors in last 24 hours:")
        for log in error_logs:
            print(f"\n   Error: {log.name}")
            print(f"   - Method: {log.method}")
            print(f"   - Time: {log.creation}")
            print(f"   - Error: {log.error[:300]}...")
    else:
        print("   ✅ No email-related errors in last 24 hours")
    
    # ============================================================================
    # 7. COMMUNICATION DOCTYPE CHECK
    # ============================================================================
    print("\n" + "=" * 100)
    print("7. COMMUNICATION DOCTYPE STATUS")
    print("=" * 100)
    
    recent_comms = frappe.get_all("Communication",
        filters={
            "communication_type": "Communication",
            "sent_or_received": "Sent",
            "creation": [">", frappe.utils.add_days(now(), -1)]
        },
        fields=["name", "subject", "sender", "recipients", "creation", "delivery_status"],
        order_by="creation desc",
        limit=5
    )
    
    if recent_comms:
        print(f"   ✅ Recent Communications (last 24h): {len(recent_comms)}")
        for comm in recent_comms:
            print(f"\n   - {comm.name}")
            print(f"     Subject: {comm.subject}")
            print(f"     From: {comm.sender}")
            print(f"     To: {comm.recipients}")
            print(f"     Status: {comm.delivery_status or 'Unknown'}")
    else:
        print("   ℹ️  No communications sent in last 24 hours")
    
    # ============================================================================
    # 8. DIAGNOSTIC SUMMARY & RECOMMENDATIONS
    # ============================================================================
    print("\n" + "=" * 100)
    print("8. DIAGNOSTIC SUMMARY & RECOMMENDATIONS")
    print("=" * 100)
    
    issues = []
    
    # Check critical issues
    if not email_accounts:
        issues.append("❌ CRITICAL: No outgoing email account configured")
    elif any(acc.awaiting_password for acc in email_accounts):
        issues.append("❌ CRITICAL: Email account password not set")
    
    if not scheduler_enabled:
        issues.append("❌ CRITICAL: Scheduler is disabled")
    
    if stuck_emails:
        issues.append(f"⚠️  WARNING: {len(stuck_emails)} emails stuck in queue")
    
    if failed_emails:
        issues.append(f"⚠️  WARNING: {len(failed_emails)} failed emails in queue")
    
    if issues:
        print("\n   ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n   ✅ No critical issues detected")
    
    print("\n" + "=" * 100)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    try:
        diagnose_email_notifications()
    except Exception as e:
        print(f"\n❌ Diagnostic script error: {e}")
        import traceback
        traceback.print_exc()

