# Print Format Preparation System

## Overview

The Print Format Preparation System ensures clean deployment of Mozambique-specific print formats by automatically disabling existing print formats before creating new ones. This prevents conflicts and ensures a consistent user experience.

## Script: `disable_existing_print_formats.py`

### Core Functions

#### 1. `disable_all_existing_print_formats()`
- **Purpose**: Disables all existing print formats in the system
- **Scope**: Targets all print formats regardless of DocType
- **Safety**: Skips already disabled formats
- **Result**: Returns count of disabled and skipped formats

#### 2. `disable_print_formats_by_doctype(doctypes_list)`
- **Purpose**: Disables print formats for specific DocTypes only
- **Scope**: Targeted approach for specific business documents
- **Default DocTypes**: Sales, Purchase, Inventory, Financial, HR, Customer/Supplier documents
- **Flexibility**: Accepts custom list of DocTypes

#### 3. `reset_print_format_defaults()`
- **Purpose**: Clears default print format settings on DocTypes
- **Scope**: Resets DocType-level default print format configurations
- **Safety**: Only affects DocTypes that have default print format fields

#### 4. `prepare_for_mozambique_print_formats()`
- **Purpose**: Complete preparation workflow
- **Steps**: 
  1. Disable all existing print formats
  2. Reset default print format settings
- **Result**: System ready for Mozambique print format generation

## Integration Points

### 1. **Automatic Integration**
The preparation script is automatically called before print format generation in:
- `comprehensive_print_formats.py`
- `simple_print_formats.py`
- `onboarding.py` (Company Setup Wizard)

### 2. **Manual Execution**
Can be run independently for maintenance:
```bash
bench --site erp.local execute "erpnext_mz.setup.disable_existing_print_formats.prepare_for_mozambique_print_formats"
```

### 3. **Targeted Execution**
For specific DocTypes only:
```bash
bench --site erp.local execute "erpnext_mz.setup.disable_existing_print_formats.disable_print_formats_by_doctype"
```

## Test Results

### ✅ **Successful Execution**
```json
{
  "disabled": 21,
  "skipped": 4,
  "reset_defaults": 0,
  "status": "ready_for_mozambique_formats"
}
```

**Interpretation:**
- **21 formats disabled**: Successfully disabled active print formats
- **4 formats skipped**: Already disabled formats left unchanged
- **0 defaults reset**: No DocType default settings found to reset
- **Status**: System ready for Mozambique print format generation

## Safety Features

### 1. **Non-Destructive**
- Only disables formats, doesn't delete them
- Can be re-enabled if needed
- Preserves all existing data

### 2. **Error Handling**
- Comprehensive try-catch blocks
- Detailed error logging
- Graceful failure handling

### 3. **Logging**
- All actions logged to Error Log
- Detailed summary of operations
- Audit trail for troubleshooting

### 4. **Validation**
- Checks format status before modification
- Skips already disabled formats
- Validates DocType existence

## Usage Scenarios

### 1. **Initial Setup**
- Run during company setup wizard
- Ensures clean slate for new installations
- Automatic integration with onboarding process

### 2. **Format Updates**
- Run before deploying new print format versions
- Prevents conflicts between old and new formats
- Ensures consistent user experience

### 3. **Maintenance**
- Run periodically to clean up unused formats
- Reset system to known state
- Prepare for format reorganization

### 4. **Troubleshooting**
- Run to resolve print format conflicts
- Reset system when formats become corrupted
- Clean up after failed format installations

## Technical Details

### Database Operations
- Uses `frappe.db.set_value()` for efficient updates
- Batch operations with `frappe.db.commit()`
- Minimal database queries for performance

### Performance Considerations
- Efficient queries with proper filtering
- Batch processing for multiple formats
- Minimal memory footprint

### Error Recovery
- Detailed error messages for troubleshooting
- Rollback capability on failures
- Comprehensive logging for audit trails

## Monitoring and Maintenance

### 1. **Log Monitoring**
Check Error Log for:
- `Print Format Disabled` entries
- `Print Format Disable Summary` entries
- `Print Format Preparation` entries

### 2. **Status Verification**
Verify preparation success:
```python
# Check disabled formats
frappe.get_all("Print Format", filters={"disabled": 1})

# Check active formats
frappe.get_all("Print Format", filters={"disabled": 0})
```

### 3. **Rollback Procedure**
If needed, re-enable formats:
```python
# Re-enable specific format
frappe.db.set_value("Print Format", "format_name", "disabled", 0)

# Re-enable all formats
frappe.db.sql("UPDATE `tabPrint Format` SET disabled = 0")
```

## Best Practices

### 1. **Always Run Before Format Generation**
- Ensures clean deployment
- Prevents user confusion
- Maintains system consistency

### 2. **Monitor Logs**
- Check Error Log after execution
- Verify expected counts
- Investigate any anomalies

### 3. **Test in Development First**
- Run preparation script in dev environment
- Verify expected behavior
- Test rollback procedures

### 4. **Document Changes**
- Keep record of disabled formats
- Note any custom formats affected
- Plan for re-enablement if needed

## Conclusion

The Print Format Preparation System provides a robust, safe, and efficient way to prepare the system for Mozambique print format deployment. It ensures clean installations, prevents conflicts, and maintains system integrity while providing comprehensive logging and error handling.

The system is designed to be:
- **Safe**: Non-destructive operations with rollback capability
- **Efficient**: Minimal database operations and fast execution
- **Reliable**: Comprehensive error handling and logging
- **Flexible**: Multiple execution modes for different scenarios
- **Integrated**: Automatic integration with existing workflows
