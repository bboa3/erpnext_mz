# 🔍 ERPNext Mozambique App - Troubleshooting & Verification Checklist

## 🎯 **Purpose of This Document**

This document is for **troubleshooting and verification** after deployment. It's **NOT** for initial deployment - use [README.md](README.md) for that.

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
- [ ] Custom fields visible in forms
- [ ] Print formats available for selection

### **✅ Mozambique Compliance Setup**
- [ ] Chart of Accounts created (IFRS structure)
- [ ] VAT templates created (16%, 5%, 0%)
- [ ] HR components created (INSS, IRPS)
- [ ] Custom fields created (NUIT, fiscal, AT)

### **✅ Functionality Testing**
- [ ] SAF-T generation works
- [ ] VAT calculations correct
- [ ] HR & Payroll components functional
- [ ] API endpoints responding

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

### **Issue 2: Custom Fields Not Showing**
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
- [ ] All API endpoints responding
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
- [ ] Compliance reporting scheduled

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
- Remove specific custom fields
- Disable specific features
- Rollback specific configurations

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
- **[DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)** - Detailed deployment steps

---

**Remember**: This document is for troubleshooting, not initial deployment. Start with [README.md](README.md) for deployment instructions.

### 4. Verification Steps
```bash
# Check if app is installed
bench --site your-site.com list-apps | grep erpnext_mz

# Check custom fields
bench --site your-site.com console
frappe.get_all("Custom Field", filters={"app": "erpnext_mz"})

# Check print formats
frappe.get_all("Print Format", filters={"app": "erpnext_mz"})
```

## Post-Deployment Configuration

### 1. Company Settings
- [ ] Set company country to "Mozambique"
- [ ] Set company currency to "MZN"
- [ ] Add company NUIT number
- [ ] Add AT certification number (if available)

### 2. AT Integration Setup (Optional)
- [ ] Configure AT API endpoint
- [ ] Add AT API key
- [ ] Enable AT integration
- [ ] Test invoice transmission

### 3. User Permissions
- [ ] Ensure users have proper roles
- [ ] Test custom field access
- [ ] Verify print format access

## Testing Checklist

### 1. Basic Functionality
- [ ] App loads without errors
- [ ] Custom fields appear in forms
- [ ] Print formats work correctly
- [ ] Chart of accounts created

### 2. SAF-T Generation
- [ ] Generate test SAF-T files
- [ ] Verify XML structure
- [ ] Check file saving
- [ ] Validate checksums

### 3. HR & Payroll
- [ ] INSS calculations work
- [ ] IRPS calculations work
- [ ] Benefits in kind setup
- [ ] Salary components created

### 4. API Endpoints
- [ ] SAF-T generation API
- [ ] AT integration API
- [ ] Proper error responses
- [ ] Authentication working

## Troubleshooting

### Common Issues
1. **Import Errors**: Check all module imports
2. **Custom Fields Not Showing**: Clear browser cache
3. **File Permission Errors**: Check site file permissions
4. **Database Errors**: Verify database connectivity

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
2. **Remove custom fields**: Delete via ERPNext admin
3. **Restore from backup**: If database changes were made
4. **Check logs**: Identify root cause before re-deployment

## Success Criteria

### Deployment Success
- [ ] App installs without errors
- [ ] All custom fields created successfully
- [ ] Chart of accounts setup complete
- [ ] VAT templates created
- [ ] HR components working
- [ ] SAF-T generation functional
- [ ] No console errors in browser
- [ ] All API endpoints responding

### Compliance Ready
- [ ] Mozambique Chart of Accounts active
- [ ] VAT rates configured (16%, 5%, 0%)
- [ ] INSS/IRPS calculations working
- [ ] SAF-T XML generation working
- [ ] Custom fields for NUIT and fiscal data
- [ ] Print formats with fiscal information

---

**Note**: This checklist should be completed before going live with the Mozambique compliance features. Ensure all items are verified to avoid production issues.
