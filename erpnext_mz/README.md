# 🌍 ERPNext Moçambique - Aplicação Customizada

## 🎯 **Conformidade Fiscal para Moçambique no ERPNext**

Uma aplicação que adiciona conformidade fiscal, contabilidade e RH específicas de Moçambique ao ERPNext, incluindo SAF‑T, IVA, INSS, IRPS e integração com a AT.

---

## 📚 **NAVEGAÇÃO DA DOCUMENTAÇÃO**

### **🚀 Comece Aqui (Escolha o Caminho)**

| **Para** | **Leia** | **Tempo** | **Complexidade** |
|---------|-------------|----------|------------------|
| **Implantação Rápida** | [QUICK_START.md](QUICK_START.md) | 5 minutos | ⭐ Fácil |
| **Guia Completo Docker** | [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md) | 15 minutos | ⭐⭐ Médio |
| **Resolução de Problemas** | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Conforme necessário | ⭐⭐⭐ Avançado |

---

## 🚀 **INÍCIO RÁPIDO (5 Minutos)**

### **Implantação com um Comando**
```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```

**É isso!** O script trata de tudo automaticamente.

### **O que acontece:**
1. ✅ Detecta automaticamente os seus sites ERPNext
2. ✅ Permite escolher os sites de destino
3. ✅ Instala a aplicação
4. ✅ Configura conformidade para todas as empresas
5. ✅ Verifica se tudo correu bem

---

## 🌟 **FUNCIONALIDADES**

### **📊 Conformidade Fiscal**
- **Geração de SAF‑T** - Exportações mensais em XML
- **Fiscalização em Tempo Real** - Monitorização eletrónica de faturas
- **Gestão de IVA** - 16%, 5%, 0%
- **Integração com a AT**

### **🏦 Contabilidade**
- **Gestão de Documentos Fiscais** - Séries e numeração
- **Campos Personalizados** - NUIT, série fiscal, certificação AT
- **Formatos de Impressão** - Fatura padrão Moçambique

### **👥 RH & Folha**
- **INSS** - Empregador 4%, Empregado 3%
- **IRPS** - Escalões progressivos (10% a 32%)
- **Benefícios em Espécie** - Viatura, habitação, seguros
- **Regra dos 3%** - Vendas vs. Folha

---

## 🏗️ **ARQUITETURA**

```
erpnext_mz/
├── modules/
│   ├── accounting/          # IVA, categorias e templates
│   ├── hr_payroll/          # INSS, IRPS, benefícios
│   └── tax_compliance/      # SAF-T, integração AT
├── api/                     # Endpoints REST
├── deploy_docker.sh         # 🚀 Script principal de implantação
└── setup.py                 # Configuração de conformidade Moçambique
```

---

## 🔧 **OPÇÕES DE IMPLANTAÇÃO**

### **Opção 1: Automatizada (Recomendado)**
```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```
**Ideal**: Maioria dos utilizadores; trata de tudo

### **Opção 2: Manual Passo‑a‑Passo**
Siga [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)

### **Opção 3: Manual Rápido**
Siga [QUICK_START.md](QUICK_START.md)

---

## 📋 **PRÉ‑REQUISITOS**

- ✅ **Docker & Docker Compose v2** instalados
- ✅ **ERPNext a correr** em contentores Docker
- ✅ **Pelo menos um site** criado
- ✅ **Acesso admin** ao ERPNext

---

## 🎯 **APÓS A IMPLANTAÇÃO**

### **Benefícios Imediatos**
- ✅ **Modelos de IVA** - 16%, 5%, 0% configurados
- ✅ **Campos Personalizados** - NUIT, dados fiscais
- ✅ **Formatos de Impressão** - Layout padrão Moçambique
- ✅ **Componentes de RH** - INSS, IRPS

### **Conformidade**
- ✅ **Geração de SAF‑T**
- ✅ **Monitorização em tempo real**
- ✅ **Cálculos de IVA/INSS/IRPS**
- ✅ **Gestão de benefícios**

---

## 🔍 **VERIFICAÇÃO**

### **Verificar Instalação**
```bash
# Verificar app instalada
docker compose exec backend bench --site your-site.com list-apps | grep erpnext_mz

# Contar campos personalizados
docker compose exec backend bench --site your-site.com console -c "
import frappe
print(len(frappe.get_all('Custom Field', filters={'app': 'erpnext_mz'})))
"
```

### **Testar Geração de SAF‑T**
```bash
docker compose exec backend bench --site your-site.com console -c "
from erpnext_mz.modules.tax_compliance.saf_t_generator import generate_monthly_saf_t
companies = frappe.get_all('Company', limit=1)
if companies:
    result = generate_monthly_saf_t(companies[0].name, 2025, 1)
    print('✅ Sucesso:', result)
"
```

---

## 🚨 **RESOLUÇÃO DE PROBLEMAS**

- **Logs**: `docker compose logs backend`
- **Console**: `docker compose exec backend bench --site your-site.com console`
- **Checklist**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

## 📖 **PRÓXIMOS PASSOS**

1. **Configurar Empresa** → País "Moçambique", moeda "MZN"
2. **Adicionar NUIT** → Empresa e Clientes/Fornecedores
3. **Testar** → Gerar SAF‑T, validar IVA
4. **Configurar AT** → Integração (opcional)

---

## 🌟 **SUPORTE & COMUNIDADE**

- **Documentação**: Este README e guias ligados
- **Issues**: Ver [DEPLOYMENT_CHECKLIST.md]
- **Customização**: Ajustar [setup.py]
- **Atualizações**: Acompanhar ERPNext e legislação Moçambique

---

## 🎉 **PRONTO PARA IMPLANTAÇÃO?**

```bash
cd frappe_docker
../erpnext_mz/deploy_docker.sh
```

**Aplicação pronta para produção!** 🚀
