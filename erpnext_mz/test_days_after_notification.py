#!/usr/bin/env python3
"""
Test and Debug "Days After" Notifications
Usage: bench --site SITE_NAME execute erpnext_mz.test_days_after_notification.test_days_after_notification
"""

import frappe
from frappe.utils import add_days, today, now

def test_days_after_notification():
    """Diagnose Days After notifications"""
    
    print("\n" + "=" * 80)
    print("DAYS AFTER NOTIFICATION DIAGNOSTIC")
    print("=" * 80)

    # 1. List all Days After notifications
    print("\n1. ALL 'DAYS AFTER' NOTIFICATIONS:")
    print("=" * 80)

    notifications = frappe.get_all("Notification",
        filters={"enabled": 1, "event": "Days After"},
        fields=["name", "document_type", "days_in_advance", "date_changed"],
        order_by="document_type"
    )

    if notifications:
        for notif in notifications:
            print(f"\n  {notif.name}")
            print(f"  - Document Type: {notif.document_type}")
            print(f"  - Days After: {notif.days_in_advance}")
            print(f"  - Date Field: {notif.date_changed}")
    else:
        print("  No 'Days After' notifications found")

    # 2. Check one specific notification in detail
    print("\n\n2. DETAILED CHECK - First Opportunity Notification:")
    print("=" * 80)

    opp_notif = frappe.get_all("Notification",
        filters={"enabled": 1, "event": "Days After", "document_type": "Opportunity"},
        fields=["name"],
        limit=1
    )

    if opp_notif:
        notif_name = opp_notif[0].name
        notif = frappe.get_doc("Notification", notif_name)
        
        print(f"\nName: {notif.name}")
        print(f"Enabled: {notif.enabled}")
        print(f"Event: {notif.event}")
        print(f"Days After: {notif.days_in_advance}")
        print(f"Date Field: {notif.date_changed}")
        print(f"Send Alert On: {notif.send_alert_on}")
        
        print(f"\nCondition:")
        if notif.condition:
            print(f"  {notif.condition}")
        else:
            print(f"  None (always triggers)")
        
        print(f"\nRecipients:")
        for recipient in notif.recipients:
            for field in ['email_by_document_field', 'receiver_by_role', 'email']:
                if hasattr(recipient, field) and getattr(recipient, field):
                    print(f"  - {field}: {getattr(recipient, field)}")
        
        # 3. Check if there are opportunities that should trigger this
        print("\n\n3. CHECKING OPPORTUNITIES THAT SHOULD TRIGGER:")
        print("=" * 80)
        
        target_date = add_days(today(), -int(notif.days_in_advance))
        date_field = notif.date_changed or "creation"
        
        print(f"\nLooking for Opportunities where {date_field} = {target_date}")
        
        opportunities = frappe.get_all("Opportunity",
            filters={
                date_field: [">=", target_date + " 00:00:00"],
                date_field: ["<=", target_date + " 23:59:59"]
            },
            fields=["name", "creation", "status", "opportunity_from"],
            limit=10
        )
        
        if opportunities:
            print(f"\nFound {len(opportunities)} opportunities:")
            for opp in opportunities:
                print(f"\n  {opp.name}")
                print(f"  - Created: {opp.creation}")
                print(f"  - Status: {opp.status}")
                
                # Check if condition matches
                if notif.condition:
                    try:
                        full_opp = frappe.get_doc("Opportunity", opp.name)
                        # Evaluate condition
                        condition_result = frappe.safe_eval(notif.condition, None, {"doc": full_opp})
                        print(f"  - Condition matches: {condition_result}")
                    except Exception as e:
                        print(f"  - Condition error: {e}")
        else:
            print(f"\n  No opportunities found from {target_date}")
        
        # 4. Check scheduled emails
        print("\n\n4. SCHEDULED EMAILS FOR THIS NOTIFICATION:")
        print("=" * 80)
        
        scheduled = frappe.db.sql("""
            SELECT name, document_name, scheduled_time, status, creation
            FROM `tabScheduled Email`
            WHERE notification = %s
            ORDER BY creation DESC
            LIMIT 10
        """, (notif.name,), as_dict=True)
        
        if scheduled:
            print(f"\nFound {len(scheduled)} scheduled emails:")
            for sched in scheduled:
                print(f"\n  {sched.name}")
                print(f"  - Document: {sched.document_name}")
                print(f"  - Scheduled: {sched.scheduled_time}")
                print(f"  - Status: {sched.status}")
                print(f"  - Created: {sched.creation}")
        else:
            print("\n  ❌ NO scheduled emails found")
            print("  This means notifications are NOT being queued!")
            
            print("\n  POSSIBLE REASONS:")
            print("  1. No documents match the date criteria")
            print("  2. Notification condition is filtering them out")
            print("  3. Scheduler is not running the 'send_daily_digest' job")
            print("  4. Recipients have no valid email")

    else:
        print("\n  No Opportunity 'Days After' notifications found")

    # 5. Check if scheduler is processing notifications
    print("\n\n5. SCHEDULER STATUS:")
    print("=" * 80)

    # Check last time daily digest ran
    last_digest = frappe.db.sql("""
        SELECT creation, status
        FROM `tabScheduled Job Log`
        WHERE job_name LIKE '%daily%' OR job_name LIKE '%notification%'
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)

    if last_digest:
        print("\nRecent notification/digest jobs:")
        for job in last_digest:
            print(f"  - {job.creation}: {job.status}")
    else:
        print("\n  ⚠️  No daily digest jobs found")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

