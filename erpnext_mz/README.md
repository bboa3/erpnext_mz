# 🌍 ERPNext Mozambique - Clean Skeleton

This branch provides a minimal, clean installable app skeleton. All customizations have been removed so you can start fresh. The only remaining code is a standalone SAF-T generator module kept for reference and not connected to hooks or schedules.

---

## 📚 Documentation

No quick-deploy script or UI fixtures are included in this clean state.

---

## 🚀 Quick start
Install the app via bench as usual. There are no post-install hooks.

---

## 🌟 What remains

- SAF-T generator module (reference only): `erpnext_mz.modules.tax_compliance.saf_t_generator`

---

## 🏗️ Architecture

```
erpnext_mz/
└── modules/
    └── tax_compliance/      # SAF-T generator only
```

---

## 🔧 Deployment
Install the app on your site as a normal Frappe app. No schedules are registered.

---

## 📋 Pre-requisites

- ✅ **Docker & Docker Compose v2** installed
- ✅ **ERPNext running** in Docker containers
- ✅ **At least one site** created
- ✅ **Admin access** to ERPNext

---

## 🎯 After installation
- No custom fields, print formats, COA, HR, AT integration, or schedules.
- SAF-T generator available for you to wire later.

---

## 🔍 Verification

### Check Installation
```bash
# Verify app is installed
docker compose exec backend bench --site your-site.com list-apps | grep erpnext_mz

# No custom fields are installed in this clean skeleton
```

### Test SAF-T Generator (manual)
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

## 🚨 Troubleshooting

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

## 📖 Next steps

1. Add hooks you need in `hooks.py`
2. Reintroduce modules progressively (fields, fixtures, AT, HR)
3. Connect the SAF-T generator to schedules when ready

---

## 🌟 Support & community

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
