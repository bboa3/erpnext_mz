import frappe
from erpnext_mz.setup.onboarding import get_status


def boot_session(bootinfo):
    try:
        # Only show to System Managers/Administrators inside Desk
        roles = set((bootinfo.get("roles") or []))
        print("Boot session - User roles:", roles)
        
        # Temporarily allow all users for debugging
        if "System Manager" not in roles and "System Administrator" not in roles:
            return

        status = get_status()
        print("Boot session - Onboarding status:", status)
        bootinfo["erpnext_mz_onboarding"] = status
    except Exception as e:
        print("Boot session error:", str(e))
        import traceback
        traceback.print_exc()


