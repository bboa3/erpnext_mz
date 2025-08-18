# 🐳 Guia de Implantação Docker - App ERPNext Moçambique

## 🎯 Passo-a-Passo Completo (Do Zero ao Operacional)

## ✅ **CHECKLIST DE VERIFICAÇÃO**

### **Pré-Implantação**
- [ ] Docker e Docker Compose v2 disponíveis
- [ ] Serviços ERPNext em execução
- [ ] Pelo menos um site criado
- [ ] Ficheiros da app copiados para `../apps/erpnext_mz/` (opcional)

### **Durante a Implantação**
- [ ] Estrutura da app criada com sucesso
- [ ] App instalada nos sites alvo
- [ ] Setup de conformidade concluído para todas as empresas
- [ ] Campos personalizados criados (NUIT, série fiscal, AT)
- [ ] Formatos de impressão (gerir via UI; nenhum formato é criado pela app)
- [ ] Modelos de IVA criados (16%, 5%, 0%)
- [ ] Componentes de RH criados (INSS, IRPS, benefícios)

### **Pós-Implantação**
- [ ] App visível em `bench list-apps`
- [ ] Campos personalizados visíveis nos formulários
- [ ] Formatos de impressão disponíveis (se criados)
- [ ] Teste de geração do SAF‑T bem sucedido
- [ ] Definições da empresa (Moçambique, MZN)

---

## **🚀 IMPLANTAÇÃO AUTOMATIZADA (Recomendado)**

```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```

---

## **🔧 IMPLANTAÇÃO MANUAL (Passo-a-Passo)**

### **Passo 1: Preparar Ambiente**
```bash
cd frappe_docker
docker compose ps
# Se necessário
docker compose up -d
```

### **Passo 2: Diretório da App**
```bash
mkdir -p ../apps
mkdir -p ../apps/erpnext_mz
cp -r ../erpnext_mz/* ../apps/erpnext_mz/
chmod -R 755 ../apps/erpnext_mz/
```

### **Passo 3: Estrutura da App**
```bash
docker compose exec backend bench new-app erpnext_mz --skip-git
docker compose exec backend bash -c "rm -rf /home/frappe/frappe-bench/apps/erpnext_mz/*"
docker cp ../apps/erpnext_mz/. $(docker compose ps -q backend):/home/frappe/frappe-bench/apps/erpnext_mz/
docker compose exec backend bash -c "chown -R frappe:frappe /home/frappe/frappe-bench/apps/erpnext_mz/"
```

### **Passo 4: Instalar a App**
```bash
SITE_NAME="erp.example.com"
docker compose exec backend bench --site $SITE_NAME install-app erpnext_mz
```

### **Passo 5: Executar Setup**
```bash
COMPANY_NAME=$(docker compose exec backend bench --site $SITE_NAME console -c "
import frappe
companies = frappe.get_all('Company', limit=1)
print(companies[0].name)
" | tail -n 1)

echo "Empresa: $COMPANY_NAME"

docker compose exec backend bench --site $SITE_NAME console -c "
from erpnext_mz.setup import setup_mozambique_compliance
setup_mozambique_compliance('$COMPANY_NAME')
"
```

### **Passo 6: Verificar**
```bash
docker compose exec backend bench --site $SITE_NAME list-apps | grep erpnext_mz

# Não aplicável: a app não cria formatos de impressão
```

---

## 🚨 **PROBLEMAS COMUNS & SOLUÇÕES**

- Permissões/ownership: ajuste permissões em `../apps/erpnext_mz/`
- Site não acessível: verifique `show-config` e conectividade
- Falhas de setup: confirme Company/BD/Redis e volte a executar

---

## **✅ VERIFICAÇÃO FINAL**

- App instalada e sem erros
- Campos personalizados presentes (NUIT, série fiscal, AT)
- Modelos de IVA criados
- Componentes de RH criados
- Geração de SAF‑T funcional

---

## **PLANO DE ROLLBACK**

```bash
# Desinstalar a app
docker compose exec backend bench --site $SITE_NAME uninstall-app erpnext_mz
# Remover diretório
docker compose exec backend rm -rf /home/frappe/frappe-bench/apps/erpnext_mz
# Reiniciar serviços
docker compose restart backend
```

---

## **CONCLUSÃO**

A app ERPNext Moçambique está pronta para produção, com suporte multi‑tenant, logs, rollback e baixo impacto de recursos.
