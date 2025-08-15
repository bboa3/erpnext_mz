#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to verify ERPNext Mozambique app structure

Run this script to check if all modules can be imported correctly.
"""

import os
import sys

def test_imports():
    """Test if all modules can be imported"""
    
    print("Testing ERPNext Mozambique app imports...")
    
    try:
        # Test main app
        print("✓ Testing main app...")
        import erpnext_mz
        
        # Test modules
        print("✓ Testing accounting module...")
        from erpnext_mz.modules.accounting import chart_of_accounts, vat_templates
        
        print("✓ Testing HR & Payroll module...")
        from erpnext_mz.modules.hr_payroll import inss_irps, benefits_in_kind
        
        print("✓ Testing Tax Compliance module...")
        from erpnext_mz.modules.tax_compliance import saf_t_generator, at_integration
        
        # Test utilities
        print("✓ Testing permissions...")
        from erpnext_mz import permissions
        
        print("✓ Testing overrides...")
        from erpnext_mz import overrides
        
        print("✓ Testing tasks...")
        from erpnext_mz import tasks
        
        print("✓ Testing API...")
        from erpnext_mz.api.v1 import saf_t_export, at_integration
        
        print("✓ Testing setup...")
        from erpnext_mz import setup
        
        print("\n🎉 All imports successful! App structure is correct.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    
    print("\nTesting file structure...")
    
    required_files = [
        "__init__.py",
        "app.json",
        "hooks.py",
        "setup.py",
        "requirements.txt",
        "README.md"
    ]
    
    required_dirs = [
        "modules/",
        "modules/accounting/",
        "modules/hr_payroll/",
        "modules/tax_compliance/",
        "doctypes/",
        "pages/",
        "api/",
        "api/v1/"
    ]
    
    missing_files = []
    missing_dirs = []
    
    # Check files
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✓ {file}")
    
    # Check directories
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
        else:
            print(f"✓ {dir_path}")
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
    
    if missing_dirs:
        print(f"\n❌ Missing directories: {missing_dirs}")
    
    return len(missing_files) == 0 and len(missing_dirs) == 0

if __name__ == "__main__":
    print("ERPNext Mozambique App Structure Test")
    print("=" * 40)
    
    # Test file structure
    structure_ok = test_file_structure()
    
    # Test imports (only if structure is ok)
    if structure_ok:
        imports_ok = test_imports()
        
        if imports_ok:
            print("\n🎯 App is ready for deployment!")
            sys.exit(0)
        else:
            print("\n❌ App has import issues that need fixing.")
            sys.exit(1)
    else:
        print("\n❌ App has structural issues that need fixing.")
        sys.exit(1)
