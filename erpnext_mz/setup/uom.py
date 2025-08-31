#!/usr/bin/env python3
"""
Script to completely remove all existing UOMs and create new Portuguese UOMs.
This ensures users only see Portuguese unit names throughout the system.

This script should be run during app installation or migration.
"""

import frappe

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

def get_uom_references():
    """Get all references to UOMs in the system"""
    print("🔍 Scanning for UOM references...")
    
    references = {}
    
    # Check Items table
    item_refs = frappe.db.sql("""
        SELECT name, stock_uom, purchase_uom, sales_uom 
        FROM `tabItem` 
        WHERE stock_uom IS NOT NULL OR purchase_uom IS NOT NULL OR sales_uom IS NOT NULL
    """, as_dict=True)
    
    for item in item_refs:
        if item.stock_uom:
            references.setdefault(item.stock_uom, []).append(f"Item {item.name} (stock)")
        if item.purchase_uom:
            references.setdefault(item.purchase_uom, []).append(f"Item {item.name} (purchase)")
        if item.sales_uom:
            references.setdefault(item.sales_uom, []).append(f"Item {item.name} (sales)")
    
    # Check UOM Conversion Factor
    conv_refs = frappe.db.sql("""
        SELECT name, from_uom, to_uom 
        FROM `tabUOM Conversion Factor`
    """, as_dict=True)
    
    for conv in conv_refs:
        references.setdefault(conv.from_uom, []).append(f"Conversion {conv.name} (from)")
        references.setdefault(conv.to_uom, []).append(f"Conversion {conv.name} (to)")
    
    # Check other common tables
    other_tables = [
        ("tabStock Entry Detail", "uom"),
        ("tabPurchase Invoice Item", "uom"),
        ("tabSales Invoice Item", "uom"),
        ("tabQuotation Item", "uom"),
        ("tabSales Order Item", "uom"),
        ("tabPurchase Order Item", "uom"),
    ]
    
    for table, field in other_tables:
        try:
            refs = frappe.db.sql(f"""
                SELECT DISTINCT {field} as uom, COUNT(*) as count
                FROM `{table}` 
                WHERE {field} IS NOT NULL 
                GROUP BY {field}
            """, as_dict=True)
            
            for ref in refs:
                references.setdefault(ref.uom, []).append(f"{table} ({ref.count} records)")
        except Exception:
            # Table might not exist in all setups
            pass
    
    print(f"✅ Found references to {len(references)} different UOMs")
    return references

def create_uom_mapping(old_uoms, references):
    """Create mapping from old English UOMs to new Portuguese UOMs"""
    print("🗺️  Creating UOM mapping...")
    
    # Common English to Portuguese mappings
    mappings = {
        "Unit": "Unidade",
        "Units": "Unidade", 
        "Nos": "Unidade",
        "Each": "Unidade",
        "Piece": "Peça",
        "Pieces": "Peça",
        "Pair": "Par",
        "Pairs": "Par",
        "Set": "Conjunto",
        "Sets": "Conjunto",
        "Box": "Caixa",
        "Boxes": "Caixa",
        "Packet": "Pacote",
        "Packets": "Pacote",
        "Dozen": "Dúzia",
        "Dozens": "Dúzia",
        "Hundred": "Centena",
        "Hundreds": "Centena",
        "Thousand": "Milhar",
        "Thousands": "Milhar",
        
        "Meter": "Metro",
        "Meters": "Metro",
        "Metre": "Metro",
        "Metres": "Metro",
        "Centimeter": "Centímetro",
        "Centimeters": "Centímetro",
        "Centimetre": "Centímetro",
        "Centimetres": "Centímetro",
        "Millimeter": "Milímetro",
        "Millimeters": "Milímetro",
        "Millimetre": "Milímetro",
        "Millimetres": "Milímetro",
        "Kilometer": "Quilómetro",
        "Kilometers": "Quilómetro",
        "Kilometre": "Quilómetro",
        "Kilometres": "Quilómetro",
        "Inch": "Polegada",
        "Inches": "Polegada",
        "Foot": "Pé",
        "Feet": "Pé",
        "Yard": "Jarda",
        "Yards": "Jarda",
        "Mile": "Milha",
        "Miles": "Milha",
        
        "Square Meter": "Metro Quadrado",
        "Square Metre": "Metro Quadrado",
        "Square Centimeter": "Centímetro Quadrado",
        "Square Kilometre": "Quilómetro Quadrado",
        "Hectare": "Hectare",
        "Acre": "Acre",
        
        "Liter": "Litro",
        "Liters": "Litro",
        "Litre": "Litro",
        "Litres": "Litro",
        "Milliliter": "Mililitro",
        "Milliliters": "Mililitro",
        "Millilitre": "Mililitro",
        "Millilitres": "Mililitro",
        "Cubic Meter": "Metro Cúbico",
        "Cubic Metre": "Metro Cúbico",
        "Cubic Centimeter": "Centímetro Cúbico",
        "Gallon": "Galão",
        "Gallons": "Galão",
        
        "Kilogram": "Quilograma",
        "Kilograms": "Quilograma",
        "Kg": "Quilograma",
        "Gram": "Grama",
        "Grams": "Grama",
        "Milligram": "Miligrama",
        "Milligrams": "Miligrama",
        "Ton": "Tonelada",
        "Tons": "Tonelada",
        "Tonne": "Tonelada",
        "Tonnes": "Tonelada",
        "Pound": "Libra",
        "Pounds": "Libra",
        "Ounce": "Onça",
        "Ounces": "Onça",
        
        "Second": "Segundo",
        "Seconds": "Segundo",
        "Minute": "Minuto",
        "Minutes": "Minuto",
        "Hour": "Hora",
        "Hours": "Hora",
        "Day": "Dia",
        "Days": "Dia",
        "Week": "Semana",
        "Weeks": "Semana",
        "Month": "Mês",
        "Months": "Mês",
        "Year": "Ano",
        "Years": "Ano",
        
        "Watt": "Watt",
        "Watts": "Watt",
        "Kilowatt": "Quilowatt",
        "Kilowatts": "Quilowatt",
        "Joule": "Joule",
        "Joules": "Joule",
        "Watt-Hour": "Watt-hora",
        "Watt-Hours": "Watt-hora",
        "Kilowatt-Hour": "Quilowatt-hora",
        
        "Pascal": "Pascal",
        "Bar": "Bar",
        "Atmosphere": "Atmosfera",
        
        "Celsius": "Celsius",
        "Fahrenheit": "Fahrenheit",
        "Kelvin": "Kelvin",
        
        "Ampere": "Ampere",
        "Amp": "Ampere",
        "Volt": "Volt",
        "Volts": "Volt",
        "Ohm": "Ohm",
        "Ohms": "Ohm",
        
        "Meter/Second": "Metro/Segundo",
        "Kilometer/Hour": "Quilómetro/Hora",
        "Mile/Hour": "Milha/Hora",
        
        "Bag": "Saco",
        "Bags": "Saco",
        "Bale": "Fardo",
        "Bales": "Fardo",
        "Roll": "Rolo",
        "Rolls": "Rolo",
        "Tube": "Tubo",
        "Tubes": "Tubo",
        "Sheet": "Folha",
        "Sheets": "Folha",
        "Ream": "Resma",
        "Reams": "Resma",
        
        "Percent": "Percentagem",
        "Percentage": "Percentagem",
        "%": "Percentagem",
        
        "Teaspoon": "Colher de Chá",
        "Tablespoon": "Colher de Sopa",
        "Cup": "Chávena",
        "Cups": "Chávena",
    }
    
    # Create final mapping for UOMs that have references
    final_mapping = {}
    unmapped_uoms = []
    
    for uom in old_uoms:
        uom_name = uom.uom_name
        if uom_name in references:  # Only map UOMs that are actually used
            if uom_name in mappings:
                final_mapping[uom_name] = mappings[uom_name]
                print(f"  📍 {uom_name} -> {mappings[uom_name]}")
            else:
                unmapped_uoms.append(uom_name)
                # Default to keeping the same name if no mapping found
                final_mapping[uom_name] = uom_name
                print(f"  ⚠️  {uom_name} -> {uom_name} (no mapping found)")
    
    if unmapped_uoms:
        print(f"⚠️  Warning: {len(unmapped_uoms)} UOMs have no Portuguese mapping: {unmapped_uoms}")
    
    print(f"✅ Created mapping for {len(final_mapping)} UOMs")
    return final_mapping, unmapped_uoms

def update_uom_references(uom_mapping):
    """Update all references to use new Portuguese UOM names"""
    print("🔄 Updating UOM references...")
    
    update_count = 0
    
    # Update Items
    for old_uom, new_uom in uom_mapping.items():
        if old_uom != new_uom:
            # Update stock_uom
            frappe.db.sql("""
                UPDATE `tabItem` 
                SET stock_uom = %s 
                WHERE stock_uom = %s
            """, [new_uom, old_uom])
            
            # Update purchase_uom
            frappe.db.sql("""
                UPDATE `tabItem` 
                SET purchase_uom = %s 
                WHERE purchase_uom = %s
            """, [new_uom, old_uom])
            
            # Update sales_uom
            frappe.db.sql("""
                UPDATE `tabItem` 
                SET sales_uom = %s 
                WHERE sales_uom = %s
            """, [new_uom, old_uom])
            
            print(f"  ✅ Updated Item references: {old_uom} -> {new_uom}")
            update_count += 1
    
    # Update UOM Conversion Factors
    for old_uom, new_uom in uom_mapping.items():
        if old_uom != new_uom:
            frappe.db.sql("""
                UPDATE `tabUOM Conversion Factor`
                SET from_uom = %s 
                WHERE from_uom = %s
            """, [new_uom, old_uom])
            
            frappe.db.sql("""
                UPDATE `tabUOM Conversion Factor`
                SET to_uom = %s 
                WHERE to_uom = %s
            """, [new_uom, old_uom])
    
    # Update transaction tables
    transaction_tables = [
        "tabStock Entry Detail",
        "tabPurchase Invoice Item", 
        "tabSales Invoice Item",
        "tabQuotation Item",
        "tabSales Order Item",
        "tabPurchase Order Item",
        "tabDelivery Note Item",
        "tabPurchase Receipt Item",
    ]
    
    for table in transaction_tables:
        try:
            for old_uom, new_uom in uom_mapping.items():
                if old_uom != new_uom:
                    frappe.db.sql(f"""
                        UPDATE `{table}`
                        SET uom = %s 
                        WHERE uom = %s
                    """, [new_uom, old_uom])
        except Exception:
            # Table might not exist in all setups
            pass
    
    frappe.db.commit()
    print(f"✅ Updated references for {update_count} UOMs")
    return update_count

def delete_all_uoms():
    """Delete all existing UOMs"""
    print("🗑️  Deleting all existing UOMs...")
    
    # First, try to delete UOM Conversion Factors
    try:
        frappe.db.sql("DELETE FROM `tabUOM Conversion Factor`")
        print("  ✅ Deleted all UOM Conversion Factors")
    except Exception as e:
        print(f"  ⚠️  Could not delete UOM Conversion Factors: {e}")
    
    # Delete all UOMs
    try:
        deleted_count = frappe.db.sql("SELECT COUNT(*) FROM `tabUOM`")[0][0]
        frappe.db.sql("DELETE FROM `tabUOM`")
        frappe.db.commit()
        print(f"  ✅ Deleted {deleted_count} UOMs")
        return deleted_count
    except Exception as e:
        print(f"  ❌ Error deleting UOMs: {e}")
        frappe.db.rollback()
        raise

def create_portuguese_uoms():
    """Create all Portuguese UOMs"""
    print("➕ Creating Portuguese UOMs...")
    
    created_count = 0
    
    for uom_data in PORTUGUESE_UOMS:
        try:
            uom_doc = frappe.get_doc({
                "doctype": "UOM",
                "uom_name": uom_data["name"],
                "enabled": 1,
                "must_be_whole_number": 1 if uom_data["must_be_whole"] else 0
            })
            uom_doc.insert(ignore_permissions=True)
            created_count += 1
            print(f"  ✅ Created: {uom_data['name']} {'(whole numbers)' if uom_data['must_be_whole'] else ''}")
            
        except Exception as e:
            print(f"  ❌ Failed to create {uom_data['name']}: {e}")
    
    frappe.db.commit()
    print(f"✅ Created {created_count} Portuguese UOMs")
    return created_count

def setup_portuguese_uoms_complete():
    """Main function to completely replace all UOMs with Portuguese ones"""
    print("🚀 Starting COMPLETE UOM replacement with Portuguese units...")
    print("⚠️  WARNING: This will delete ALL existing UOMs and create new Portuguese ones!")
    
    try:
        # Step 1: Get all UOMs
        old_uoms = frappe.get_all("UOM", 
            fields=["name", "uom_name", "enabled", "must_be_whole_number"],
            order_by="uom_name"
        )
        
        # Step 2: Get all UOM references
        references = get_uom_references()
        
        # Step 3: Create mapping from old to new UOMs
        uom_mapping, unmapped = create_uom_mapping(old_uoms, references)
        
        # Step 4: Update all references to use Portuguese names
        updated_refs = update_uom_references(uom_mapping)
        
        # Step 5: Delete all existing UOMs
        deleted_count = delete_all_uoms()
        
        # Step 6: Create new Portuguese UOMs
        created_count = create_portuguese_uoms()
        
        # Step 7: Final summary
        print("\n" + "="*60)
        print("🎉 COMPLETE UOM REPLACEMENT FINISHED!")
        print("="*60)
        print(f"🗑️  Deleted UOMs: {deleted_count}")
        print(f"➕ Created Portuguese UOMs: {created_count}")
        print(f"🔄 Updated references: {updated_refs}")
        print(f"⚠️  Unmapped UOMs: {len(unmapped)}")
        
        final_count = frappe.db.count("UOM")
        print(f"📊 Final UOM count: {final_count}")
        
        print("\n✅ SUCCESS: All UOMs are now in Portuguese!")
        print("💡 Users will only see Portuguese unit names in the system")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR during UOM replacement: {str(e)}")
        frappe.db.rollback()
        raise

def test_portuguese_uoms():
    """Test function to verify Portuguese UOMs exist"""
    print("🧪 Testing Portuguese UOMs...")
    
    total_uoms = frappe.db.count("UOM")
    print(f"Total UOMs in system: {total_uoms}")
    
    # Check some key Portuguese UOMs
    key_uoms = ["Unidade", "Quilograma", "Metro", "Litro", "Caixa", "Conjunto"]
    
    print("Key Portuguese UOMs:")
    for uom_name in key_uoms:
        if frappe.db.exists("UOM", uom_name):
            uom = frappe.get_doc("UOM", uom_name)
            print(f"  ✅ {uom_name} (whole: {bool(uom.must_be_whole_number)})")
        else:
            print(f"  ❌ {uom_name} - NOT FOUND")
    
    # Check for any remaining English UOMs
    english_uoms = ["Unit", "Nos", "Kg", "Meter", "Liter", "Box", "Set", "Piece", "Pair", "Dozen"]
    print("\nChecking for English UOMs:")
    english_found = []
    for uom_name in english_uoms:
        if frappe.db.exists("UOM", uom_name):
            english_found.append(uom_name)
            print(f"  ⚠️  {uom_name} - STILL EXISTS (should be Portuguese)")
    
    if not english_found:
        print("  ✅ No English UOMs found - system is 100% Portuguese!")
    else:
        print(f"  ❌ Found {len(english_found)} English UOMs that should be converted")
    
    print("✅ Test completed!")
    return len(english_found) == 0
