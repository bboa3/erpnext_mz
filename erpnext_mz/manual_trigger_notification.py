#!/usr/bin/env python3
"""
Manually trigger a notification to test if it works
Usage: bench --site SITE_NAME execute erpnext_mz.manual_trigger_notification.manual_trigger_notification
"""

import frappe

def manual_trigger_notification():
    """Manually trigger a notification for testing"""
    
    print("\n" + "=" * 80)
    print("MANUAL NOTIFICATION TRIGGER TEST")
    print("=" * 80)

    # Get all Opportunity notifications
    notifs = frappe.get_all("Notification",
        filters={"enabled": 1, "document_type": "Opportunity"},
        fields=["name", "event"],
        limit=10
    )

    if not notifs:
        print("\n❌ No Opportunity notifications found")
        return

    print(f"\nAvailable Opportunity notifications:")
    for i, notif in enumerate(notifs):
        print(f"  {i+1}. {notif.name} ({notif.event})")

    # Use first one by default
    notif_name = notifs[2].name
    print(f"\nUsing: {notif_name}")

    # Get the notification
    try:
        notif = frappe.get_doc("Notification", notif_name)
    except:
        print(f"❌ Notification '{notif_name}' not found")
        return

    print(f"\n✅ Found notification: {notif.name}")
    print(f"   Document Type: {notif.document_type}")
    print(f"   Event: {notif.event}")

    # Get a test document
    print(f"\nLooking for test Opportunities...")

    docs = frappe.get_all("Opportunity",
        fields=["name", "status", "creation"],
        limit=5,
        order_by="creation desc"
    )

    if not docs:
        print(f"❌ No Opportunity documents found")
        return

    print(f"\nAvailable Opportunities (using first one):")
    for i, doc in enumerate(docs):
        marker = "→" if i == 0 else " "
        print(f"  {marker} {doc.name} - {doc.status} ({doc.creation})")

    doc_name = docs[0].name
    print(f"\nUsing: {doc_name}")

    # Load the document
    doc = frappe.get_doc("Opportunity", doc_name)

    print(f"\n" + "=" * 80)
    print("ATTEMPTING TO SEND NOTIFICATION")
    print("=" * 80)

    try:
        # Try to send
        print(f"\nCalling notif.send(doc)...")
        notif.send(doc)
        
        print(f"\n✅ SUCCESS - Notification method executed!")
        print(f"\nChecking Email Queue...")
        
        # Check email queue
        emails = frappe.get_all("Email Queue",
            filters={
                "reference_doctype": "Opportunity",
                "reference_name": doc.name,
                "creation": [">", frappe.utils.add_to_date(frappe.utils.now(), minutes=-5)]
            },
            fields=["name", "status", "sender", "error"],
            limit=5
        )
        
        if emails:
            print(f"   ✅ Found {len(emails)} email(s) in queue:")
            for email in emails:
                print(f"\n   {email.name}")
                print(f"   - Status: {email.status}")
                print(f"   - From: {email.sender}")
                if email.error:
                    print(f"   - Error: {email.error[:200]}")
        else:
            print(f"   ⚠️  No emails found in queue")
            print(f"\n   Possible reasons:")
            print(f"   1. Notification condition doesn't match this document")
            print(f"   2. No recipients configured or recipients have no email")
            print(f"   3. Template error prevented email creation")
            
            # Check notification recipients
            print(f"\n   Checking recipients:")
            for recipient in notif.recipients:
                for field in ['email_by_document_field', 'receiver_by_role', 'email']:
                    if hasattr(recipient, field) and getattr(recipient, field):
                        field_name = getattr(recipient, field)
                        print(f"   - {field}: {field_name}")
                        
                        # Check if field exists on doc
                        if field == 'email_by_document_field':
                            value = getattr(doc, field_name, None)
                            print(f"     Value on document: {value or '❌ EMPTY'}")
            
            # Check condition
            if notif.condition:
                print(f"\n   Checking condition:")
                print(f"   {notif.condition}")
                try:
                    result = frappe.safe_eval(notif.condition, None, {"doc": doc})
                    print(f"   Result: {result}")
                except Exception as e:
                    print(f"   ❌ Condition error: {e}")
                    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

