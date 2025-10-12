#!/usr/bin/env python3
"""
Reset public folder - delete and rebuild from scratch
This is safer than trying to fix corrupted state

Usage: bench --site SITE_NAME console < reset_public_folder.py
"""

import frappe
import os
import shutil
from pathlib import Path
from frappe.utils import get_site_path

def reset_public_folder():
    """
    Reset the public folder to a clean state:
    1. Delete all File documents marked as public
    2. Remove public/files folder
    3. Let users re-upload files
    """
    
    print("\n" + "=" * 80)
    print("RESET PUBLIC FOLDER")
    print("=" * 80)
    
    # Get all "public" files
    files = frappe.get_all("File", 
        filters={"is_private": 0, "file_url": ["like", "/files/%"]},
        fields=["name", "file_name", "file_url", "attached_to_doctype", "attached_to_name"]
    )
    
    print(f"\n⚠️  Found {len(files)} files marked as public")
    print("\nThese will be deleted from the database:")
    
    important_files = []
    
    for f in files:
        print(f"\n  - {f.file_name}")
        print(f"    URL: {f.file_url}")
        if f.attached_to_doctype:
            print(f"    Attached to: {f.attached_to_doctype} - {f.attached_to_name}")
            important_files.append(f)
    
    if important_files:
        print(f"\n⚠️  WARNING: {len(important_files)} files are attached to documents!")
        print("These will need to be re-uploaded:")
        for f in important_files:
            print(f"  - {f.attached_to_doctype}.{f.attached_to_name}: {f.file_name}")
    
    # Ask for confirmation (in interactive mode)
    print("\n" + "=" * 80)
    print("⚠️  THIS WILL:")
    print("1. Delete all File documents marked as public")
    print("2. Remove the public/files folder")
    print("3. Clear company_logo from all companies")
    print("4. You'll need to re-upload files through the UI")
    print("=" * 80)
    
    response = input("\nType 'YES' to continue: ")
    if response != "YES":
        print("❌ Cancelled")
        return
    
    # Step 1: Clear company logos
    print("\n🔄 Clearing company logos...")
    companies = frappe.get_all("Company", 
        filters={"company_logo": ["!=", ""]},
        fields=["name"]
    )
    
    for company_data in companies:
        company = frappe.get_doc("Company", company_data.name)
        if company.company_logo and company.company_logo.startswith("/files/"):
            print(f"  Clearing logo from: {company.name}")
            company.company_logo = None
            company.save(ignore_permissions=True)
    
    frappe.db.commit()
    
    # Step 2: Delete File documents
    print(f"\n🗑️  Deleting {len(files)} File documents...")
    for f in files:
        try:
            file_doc = frappe.get_doc("File", f.name)
            file_doc.delete(ignore_permissions=True)
            print(f"  ✅ Deleted: {f.file_name}")
        except Exception as e:
            print(f"  ❌ Error deleting {f.file_name}: {e}")
    
    frappe.db.commit()
    
    # Step 3: Remove public/files folder
    print("\n🗑️  Removing public/files folder...")
    public_files_dir = Path(get_site_path("public", "files"))
    
    if public_files_dir.exists():
        try:
            shutil.rmtree(str(public_files_dir))
            print(f"  ✅ Removed: {public_files_dir}")
        except Exception as e:
            print(f"  ❌ Error removing folder: {e}")
    else:
        print("  ℹ️  Folder doesn't exist")
    
    print("\n" + "=" * 80)
    print("✅ PUBLIC FOLDER RESET COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Re-upload company logos through UI or onboarding wizard")
    print("2. Run apply_all() to convert logos to public (correctly this time)")
    print("3. Re-upload any other files that were deleted")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    reset_public_folder()

