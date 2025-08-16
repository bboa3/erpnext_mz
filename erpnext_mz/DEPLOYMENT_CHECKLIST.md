# 🔍 ERPNext Mozambique App - Troubleshooting & Verification Checklist (Clean Skeleton)

## 🎯 **Purpose of This Document**

This document is for **troubleshooting and verification** after deployment. In the clean skeleton, most feature checks are intentionally N/A.

---

## 🚨 **WHEN TO USE THIS DOCUMENT**

- ❌ **Don't use this for initial deployment**
- ✅ **Use this for troubleshooting issues**
- ✅ **Use this for verifying deployment success**
- ✅ **Use this for production readiness checks**

---

## 📋 **VERIFICATION CHECKLIST**

### **✅ App Installation Verification**
- [ ] App appears in `bench list-apps`
- [ ] No import errors in console
- [ ] Custom fields visible in forms (N/A in clean skeleton)
- [ ] Print formats available for selection (N/A in clean skeleton)

### **✅ Mozambique Compliance Setup** (N/A in clean skeleton)
- [ ] Chart of Accounts created (IFRS structure)
- [ ] VAT templates created (16%, 5%, 0%)
- [ ] HR components created (INSS, IRPS)
- [ ] Custom fields created (NUIT, fiscal, AT)

### **✅ Functionality Testing**
- [ ] SAF-T generation works (manual invocation only)
- [ ] VAT calculations correct (N/A)
- [ ] HR & Payroll components functional (N/A)
- [ ] API endpoints responding (N/A)

---

## 🔧 **TROUBLESHOOTING COMMON ISSUES**

### **Issue 1: App Not Installing**
```bash
# Check Docker services
docker compose ps

# Check app directory exists
docker compose exec backend ls -la /home/frappe/frappe-bench/apps/erpnext_mz/

# Check permissions
docker compose exec backend ls -la /home/frappe/frappe-bench/apps/erpnext_mz/
```

**Solutions:**
- Ensure ERPNext services are running
- Check app directory permissions
- Verify app structure is correct

### **Issue 2: Custom Fields Not Showing** (N/A)
```bash
# Check custom fields exist
docker compose exec backend bench --site your-site.com console -c "
import frappe
custom_fields = frappe.get_all('Custom Field', filters={'app': 'erpnext_mz'})
print(f'Found {len(custom_fields)} custom fields')
"
```

**Solutions:**
- Clear browser cache
- Check user permissions
- Verify custom fields were created

### **Issue 3: Import Errors**
```bash
# Test app imports
docker compose exec backend bench --site your-site.com console -c "
import erpnext_mz
print('✅ App imports successfully')
"
```

**Solutions:**
- Check app structure
- Verify all required files exist
- Check Python syntax in modules

### **Issue 4: SAF-T Generation Fails**
```bash
# Test SAF-T generation
docker compose exec backend bench --site your-site.com console -c "
from erpnext_mz.modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
try:
    companies = frappe.get_all('Company', limit=1)
    if companies:
        result = generate_monthly_saf_t(companies[0].name, 2025, 1)
        print('✅ Success:', result)
    else:
        print('❌ No companies found')
except Exception as e:
    print(f'❌ Error: {str(e)}')
"
```

**Solutions:**
- Check company configuration
- Verify file permissions
- Check disk space

---

## 🚀 **PRODUCTION READINESS CHECK**

### **Pre-Go-Live Verification**
- [ ] All verification tests pass
- [ ] No console errors in browser
- [ ] All API endpoints responding (N/A)
- [ ] Performance acceptable
- [ ] Backup procedures in place

### **User Training Checklist**
- [ ] Users understand new fields
- [ ] Users can generate SAF-T files
- [ ] Users understand VAT calculations
- [ ] Users know compliance requirements

### **Monitoring Setup**
- [ ] Log monitoring configured
- [ ] Error alerting set up
- [ ] Performance monitoring active
- [ ] Compliance reporting scheduled (N/A)

---

## 🔄 **ROLLBACK PROCEDURES**

### **If Critical Issues Found**
```bash
# 1. Uninstall app
docker compose exec backend bench --site your-site.com uninstall-app erpnext_mz

# 2. Remove app directory
docker compose exec backend rm -rf /home/frappe/frappe-bench/apps/erpnext_mz

# 3. Restart services
docker compose restart backend

# 4. Restore from backup if needed
```

### **Partial Rollback Options**
- Remove specific custom fields (N/A)
- Disable specific features (N/A)
- Rollback specific configurations (N/A)

---

## 📞 **GETTING HELP**

### **Self-Service Troubleshooting**
1. **Check this checklist** for common solutions
2. **Review deployment logs** for error details
3. **Test functionality** step by step
4. **Check ERPNext documentation** for framework issues

### **When to Seek External Help**
- App won't install after multiple attempts
- Critical functionality not working
- Performance issues affecting production
- Compliance requirements not met

---

## 📚 **RELATED DOCUMENTATION**

- **[README.md](README.md)** - Start here for deployment
- **[QUICK_START.md](QUICK_START.md)** - Fast deployment guide
- **[DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)** - Minimal deployment notes

---

**Remember**: This document is for troubleshooting, not initial deployment. Start with [README.md](README.md) for deployment instructions.

### 4. Verification Steps
```bash
# Check if app is installed
bench --site your-site.com list-apps | grep erpnext_mz

# Custom fields and print formats are not included in the clean skeleton
```

## Post-Deployment Configuration

### 1. Company Settings (optional)
- [ ] Set company country to "Mozambique"
- [ ] Set company currency to "MZN"

### 2. AT Integration Setup (N/A)

### 3. User Permissions (N/A)

## Testing Checklist

### 1. Basic Functionality
- [ ] App loads without errors

### 2. SAF-T Generation
- [ ] Generate test SAF-T files
- [ ] Verify XML structure
- [ ] Check file saving
- [ ] Validate checksums

### 3. HR & Payroll (N/A)

### 4. API Endpoints (N/A)

## Troubleshooting

### Common Issues
1. **Import Errors**: Check all module imports
2. **File Permission Errors**: Check site file permissions
3. **Database Errors**: Verify database connectivity

### Debug Commands
```bash
# Check app logs
bench --site your-site.com tail-logs

# Check app status
bench --site your-site.com show-config

# Test app imports
bench --site your-site.com console
import erpnext_mz
```

## Rollback Plan

### If Issues Occur
1. **Uninstall app**: `bench --site your-site.com uninstall-app erpnext_mz`
2. **Restore from backup**: If database changes were made
3. **Check logs**: Identify root cause before re-deployment

## Success Criteria

### Deployment Success
- [ ] App installs without errors
- [ ] SAF-T generator imports and can be called manually
- [ ] No console errors in browser

### Compliance Ready (future work)
- [ ] SAF-T XML generation working (when wired)

---

**Note**: This checklist should be completed before going live with the Mozambique compliance features. Ensure all items are verified to avoid production issues.
