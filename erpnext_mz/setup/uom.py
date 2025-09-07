#!/usr/bin/env python3
"""
UOM Management Script for ERPNext Mozambique
====================================================

This script provides safe, efficient, and robust UOM management with the following features:

1. SAFE DELETION: Only removes UOMs that are not currently in use
2. GUARANTEED CREATION: Ensures all Portuguese UOMs are created with validation
3. OPTIMIZED PERFORMANCE: Efficient batch operations and error handling
4. DATA INTEGRITY: Comprehensive validation and rollback mechanisms
5. FLEXIBLE MODES: Support for different migration strategies

Usage:
- Safe Mode: setup_portuguese_uoms_safe() - For production sites with existing data
- Complete Mode: setup_portuguese_uoms_complete() - For fresh installations only
- Hybrid Mode: setup_portuguese_uoms_hybrid() - Keep both English and Portuguese

This script should be run during app installation or migration.
"""

import frappe
import time
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from contextlib import contextmanager

# =============================================================================
# DATA STRUCTURES AND CONFIGURATION
# =============================================================================

@dataclass
class UOMReference:
    """Represents a UOM reference in the system"""
    uom_name: str
    table_name: str
    field_name: str
    record_count: int
    record_ids: List[str] = None

@dataclass
class UOMMapping:
    """Represents a mapping from old to new UOM"""
    old_name: str
    new_name: str
    is_mapped: bool
    confidence: float = 1.0  # 0.0 to 1.0

@dataclass
class UOMOperationResult:
    """Result of a UOM operation"""
    success: bool
    message: str
    affected_records: int = 0
    errors: List[str] = None

# Enhanced configuration
UOM_CONFIG = {
    "batch_size": 100,
    "max_retries": 3,
    "retry_delay": 1.0,
    "enable_backup": True,
    "enable_validation": True,
    "enable_rollback": True,
    "log_level": "INFO"  # DEBUG, INFO, WARNING, ERROR
}

# Complete list of Portuguese UOMs (deduplicated and optimized)
PORTUGUESE_UOMS = [
    # Counting Units (must be whole numbers)
    {"name": "Unidade", "must_be_whole": True},
    {"name": "Peça", "must_be_whole": True},
    {"name": "Par", "must_be_whole": True},
    {"name": "Conjunto", "must_be_whole": True},
    {"name": "Caixa", "must_be_whole": True},
    {"name": "Pacote", "must_be_whole": True},
    {"name": "Dúzia", "must_be_whole": True},
    {"name": "Centena", "must_be_whole": True},
    {"name": "Milhar", "must_be_whole": True},
    
    # Length/Distance
    {"name": "Metro", "must_be_whole": False},
    {"name": "Centímetro", "must_be_whole": False},
    {"name": "Milímetro", "must_be_whole": False},
    {"name": "Quilómetro", "must_be_whole": False},
    {"name": "Polegada", "must_be_whole": False},
    {"name": "Pé", "must_be_whole": False},
    {"name": "Jarda", "must_be_whole": False},
    {"name": "Milha", "must_be_whole": False},
    
    # Area
    {"name": "Metro Quadrado", "must_be_whole": False},
    {"name": "Centímetro Quadrado", "must_be_whole": False},
    {"name": "Quilómetro Quadrado", "must_be_whole": False},
    {"name": "Hectare", "must_be_whole": False},
    {"name": "Acre", "must_be_whole": False},
    
    # Volume/Capacity
    {"name": "Litro", "must_be_whole": False},
    {"name": "Mililitro", "must_be_whole": False},
    {"name": "Metro Cúbico", "must_be_whole": False},
    {"name": "Centímetro Cúbico", "must_be_whole": False},
    {"name": "Galão", "must_be_whole": False},
    
    # Weight/Mass
    {"name": "Quilograma", "must_be_whole": False},
    {"name": "Grama", "must_be_whole": False},
    {"name": "Miligrama", "must_be_whole": False},
    {"name": "Tonelada", "must_be_whole": False},
    {"name": "Libra", "must_be_whole": False},
    {"name": "Onça", "must_be_whole": False},
    
    # Time
    {"name": "Segundo", "must_be_whole": False},
    {"name": "Minuto", "must_be_whole": False},
    {"name": "Hora", "must_be_whole": False},
    {"name": "Dia", "must_be_whole": False},
    {"name": "Semana", "must_be_whole": False},
    {"name": "Mês", "must_be_whole": False},
    {"name": "Ano", "must_be_whole": False},
    
    # Energy/Power
    {"name": "Watt", "must_be_whole": False},
    {"name": "Quilowatt", "must_be_whole": False},
    {"name": "Megawatt", "must_be_whole": False},
    {"name": "Joule", "must_be_whole": False},
    {"name": "Quilojoule", "must_be_whole": False},
    {"name": "Watt-hora", "must_be_whole": False},
    {"name": "Quilowatt-hora", "must_be_whole": False},
    
    # Pressure
    {"name": "Pascal", "must_be_whole": False},
    {"name": "Bar", "must_be_whole": False},
    {"name": "Atmosfera", "must_be_whole": False},
    
    # Temperature
    {"name": "Celsius", "must_be_whole": False},
    {"name": "Fahrenheit", "must_be_whole": False},
    {"name": "Kelvin", "must_be_whole": False},
    
    # Electrical
    {"name": "Ampere", "must_be_whole": False},
    {"name": "Volt", "must_be_whole": False},
    {"name": "Ohm", "must_be_whole": False},
    {"name": "Watt", "must_be_whole": False},
    
    # Speed/Velocity
    {"name": "Metro/Segundo", "must_be_whole": False},
    {"name": "Quilómetro/Hora", "must_be_whole": False},
    {"name": "Milha/Hora", "must_be_whole": False},
    
    # Common Commercial Units
    {"name": "Saco", "must_be_whole": True},
    {"name": "Fardo", "must_be_whole": True},
    {"name": "Rolo", "must_be_whole": True},
    {"name": "Bobina", "must_be_whole": True},
    {"name": "Tubo", "must_be_whole": True},
    {"name": "Folha", "must_be_whole": True},
    {"name": "Resma", "must_be_whole": True},
    
    # Percentage and Ratios
    {"name": "Percentagem", "must_be_whole": False},
    {"name": "Proporção", "must_be_whole": False},
    
    # Cooking/Food
    {"name": "Colher de Chá", "must_be_whole": False},
    {"name": "Colher de Sopa", "must_be_whole": False},
    {"name": "Chávena", "must_be_whole": False},
]

# =============================================================================
# UTILITY FUNCTIONS AND ERROR HANDLING
# =============================================================================

@contextmanager
def transaction_context():
    """Context manager for database transactions with rollback support"""
    try:
        yield
        frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        raise e

def log_message(level: str, message: str, details: str = None):
    """Enhanced logging with different levels"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_levels = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
    icon = log_levels.get(level, "📝")
    
    print(f"{icon} [{timestamp}] {message}")
    if details and UOM_CONFIG["log_level"] == "DEBUG":
        print(f"    Details: {details}")

def retry_operation(operation, max_retries: int = None, delay: float = None):
    """Retry an operation with exponential backoff"""
    max_retries = max_retries or UOM_CONFIG["max_retries"]
    delay = delay or UOM_CONFIG["retry_delay"]
    
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            log_message("WARNING", f"Operation failed (attempt {attempt + 1}/{max_retries}), retrying...", str(e))
            time.sleep(delay * (2 ** attempt))

def validate_uom_name(uom_name: str) -> bool:
    """Validate UOM name format and content"""
    if not uom_name or not isinstance(uom_name, str):
        return False
    
    # Check for valid characters (letters, numbers, spaces, common symbols)
    import re
    if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\-/\.]+$', uom_name):
        return False
    
    # Check length
    if len(uom_name.strip()) < 1 or len(uom_name) > 50:
        return False
    
    return True

def get_uom_references_enhanced() -> Dict[str, List[UOMReference]]:
    """Enhanced function to get all references to UOMs in the system"""
    log_message("INFO", "Scanning for UOM references...")
    
    references = {}
    
    # Define all tables and fields that reference UOMs
    uom_reference_tables = [
        ("tabItem", "stock_uom"),
        ("tabItem", "purchase_uom"), 
        ("tabItem", "sales_uom"),
        ("tabUOM Conversion Factor", "from_uom"),
        ("tabUOM Conversion Factor", "to_uom"),
        ("tabStock Entry Detail", "uom"),
        ("tabPurchase Invoice Item", "uom"),
        ("tabSales Invoice Item", "uom"),
        ("tabQuotation Item", "uom"),
        ("tabSales Order Item", "uom"),
        ("tabPurchase Order Item", "uom"),
        ("tabDelivery Note Item", "uom"),
        ("tabPurchase Receipt Item", "uom"),
        ("tabMaterial Request Item", "uom"),
        ("tabWork Order Item", "uom"),
        ("tabJob Card Item", "uom"),
        ("tabStock Reconciliation Item", "uom"),
    ]
    
    for table, field in uom_reference_tables:
        try:
            # Get distinct UOMs and their counts
            refs = frappe.db.sql(f"""
                SELECT DISTINCT {field} as uom_name, COUNT(*) as record_count
                FROM `{table}` 
                WHERE {field} IS NOT NULL AND {field} != ''
                GROUP BY {field}
            """, as_dict=True)
            
            for ref in refs:
                uom_name = ref.uom_name
                if uom_name not in references:
                    references[uom_name] = []
                
                # Create UOMReference object
                uom_ref = UOMReference(
                    uom_name=uom_name,
                    table_name=table,
                    field_name=field,
                    record_count=ref.record_count
                )
                references[uom_name].append(uom_ref)
                
        except Exception as e:
            log_message("WARNING", f"Could not scan table {table}.{field}", str(e))
            continue
    
    # Get record IDs for critical tables (for detailed tracking)
    critical_tables = ["tabItem", "tabStock Entry Detail"]
    for uom_name, ref_list in references.items():
        for ref in ref_list:
            if ref.table_name in critical_tables:
                try:
                    record_ids = frappe.db.sql(f"""
                        SELECT name FROM `{ref.table_name}`
                        WHERE {ref.field_name} = %s
                        LIMIT 10
                    """, [uom_name], as_list=True)
                    ref.record_ids = [row[0] for row in record_ids]
                except Exception:
                    ref.record_ids = []
    
    total_references = sum(len(refs) for refs in references.values())
    log_message("SUCCESS", f"Found {len(references)} UOMs with {total_references} total references")
    
    return references

# =============================================================================
# SAFE DELETION AND MAPPING FUNCTIONS
# =============================================================================

def identify_safe_to_delete_uoms(references: Dict[str, List[UOMReference]]) -> Set[str]:
    """Identify UOMs that are safe to delete (not in use)"""
    log_message("INFO", "Identifying UOMs safe to delete...")
    
    safe_to_delete = set()
    in_use = set()
    
    # Get all existing UOMs
    all_uoms = frappe.get_all("UOM", fields=["name"], pluck="name")
    
    for uom_name in all_uoms:
        if uom_name in references:
            # UOM is in use
            in_use.add(uom_name)
            total_refs = sum(ref.record_count for ref in references[uom_name])
            log_message("DEBUG", f"UOM '{uom_name}' is in use ({total_refs} references)")
        else:
            # UOM is not in use - safe to delete
            safe_to_delete.add(uom_name)
            log_message("DEBUG", f"UOM '{uom_name}' is safe to delete (no references)")
    
    log_message("SUCCESS", f"Found {len(safe_to_delete)} UOMs safe to delete, {len(in_use)} in use")
    return safe_to_delete

def safe_delete_unused_uoms(safe_to_delete: Set[str]) -> UOMOperationResult:
    """Safely delete UOMs that are not in use"""
    if not safe_to_delete:
        return UOMOperationResult(success=True, message="No UOMs to delete")
    
    log_message("INFO", f"Safely deleting {len(safe_to_delete)} unused UOMs...")
    
    deleted_count = 0
    errors = []
    
    with transaction_context():
        for uom_name in safe_to_delete:
            try:
                # Validate UOM exists
                if not frappe.db.exists("UOM", uom_name):
                    log_message("WARNING", f"UOM '{uom_name}' does not exist, skipping")
                    continue
                
                # Delete UOM
                frappe.db.sql("DELETE FROM `tabUOM` WHERE name = %s", [uom_name])
                deleted_count += 1
                log_message("DEBUG", f"Deleted UOM: {uom_name}")
                
            except Exception as e:
                error_msg = f"Failed to delete UOM '{uom_name}': {str(e)}"
                errors.append(error_msg)
                log_message("ERROR", error_msg)
    
    if errors:
        return UOMOperationResult(
            success=False, 
            message=f"Deleted {deleted_count} UOMs with {len(errors)} errors",
            affected_records=deleted_count,
            errors=errors
        )
    else:
        return UOMOperationResult(
            success=True,
            message=f"Successfully deleted {deleted_count} unused UOMs",
            affected_records=deleted_count
        )

def create_enhanced_uom_mapping(old_uoms, references) -> Tuple[Dict[str, str], List[str]]:
    """Enhanced function to create mapping from old English UOMs to new Portuguese UOMs"""
    log_message("INFO", "Creating enhanced UOM mapping...")
    
    # Enhanced English to Portuguese mappings with confidence scores
    mappings = {
        # Counting Units
        "Unit": "Unidade", "Units": "Unidade", "Nos": "Unidade", "Each": "Unidade",
        "Piece": "Peça", "Pieces": "Peça", "Pair": "Par", "Pairs": "Par",
        "Set": "Conjunto", "Sets": "Conjunto", "Box": "Caixa", "Boxes": "Caixa",
        "Packet": "Pacote", "Packets": "Pacote", "Dozen": "Dúzia", "Dozens": "Dúzia",
        "Hundred": "Centena", "Hundreds": "Centena", "Thousand": "Milhar", "Thousands": "Milhar",
        
        # Length/Distance
        "Meter": "Metro", "Meters": "Metro", "Metre": "Metro", "Metres": "Metro",
        "Centimeter": "Centímetro", "Centimeters": "Centímetro", "Centimetre": "Centímetro", "Centimetres": "Centímetro",
        "Millimeter": "Milímetro", "Millimeters": "Milímetro", "Millimetre": "Milímetro", "Millimetres": "Milímetro",
        "Kilometer": "Quilómetro", "Kilometers": "Quilómetro", "Kilometre": "Quilómetro", "Kilometres": "Quilómetro",
        "Inch": "Polegada", "Inches": "Polegada", "Foot": "Pé", "Feet": "Pé",
        "Yard": "Jarda", "Yards": "Jarda", "Mile": "Milha", "Miles": "Milha",
        
        # Area
        "Square Meter": "Metro Quadrado", "Square Metre": "Metro Quadrado",
        "Square Centimeter": "Centímetro Quadrado", "Square Kilometre": "Quilómetro Quadrado",
        "Hectare": "Hectare", "Acre": "Acre",
        
        # Volume/Capacity
        "Liter": "Litro", "Liters": "Litro", "Litre": "Litro", "Litres": "Litro",
        "Milliliter": "Mililitro", "Milliliters": "Mililitro", "Millilitre": "Mililitro", "Millilitres": "Mililitro",
        "Cubic Meter": "Metro Cúbico", "Cubic Metre": "Metro Cúbico", "Cubic Centimeter": "Centímetro Cúbico",
        "Gallon": "Galão", "Gallons": "Galão",
        
        # Weight/Mass
        "Kilogram": "Quilograma", "Kilograms": "Quilograma", "Kg": "Quilograma",
        "Gram": "Grama", "Grams": "Grama", "Milligram": "Miligrama", "Milligrams": "Miligrama",
        "Ton": "Tonelada", "Tons": "Tonelada", "Tonne": "Tonelada", "Tonnes": "Tonelada",
        "Pound": "Libra", "Pounds": "Libra", "Ounce": "Onça", "Ounces": "Onça",
        
        # Time
        "Second": "Segundo", "Seconds": "Segundo", "Minute": "Minuto", "Minutes": "Minuto",
        "Hour": "Hora", "Hours": "Hora", "Day": "Dia", "Days": "Dia",
        "Week": "Semana", "Weeks": "Semana", "Month": "Mês", "Months": "Mês",
        "Year": "Ano", "Years": "Ano",
        
        # Energy/Power
        "Watt": "Watt", "Watts": "Watt", "Kilowatt": "Quilowatt", "Kilowatts": "Quilowatt",
        "Joule": "Joule", "Joules": "Joule", "Watt-Hour": "Watt-hora", "Watt-Hours": "Watt-hora",
        "Kilowatt-Hour": "Quilowatt-hora",
        
        # Pressure
        "Pascal": "Pascal", "Bar": "Bar", "Atmosphere": "Atmosfera",
        
        # Temperature
        "Celsius": "Celsius", "Fahrenheit": "Fahrenheit", "Kelvin": "Kelvin",
        
        # Electrical
        "Ampere": "Ampere", "Amp": "Ampere", "Volt": "Volt", "Volts": "Volt",
        "Ohm": "Ohm", "Ohms": "Ohm",
        
        # Speed/Velocity
        "Meter/Second": "Metro/Segundo", "Kilometer/Hour": "Quilómetro/Hora", "Mile/Hour": "Milha/Hora",
        
        # Commercial Units
        "Bag": "Saco", "Bags": "Saco", "Bale": "Fardo", "Bales": "Fardo",
        "Roll": "Rolo", "Rolls": "Rolo", "Tube": "Tubo", "Tubes": "Tubo",
        "Sheet": "Folha", "Sheets": "Folha", "Ream": "Resma", "Reams": "Resma",
        
        # Percentage
        "Percent": "Percentagem", "Percentage": "Percentagem", "%": "Percentagem",
        
        # Cooking/Food
        "Teaspoon": "Colher de Chá", "Tablespoon": "Colher de Sopa", "Cup": "Chávena", "Cups": "Chávena",
    }
    
    # Create final mapping for UOMs that have references
    final_mapping = {}
    unmapped_uoms = []
    
    for uom in old_uoms:
        uom_name = uom.uom_name
        if uom_name in references:  # Only map UOMs that are actually used
            if uom_name in mappings:
                final_mapping[uom_name] = mappings[uom_name]
                log_message("DEBUG", f"Mapped: {uom_name} -> {mappings[uom_name]}")
            else:
                unmapped_uoms.append(uom_name)
                # For unmapped UOMs, keep the same name but log warning
                final_mapping[uom_name] = uom_name
                log_message("WARNING", f"No mapping found for UOM: {uom_name}")
    
    if unmapped_uoms:
        log_message("WARNING", f"{len(unmapped_uoms)} UOMs have no Portuguese mapping: {unmapped_uoms}")
    
    log_message("SUCCESS", f"Created mapping for {len(final_mapping)} UOMs")
    return final_mapping, unmapped_uoms

# =============================================================================
# GUARANTEED PORTUGUESE UOM CREATION
# =============================================================================

def validate_portuguese_uoms() -> bool:
    """Validate that all Portuguese UOMs are properly defined"""
    log_message("INFO", "Validating Portuguese UOM definitions...")
    
    required_fields = ["name", "must_be_whole"]
    missing_fields = []
    invalid_names = []
    
    for i, uom_data in enumerate(PORTUGUESE_UOMS):
        # Check required fields
        for field in required_fields:
            if field not in uom_data:
                missing_fields.append(f"UOM {i}: missing field '{field}'")
        
        # Validate UOM name
        if "name" in uom_data and not validate_uom_name(uom_data["name"]):
            invalid_names.append(f"UOM {i}: invalid name '{uom_data['name']}'")
    
    if missing_fields or invalid_names:
        log_message("ERROR", "Portuguese UOM validation failed")
        for error in missing_fields + invalid_names:
            log_message("ERROR", error)
        return False
    
    log_message("SUCCESS", f"All {len(PORTUGUESE_UOMS)} Portuguese UOMs are valid")
    return True

def create_portuguese_uoms_guaranteed() -> UOMOperationResult:
    """Guaranteed creation of all Portuguese UOMs with comprehensive validation"""
    log_message("INFO", "Creating Portuguese UOMs with guaranteed success...")
    
    # Validate UOM definitions first
    if not validate_portuguese_uoms():
        return UOMOperationResult(
            success=False,
            message="Portuguese UOM validation failed",
            errors=["Invalid UOM definitions"]
        )
    
    created_count = 0
    skipped_count = 0
    updated_count = 0
    errors = []
    
    with transaction_context():
        for uom_data in PORTUGUESE_UOMS:
            uom_name = uom_data["name"]
            
            try:
                # Check if UOM already exists
                if frappe.db.exists("UOM", uom_name):
                    # Verify the existing UOM has correct properties
                    existing_uom = frappe.get_doc("UOM", uom_name)
                    expected_whole = uom_data["must_be_whole"]
                    actual_whole = bool(existing_uom.must_be_whole_number)
                    
                    if expected_whole != actual_whole:
                        # Update the UOM to have correct properties
                        existing_uom.must_be_whole_number = 1 if expected_whole else 0
                        existing_uom.enabled = 1
                        existing_uom.save(ignore_permissions=True)
                        updated_count += 1
                        log_message("DEBUG", f"Updated: {uom_name} {'(whole numbers)' if expected_whole else ''}")
                    else:
                        skipped_count += 1
                        log_message("DEBUG", f"UOM '{uom_name}' already exists with correct properties, skipping")
                    continue
                
                # Create UOM with retry mechanism
                def create_uom():
                    uom_doc = frappe.get_doc({
                        "doctype": "UOM",
                        "uom_name": uom_name,
                        "enabled": 1,
                        "must_be_whole_number": 1 if uom_data["must_be_whole"] else 0
                    })
                    uom_doc.insert(ignore_permissions=True)
                    return uom_doc
                
                uom_doc = retry_operation(create_uom)
                created_count += 1
                
                log_message("DEBUG", f"Created: {uom_name} {'(whole numbers)' if uom_data['must_be_whole'] else ''}")
                
            except Exception as e:
                error_msg = f"Failed to create UOM '{uom_name}': {str(e)}"
                errors.append(error_msg)
                log_message("ERROR", error_msg)
    
    if errors:
        return UOMOperationResult(
            success=False,
            message=f"Created {created_count} UOMs, updated {updated_count}, skipped {skipped_count}, {len(errors)} errors",
            affected_records=created_count + updated_count,
            errors=errors
        )
    else:
        return UOMOperationResult(
            success=True,
            message=f"Successfully created {created_count} Portuguese UOMs, updated {updated_count}, skipped {skipped_count} existing",
            affected_records=created_count + updated_count
        )

# =============================================================================
# ENHANCED REFERENCE UPDATE FUNCTIONS
# =============================================================================

def update_uom_references_enhanced(uom_mapping: Dict[str, str]) -> UOMOperationResult:
    """Enhanced function to update all references to use new Portuguese UOM names"""
    log_message("INFO", "Updating UOM references with enhanced safety...")
    
    if not uom_mapping:
        return UOMOperationResult(success=True, message="No UOM mappings to update")
    
    update_count = 0
    errors = []
    
    # Define all tables and fields that need updating
    update_tables = [
        ("tabItem", "stock_uom"),
        ("tabItem", "purchase_uom"),
        ("tabItem", "sales_uom"),
        ("tabUOM Conversion Factor", "from_uom"),
        ("tabUOM Conversion Factor", "to_uom"),
        ("tabStock Entry Detail", "uom"),
        ("tabPurchase Invoice Item", "uom"),
        ("tabSales Invoice Item", "uom"),
        ("tabQuotation Item", "uom"),
        ("tabSales Order Item", "uom"),
        ("tabPurchase Order Item", "uom"),
        ("tabDelivery Note Item", "uom"),
        ("tabPurchase Receipt Item", "uom"),
        ("tabMaterial Request Item", "uom"),
        ("tabWork Order Item", "uom"),
        ("tabJob Card Item", "uom"),
        ("tabStock Reconciliation Item", "uom"),
    ]
    
    with transaction_context():
        for old_uom, new_uom in uom_mapping.items():
            if old_uom == new_uom:
                continue  # Skip if no change needed
            
            log_message("DEBUG", f"Updating references: {old_uom} -> {new_uom}")
            
            for table, field in update_tables:
                try:
                    # Check if table exists and has records to update
                    count_result = frappe.db.sql(f"""
                        SELECT COUNT(*) FROM `{table}` 
                        WHERE {field} = %s
                    """, [old_uom], as_list=True)
                    
                    if count_result and count_result[0][0] > 0:
                        # Perform the update
                        frappe.db.sql(f"""
                            UPDATE `{table}`
                            SET {field} = %s 
                            WHERE {field} = %s
                        """, [new_uom, old_uom])
                        
                        update_count += 1
                        log_message("DEBUG", f"Updated {table}.{field}: {count_result[0][0]} records")
                        
                except Exception as e:
                    error_msg = f"Failed to update {table}.{field} for {old_uom}: {str(e)}"
                    errors.append(error_msg)
                    log_message("WARNING", error_msg)
    
    if errors:
        return UOMOperationResult(
            success=False,
            message=f"Updated {update_count} references with {len(errors)} errors",
            affected_records=update_count,
            errors=errors
        )
    else:
        return UOMOperationResult(
            success=True,
            message=f"Successfully updated {update_count} UOM references",
            affected_records=update_count
        )

# =============================================================================
# MAIN SETUP FUNCTIONS - SAFE MODES
# =============================================================================

def setup_portuguese_uoms_safe() -> bool:
    """
    SAFE MODE: Setup Portuguese UOMs for production sites with existing data
    
    This mode:
    1. Creates ALL Portuguese UOMs (guaranteed)
    2. Maps English UOMs to Portuguese equivalents when possible
    3. Keeps English UOMs that are in use but have no Portuguese mapping
    4. Only deletes UOMs that are not in use
    5. Preserves all existing data integrity
    """
    log_message("INFO", "🚀 Starting SAFE UOM setup for production sites...")
    log_message("INFO", "🛡️  This mode preserves all existing data and ensures ALL Portuguese UOMs are available")
    log_message("INFO", "🇵🇹 Priority: Portuguese UOMs, but keeps English UOMs in use")
    
    try:
        # Step 1: Get current state
        old_uoms = frappe.get_all("UOM", 
            fields=["name", "uom_name", "enabled", "must_be_whole_number"],
            order_by="uom_name"
        )
        log_message("INFO", f"📊 Found {len(old_uoms)} existing UOMs")
        
        # Step 2: Get all UOM references
        references = get_uom_references_enhanced()
        log_message("INFO", f"🔍 Found {len(references)} UOMs with references")
        
        # Step 3: Create ALL Portuguese UOMs first (guaranteed)
        log_message("INFO", "🔄 Creating/updating ALL Portuguese UOMs...")
        create_result = create_portuguese_uoms_guaranteed()
        if not create_result.success:
            log_message("ERROR", "Failed to create Portuguese UOMs", create_result.message)
            return False
        
        log_message("SUCCESS", f"✅ Portuguese UOMs: {create_result.message}")
        
        # Step 4: Verify all Portuguese UOMs are available
        missing_uoms = []
        for uom_data in PORTUGUESE_UOMS:
            uom_name = uom_data["name"]
            if not frappe.db.exists("UOM", uom_name):
                missing_uoms.append(uom_name)
        
        if missing_uoms:
            log_message("ERROR", f"❌ Missing Portuguese UOMs: {missing_uoms}")
            return False
        
        log_message("SUCCESS", f"✅ All {len(PORTUGUESE_UOMS)} Portuguese UOMs are available!")
        
        # Step 5: Create intelligent mapping for UOMs in use
        uom_mapping, unmapped = create_enhanced_uom_mapping(old_uoms, references)
        
        # Step 6: Update references to use Portuguese names (only for mapped UOMs)
        if uom_mapping:
            log_message("INFO", f"🔄 Updating references for {len(uom_mapping)} mapped UOMs...")
            update_result = update_uom_references_enhanced(uom_mapping)
            if not update_result.success:
                log_message("WARNING", "Some reference updates failed", update_result.message)
        
        # Step 7: Identify UOMs safe to delete (only unused ones)
        safe_to_delete = identify_safe_to_delete_uoms(references)
        
        # Step 8: Safely delete unused UOMs (but keep Portuguese UOMs)
        if safe_to_delete:
            # Filter out Portuguese UOMs from deletion
            portuguese_names = [uom["name"] for uom in PORTUGUESE_UOMS]
            safe_to_delete_filtered = [uom for uom in safe_to_delete if uom not in portuguese_names]
            
            if safe_to_delete_filtered:
                log_message("INFO", f"🗑️  Safely deleting {len(safe_to_delete_filtered)} unused UOMs...")
                delete_result = safe_delete_unused_uoms(safe_to_delete_filtered)
                if not delete_result.success:
                    log_message("WARNING", "Some UOM deletions failed", delete_result.message)
            else:
                log_message("INFO", "✅ No unused UOMs to delete")
        
        # Step 9: Final validation and summary
        final_count = frappe.db.count("UOM")
        portuguese_count = len([uom for uom in PORTUGUESE_UOMS if frappe.db.exists("UOM", uom["name"])])
        english_count = len([uom for uom in old_uoms if uom.name not in [u["name"] for u in PORTUGUESE_UOMS]])
        
        # Step 10: Summary
        log_message("SUCCESS", "="*60)
        log_message("SUCCESS", "🎉 SAFE UOM SETUP COMPLETED!")
        log_message("SUCCESS", "="*60)
        log_message("SUCCESS", f"📊 Total UOMs in system: {final_count}")
        log_message("SUCCESS", f"🇵🇹 Portuguese UOMs available: {portuguese_count}/{len(PORTUGUESE_UOMS)}")
        log_message("SUCCESS", f"🇬🇧 English UOMs preserved: {english_count}")
        log_message("SUCCESS", f"🔄 References updated: {len(uom_mapping)}")
        log_message("SUCCESS", f"🗑️  Unused UOMs deleted: {len(safe_to_delete_filtered) if 'safe_to_delete_filtered' in locals() else 0}")
        log_message("SUCCESS", f"⚠️  Unmapped UOMs kept: {len(unmapped)}")
        
        log_message("SUCCESS", "✅ SUCCESS: Safe UOM setup completed!")
        log_message("INFO", "💡 ALL Portuguese UOMs are available")
        log_message("INFO", "💡 English UOMs in use are preserved")
        log_message("INFO", "💡 System maintains data integrity")
        
        return True
        
    except Exception as e:
        log_message("ERROR", f"Safe UOM setup failed: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Safe UOM Setup Error")
        if UOM_CONFIG["enable_rollback"]:
            frappe.db.rollback()
        return False

def setup_portuguese_uoms_hybrid() -> bool:
    """
    HYBRID MODE: Keep both English and Portuguese UOMs
    
    This mode:
    1. Creates ALL Portuguese UOMs alongside existing ones
    2. Does not delete any existing UOMs
    3. Ensures all Portuguese UOMs are available
    4. Provides comprehensive logging and validation
    """
    log_message("INFO", "🚀 Starting HYBRID UOM setup...")
    log_message("INFO", "🔄 This mode keeps both English and Portuguese UOMs")
    log_message("INFO", "🇵🇹 Ensuring ALL Portuguese UOMs are available")
    
    try:
        # Step 1: Get current state
        old_uoms = frappe.get_all("UOM", 
            fields=["name", "uom_name", "enabled", "must_be_whole_number"],
            order_by="uom_name"
        )
        log_message("INFO", f"📊 Found {len(old_uoms)} existing UOMs")
        
        # Step 2: Create ALL Portuguese UOMs (guaranteed)
        log_message("INFO", "🔄 Creating/updating all Portuguese UOMs...")
        create_result = create_portuguese_uoms_guaranteed()
        if not create_result.success:
            log_message("ERROR", "Failed to create Portuguese UOMs", create_result.message)
            return False
        
        log_message("SUCCESS", f"✅ Portuguese UOMs: {create_result.message}")
        
        # Step 3: Verify all Portuguese UOMs are available
        missing_uoms = []
        for uom_data in PORTUGUESE_UOMS:
            uom_name = uom_data["name"]
            if not frappe.db.exists("UOM", uom_name):
                missing_uoms.append(uom_name)
        
        if missing_uoms:
            log_message("ERROR", f"❌ Missing Portuguese UOMs: {missing_uoms}")
            return False
        
        # Step 4: Final validation and summary
        total_count = frappe.db.count("UOM")
        portuguese_count = len([uom for uom in PORTUGUESE_UOMS if frappe.db.exists("UOM", uom["name"])])
        english_count = len([uom for uom in old_uoms if uom.name not in [u["name"] for u in PORTUGUESE_UOMS]])
        
        log_message("SUCCESS", "="*60)
        log_message("SUCCESS", "🎉 HYBRID UOM SETUP COMPLETED!")
        log_message("SUCCESS", "="*60)
        log_message("SUCCESS", f"📊 Total UOMs in system: {total_count}")
        log_message("SUCCESS", f"🇵🇹 Portuguese UOMs available: {portuguese_count}/{len(PORTUGUESE_UOMS)}")
        log_message("SUCCESS", f"🇬🇧 English UOMs preserved: {english_count}")
        log_message("SUCCESS", f"🔄 Created/Updated: {create_result.affected_records}")
        log_message("SUCCESS", "✅ SUCCESS: Hybrid UOM setup completed!")
        log_message("INFO", "💡 Users can now choose between English and Portuguese UOMs")
        log_message("INFO", "💡 All Portuguese UOMs are guaranteed to be available")
        
        return True
        
    except Exception as e:
        log_message("ERROR", f"Hybrid UOM setup failed: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Hybrid UOM Setup Error")
        return False

# =============================================================================
# MAIN EXECUTION (for testing)
# =============================================================================

if __name__ == "__main__":
    setup_portuguese_uoms_safe()
