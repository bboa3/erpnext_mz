# 🌍 ERPNext Mozambique - Custom App

## 🎯 **Complete Mozambique Tax Compliance for ERPNext**

A comprehensive custom app that adds Mozambique-specific tax compliance, accounting, and HR features to ERPNext, ensuring full compliance with 2025 regulations including SAF-T, VAT, INSS, IRPS, and real-time electronic fiscalization.

---

## 📚 **DOCUMENTATION NAVIGATION**

### **🚀 Start Here (Choose Your Path)**

| **For** | **Read This** | **Time** | **Complexity** |
|---------|---------------|----------|----------------|
| **Quick Deployment** | [QUICK_START.md](QUICK_START.md) | 5 minutes | ⭐ Easy |
| **Full Docker Guide** | [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md) | 15 minutes | ⭐⭐ Medium |
| **Troubleshooting** | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | As needed | ⭐⭐⭐ Advanced |

---

## 🚀 **QUICK START (5 Minutes)**

### **One-Command Deployment**
```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```

**That's it!** The script handles everything automatically.

### **What Happens:**
1. ✅ Detects your ERPNext sites automatically
2. ✅ Lets you choose which sites to deploy to
3. ✅ Installs the app on selected sites
4. ✅ Sets up Mozambique compliance for all companies
5. ✅ Verifies everything works correctly

---

## 🌟 **KEY FEATURES**

### **📊 Tax Compliance**
- **SAF-T Generation** - Monthly XML exports for tax authority
- **Real-time Fiscalization** - Electronic invoice monitoring
- **VAT Management** - 16%, 5%, 0% rates with proper calculations
- **AT Integration** - Direct connection to Tax Authority

### **🏦 Accounting**
- **Mozambique Chart of Accounts** - IFRS-compliant structure
- **Fiscal Document Management** - Series and numbering
- **Custom Fields** - NUIT, fiscal series, AT certification
- **Print Formats** - Mozambique-standard invoices

### **👥 HR & Payroll**
- **INSS Calculations** - Employer 4%, Employee 3%
- **IRPS Tax** - Progressive tax brackets (10% to 32%)
- **Benefits in Kind** - Vehicle, housing, insurance valuation
- **3% Variance Rule** - Sales vs. Payroll compliance

---

## 🏗️ **ARCHITECTURE**

```
erpnext_mz/
├── modules/
│   ├── accounting/          # Chart of accounts, VAT
│   ├── hr_payroll/          # INSS, IRPS, benefits
│   └── tax_compliance/      # SAF-T, AT integration
├── api/                     # REST endpoints
├── deploy_docker.sh         # 🚀 Main deployment script
└── setup.py                 # Mozambique compliance setup
```

---

## 🔧 **DEPLOYMENT OPTIONS**

### **Option 1: Automated (Recommended)**
```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```
**Best for**: Most users, handles everything automatically

### **Option 2: Manual Step-by-Step**
Follow [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)
**Best for**: Learning, troubleshooting, custom deployments

### **Option 3: Quick Manual**
Follow [QUICK_START.md](QUICK_START.md)
**Best for**: Fast deployment with minimal steps

---

## 📋 **PRE-REQUISITES**

- ✅ **Docker & Docker Compose v2** installed
- ✅ **ERPNext running** in Docker containers
- ✅ **At least one site** created
- ✅ **Admin access** to ERPNext

---

## 🎯 **WHAT YOU GET AFTER DEPLOYMENT**

### **Immediate Benefits**
- ✅ **Mozambique Chart of Accounts** - Ready to use
- ✅ **VAT Templates** - 16%, 5%, 0% rates configured
- ✅ **Custom Fields** - NUIT, fiscal data in forms
- ✅ **Print Formats** - Mozambique invoice layout
- ✅ **HR Components** - INSS, IRPS salary components

### **Compliance Features**
- ✅ **SAF-T Generation** - Monthly XML exports
- ✅ **Real-time Monitoring** - Electronic fiscalization
- ✅ **Tax Calculations** - Accurate VAT, INSS, IRPS
- ✅ **Benefits Management** - Proper valuation and inclusion

---

## 🔍 **VERIFICATION**

### **Check Installation**
```bash
# Verify app is installed
docker compose exec backend bench --site your-site.com list-apps | grep erpnext_mz

# Check custom fields
docker compose exec backend bench --site your-site.com console -c "
import frappe
print(len(frappe.get_all('Custom Field', filters={'app': 'erpnext_mz'})))
"
```

### **Test SAF-T Generation**
```bash
docker compose exec backend bench --site your-site.com console -c "
from erpnext_mz.modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
companies = frappe.get_all('Company', limit=1)
if companies:
    result = generate_monthly_saf_t(companies[0].name, 2025, 1)
    print('✅ Success:', result)
"
```

---

## 🚨 **TROUBLESHOOTING**

### **Common Issues**
1. **App not installing** → Check Docker services are running
2. **Custom fields not showing** → Clear browser cache
3. **Import errors** → Verify app structure is correct
4. **Permission denied** → Check file ownership

### **Get Help**
- **Check logs**: `docker compose logs backend`
- **Access console**: `docker compose exec backend bench --site your-site.com console`
- **Full troubleshooting**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## 📖 **NEXT STEPS**

### **After Deployment**
1. **Configure Company** → Set country to "Mozambique", currency to "MZN"
2. **Add NUIT Numbers** → Enter company and customer NUIT
3. **Test Features** → Generate SAF-T, check VAT calculations
4. **Configure AT** → Set up Tax Authority integration (optional)

### **Production Readiness**
1. **Test thoroughly** → Verify all compliance features
2. **Train users** → Show new fields and features
3. **Monitor compliance** → Regular SAF-T generation
4. **Stay updated** → Follow Mozambique tax regulation changes

---

## 🌟 **SUPPORT & COMMUNITY**

- **Documentation**: This README and linked guides
- **Issues**: Check [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for solutions
- **Customization**: Modify [setup.py](setup.py) for specific needs
- **Updates**: Follow ERPNext and Mozambique tax regulation updates

---

## 🎉 **READY TO DEPLOY?**

### **Start Here:**
```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```

**The app is production-ready and will give you complete Mozambique compliance in minutes!** 🚀

---

*For detailed information, see the linked documentation files above.*
