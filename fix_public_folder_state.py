#!/usr/bin/env python3
"""
Fix public folder state - sync File documents with physical files
Usage: bench --site SITE_NAME execute fix_public_folder_state.fix_all
"""

import frappe
import os
from pathlib import Path
from frappe.utils import get_site_path

def fix_all():
    """
    Fix all File documents that are out of sync.
    
    Handles the case where we broke things by manually changing file_url:
    - Files stayed in private folder
    - Database says public but file doesn't exist in public folder
    - Need to search private folder for the actual file
    """
    
    print("\n" + "=" * 80)
    print("FIXING PUBLIC FOLDER STATE (SMART FIX)")
    print("=" * 80)
    
    # Get all "public" files
    files = frappe.get_all("File", 
        filters={"is_private": 0, "file_url": ["like", "/files/%"]},
        fields=["name", "file_name", "file_url"]
    )
    
    print(f"\nFound {len(files)} files marked as public")
    
    fixed = 0
    errors = 0
    already_ok = 0
    
    for file_data in files:
        try:
            file_doc = frappe.get_doc("File", file_data.name)
            file_name = file_doc.file_url.split("/")[-1]
            
            private_path = Path(get_site_path("private", "files", file_name))
            public_path = Path(get_site_path("public", "files", file_name))
            
            # Case 1: File already in public and valid
            if public_path.exists():
                size = public_path.stat().st_size
                if size > 0:
                    # File is OK
                    already_ok += 1
                    continue
                else:
                    print(f"\n❌ {file_name}")
                    print(f"   Problem: File is empty (0 bytes) in public folder")
                    # Will try to find in private below
            
            # Case 2: File is in private but marked as public (our bug!)
            if private_path.exists():
                print(f"\n📦 {file_name}")
                print(f"   Problem: In private folder but marked public")
                print(f"   Solution: Moving to public...")
                
                # Ensure public/files exists
                public_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                import shutil
                shutil.move(str(private_path), str(public_path))
                
                # Set permissions
                os.chmod(str(public_path), 0o644)
                
                print(f"   ✅ Fixed")
                fixed += 1
                continue
            
            # Case 3: File with exact name not found - search for it in private folder
            # (Frappe may have added random suffix to filename)
            print(f"\n🔍 {file_name}")
            print(f"   Searching for file in private folder...")
            
            private_dir = Path(get_site_path("private", "files"))
            base_name = file_doc.file_name.rsplit('.', 1)[0] if '.' in file_doc.file_name else file_doc.file_name
            extension = file_doc.file_name.rsplit('.', 1)[1] if '.' in file_doc.file_name else ''
            
            # Search for files with similar name
            found_files = []
            if private_dir.exists():
                pattern = f"{base_name}*"
                if extension:
                    pattern = f"{base_name}*.{extension}"
                found_files = list(private_dir.glob(pattern))
            
            if found_files:
                # Use the first match
                source = found_files[0]
                print(f"   Found: {source.name}")
                print(f"   Moving to public...")
                
                public_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move and rename to expected name
                target = public_path.parent / file_name
                shutil.move(str(source), str(target))
                os.chmod(str(target), 0o644)
                
                print(f"   ✅ Fixed")
                fixed += 1
            else:
                # File truly doesn't exist anywhere
                print(f"   ❌ File not found anywhere")
                print(f"   Action: Deleting File document (file is lost)")
                
                file_doc.delete(ignore_permissions=True)
                errors += 1
                
        except Exception as e:
            print(f"\n❌ Error processing {file_data.name}: {e}")
            import traceback
            traceback.print_exc()
            errors += 1
    
    frappe.db.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ Already OK: {already_ok}")
    print(f"✅ Fixed: {fixed}")
    print(f"❌ Errors/Missing: {errors}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    fix_all()

