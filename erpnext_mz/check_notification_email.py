#!/usr/bin/env python3
"""
Quick check if notification created email
Usage: bench --site SITE_NAME execute erpnext_mz.check_notification_email.check_notification_email
"""

import frappe

def check_notification_email():
    """Check if notification created an email"""
    
    print("\n" + "=" * 80)
    print("NOTIFICATION EMAIL CHECK")
    print("=" * 80)
    
    # Get recent Opportunities
    opps = frappe.get_all("Opportunity",
        fields=["name", "creation"],
        order_by="creation desc",
        limit=3
    )
    
    if not opps:
        print("\n❌ No Opportunities found")
        return
    
    print(f"\nChecking last 3 Opportunities:")
    for opp in opps:
        print(f"\n{opp.name} (Created: {opp.creation})")
        
        # Check email queue
        emails = frappe.get_all("Email Queue",
            filters={
                "reference_doctype": "Opportunity",
                "reference_name": opp.name
            },
            fields=["name", "status", "sender", "creation", "recipients", "error"],
            order_by="creation desc"
        )
        
        if emails:
            print(f"  ✅ Found {len(emails)} email(s):")
            for email in emails:
                print(f"\n    {email.name}")
                print(f"    - Status: {email.status}")
                print(f"    - To: {email.recipients}")
                print(f"    - Created: {email.creation}")
                if email.error:
                    print(f"    - Error: {email.error[:150]}")
        else:
            print(f"  ❌ No emails in queue for this Opportunity")
            
            # Check why
            opp_doc = frappe.get_doc("Opportunity", opp.name)
            
            # Check if it has contact_email
            contact_email = getattr(opp_doc, 'contact_email', None)
            owner = getattr(opp_doc, 'owner', None)
            
            print(f"\n    Checking recipient fields:")
            print(f"    - contact_email: {contact_email or '❌ EMPTY'}")
            print(f"    - owner: {owner or '❌ EMPTY'}")
            
            # Check "Dia 3" notification condition
            try:
                notif = frappe.get_doc("Notification", "Dia 3 — Lead Form Task — MozEconomia Cloud")
                if notif.condition:
                    try:
                        result = frappe.safe_eval(notif.condition, None, {"doc": opp_doc})
                        print(f"\n    Notification condition check:")
                        print(f"    - Condition: {notif.condition[:80]}...")
                        print(f"    - Result: {result}")
                        if not result:
                            print(f"    - ❌ CONDITION NOT MET - This is why no email!")
                    except Exception as e:
                        print(f"\n    - ❌ Condition error: {e}")
            except:
                pass
    
    print("\n" + "=" * 80)
    print("CHECK COMPLETE")
    print("=" * 80)
    
    print("\n💡 SUMMARY:")
    print("If you see '❌ No emails in queue' for an Opportunity:")
    print("1. Check if 'contact_email' field has a value")
    print("2. Check if notification condition matches")
    print("3. Notification only triggers automatically on specific dates")
    print("\nFor 'Days After' notifications:")
    print("- They run once per day via scheduler")
    print("- They check documents from N days ago")
    print("- Manual trigger tests if notification CAN send, not if it SHOULD")

