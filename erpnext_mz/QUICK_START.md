# 🚀 Início Rápido - 5 Minutos

## **⚡ IMPLANTAÇÃO SUPER RÁPIDA**

### **Opção 1: Um Comando (Mais Fácil)**
```bash
# Ir para a pasta frappe_docker
cd frappe_docker

# Executar o script automatizado
../erpnext_mz/deploy_docker.sh
```

**Pronto!** O script trata de tudo automaticamente.

---

## **🔧 Implantação Manual Rápida**

### **Passo 1: Ir para frappe_docker**
```bash
cd frappe_docker
```

### **Passo 2: Copiar Ficheiros da App (opcional)**
```bash
mkdir -p ../apps/erpnext_mz
cp -r ../erpnext_mz/* ../apps/erpnext_mz/
```

### **Passo 3: Instalar a App**
```bash
# Criar estrutura da app (se necessário)
docker compose exec backend bench new-app erpnext_mz --skip-git

# Copiar os nossos ficheiros
docker compose exec backend bash -c "rm -rf /home/frappe/frappe-bench/apps/erpnext_mz/*"
docker cp ../apps/erpnext_mz/. $(docker compose ps -q backend):/home/frappe/frappe-bench/apps/erpnext_mz/

# Permissões
docker compose exec backend bash -c "chown -R frappe:frappe /home/frappe/frappe-bench/apps/erpnext_mz/"

# Instalar app (substituir pelo seu site)
docker compose exec backend bench --site erp.example.com install-app erpnext_mz
```

### **Passo 4: Executar Setup**
```bash
# Obter empresa e executar setup
COMPANY=$(docker compose exec backend bench --site erp.example.com console -c "import frappe; print(frappe.get_all('Company', limit=1)[0].name)" | tail -n 1)

docker compose exec backend bench --site erp.example.com console -c "
from erpnext_mz.setup import setup_mozambique_compliance
setup_mozambique_compliance('$COMPANY')
"
```

---

## **✅ Verificar**
```bash
# Verificar se a app está instalada
docker compose exec backend bench --site erp.example.com list-apps | grep erpnext_mz

# Testar SAF‑T
docker compose exec backend bench --site erp.example.com console -c "
from erpnext_mz.modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
result = generate_monthly_saf_t('$COMPANY', 2025, 1)
print('✅ Sucesso:', result)
"
```

---

## **🎯 O que recebe**

- ✅ **Modelos de IVA** (16%, 5%, 0%)
- ✅ **INSS & IRPS**
- ✅ **Geração de SAF‑T**
- ✅ **Campos Personalizados** (NUIT, série fiscal)
- ✅ **Formato de Fatura Moçambique**
- ✅ **Benefícios em Espécie**

---

## **🚨 Precisa de Ajuda?**

- **Logs**: `docker compose logs backend`
- **Console**: `docker compose exec backend bench --site erp.example.com console`
- **Guia completo**: `DOCKER_DEPLOYMENT_GUIDE.md`
- **Checklist**: `DEPLOYMENT_CHECKLIST.md`

---

**🎉 Pronto para conformidade em Moçambique!**
