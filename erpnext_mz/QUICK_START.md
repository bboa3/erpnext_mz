# 🚀 Quick Start - Deploy in 5 Minutes!

## **⚡ SUPER FAST DEPLOYMENT**

### **Option 1: One-Command Deployment (Easiest)**
```bash
# Navigate to frappe_docker directory
cd frappe_docker

# Run the automated deployment script
../erpnext_mz/deploy_docker.sh
```

**That's it! The script handles everything automatically.**

---

## **🔧 Manual Quick Deployment**

### **Step 1: Navigate to frappe_docker**
```bash
cd frappe_docker
```

### **Step 2: Copy App Files**
```bash
mkdir -p ../apps/erpnext_mz
cp -r ../erpnext_mz/* ../apps/erpnext_mz/
```

### **Step 3: Install App**
```bash
# Create app structure
docker compose exec backend bench new-app erpnext_mz --skip-git

# Copy our files
docker compose exec backend bash -c "rm -rf /home/frappe/frappe-bench/apps/erpnext_mz/*"
docker cp ../apps/erpnext_mz/. $(docker compose ps -q backend):/home/frappe/frappe-bench/apps/erpnext_mz/

# Set permissions
docker compose exec backend bash -c "chown -R frappe:frappe /home/frappe/frappe-bench/apps/erpnext_mz/"

# Install app (replace with your site name)
docker compose exec backend bench --site erp.example.com install-app erpnext_mz
```

### **Step 4: Run Setup**
```bash
# Get company name and run setup
COMPANY=$(docker compose exec backend bench --site erp.example.com console -c "import frappe; print(frappe.get_all('Company', limit=1)[0].name)" | tail -n 1)

docker compose exec backend bench --site erp.example.com console -c "
from erpnext_mz.setup import setup_mozambique_compliance
setup_mozambique_compliance('$COMPANY')
"
```

---

## **✅ Verify Deployment**
```bash
# Check if app is installed
docker compose exec backend bench --site erp.example.com list-apps | grep erpnext_mz

# Test SAF-T generation
docker compose exec backend bench --site erp.example.com console -c "
from erpnext_mz.modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
result = generate_monthly_saf_t('$COMPANY', 2025, 1)
print('✅ Success:', result)
"
```

---

## **🎯 What You Get**

- ✅ **Mozambique Chart of Accounts** (IFRS compliant)
- ✅ **VAT Templates** (16%, 5%, 0%)
- ✅ **INSS & IRPS Calculations**
- ✅ **SAF-T XML Generation**
- ✅ **Custom Fields** (NUIT, fiscal series)
- ✅ **Mozambique Invoice Format**
- ✅ **Benefits in Kind Management**

---

## **🚨 Need Help?**

- **Check logs**: `docker compose logs backend`
- **Access console**: `docker compose exec backend bench --site erp.example.com console`
- **Full guide**: See `DOCKER_DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: See `DEPLOYMENT_CHECKLIST.md`

---

**🎉 You're now ready for Mozambique compliance!**
