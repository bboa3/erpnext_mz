# Relatório: ERPNext e Conformidade Fiscal em Moçambique (2025)

**Implementação, Localização e Modelo de Negócio SaaS Multi-Tenant**

---

## 1. Contexto e Oportunidade

Moçambique está em plena transformação digital fiscal. A Autoridade Tributária (AT) e o Instituto Nacional de Segurança Social (INSS) avançam com:

* **Fiscalização eletrónica quase em tempo real** para faturas emitidas.
* **Obrigatoriedade de submissão mensal de ficheiros SAF-T** para vendas e folha de pagamento, com certificação de software.
* **Integração cruzada** entre faturação, contabilidade e folha, com tolerância máxima de **3% de variação** nos valores brutos reportados.
* **Checksums anti-adulteração**, prazos reduzidos (INSS até dia 15) e **penalidades severas** — bloqueio da conta fiscal por 5 dias, multas e até processo criminal.

Neste cenário, a conformidade não é apenas gerar relatórios: é **integração contínua e automatizada com a AT**.

O **ERPNext**, ERP open-source construído no Frappe Framework (Python, JavaScript, MariaDB, MVC, API-first), destaca-se porque:

* Não tem custos de licença — viabiliza direcionar orçamento para localização e customização.
* É altamente personalizável via **Custom Apps** isoladas do core, garantindo compatibilidade com atualizações.
* Possui módulos robustos de Contabilidade, Vendas, RH e Folha — ideais para integrar exigências fiscais, laborais e de inventário num único sistema.

---

## 2. Panorama Fiscal Moçambicano 2025

### 2.1 Requisitos-chave

| Requisito                      | Detalhe                                                                                          | Impacto no ERPNext                         |
| ------------------------------ | ------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| **IVA (16% e 5%)**             | Cobrança e reporte mensal, taxas reduzidas para setores específicos                              | Templates de imposto configuráveis         |
| **IFRS**                       | Obrigatórias p/ médias e grandes empresas                                                        | Plano de contas adaptado + relatórios IFRS |
| **Faturação certificada**      | Software certificado AT, numeração sequencial, dados obrigatórios, assinatura digital se exigida | Custom App + certificação                  |
| **Fiscalização em tempo real** | Envio imediato ou quase imediato das faturas à AT                                                | Integração API + hooks pós-submissão       |
| **SAF-T Vendas**               | Submissão mensal de ficheiro XML                                                                 | Script de geração + validação schema       |
| **SAF-T Folha**                | “Tag” de folha no XML; variação ≤3% face a vendas; cruzamento com INSS                           | Adaptação profunda no módulo de RH         |
| **Benefícios em espécie**      | Avaliação em MZN, inclusão no bruto e no SAF-T                                                   | Campos e cálculos personalizados           |
| **Checksums e arquivo**        | Retenção 10 anos, integridade comprovada                                                         | Rotinas de arquivo + backup seguro         |

---

## 3. Capacidades Nativas do ERPNext

* **Contabilidade e Impostos**:

  * Gestão do razão geral, contas a pagar/receber, multi-moeda.
  * Geração de relatórios (balanço, DRE, fluxo de caixa).
  * **Templates de imposto**:

    * IVA 16% (nacional) sobre produtos e serviços padrão.
    * IVA 5% (taxa reduzida) para setores como saúde e educação.
    * IVA 0% para exportações e bens/serviços isentos.
    * Possibilidade de criar categorias fiscais isentas com menção legal na fatura.
  * Configuração de **retenções na fonte** e **impostos especiais** (bebidas alcoólicas, tabaco, etc.) caso aplicável.

* **Vendas e Faturação**:

  * Campos customizados para NUIT, menções legais, série e numeração fiscal.
  * Formatos de impressão personalizáveis para incluir QR code, nº de certificação AT, assinatura digital.

* **RH e Folha de Pagamento**:

  * Estruturas salariais com **cálculo automático de INSS**:

    * Empregador: 4%
    * Empregado: 3%
  * **IRPS** progressivo: 10%, 15%, 20%, 25%, 32% conforme faixas de rendimento.
  * Regras para cálculo e reporte de **benefícios em espécie** (veículo, habitação, seguro, etc.) — avaliados em MZN e integrados no bruto para efeitos fiscais e contributivos.
  * Gestão de licenças segundo Lei 13/2023:

    * Maternidade: 90 dias (60 pagos pelo INSS).
    * Paternidade: 7 dias.
    * Férias: 30 dias após 1 ano de contrato; 12 dias no 1º ano.
  * Emissão de relatórios consolidados para cruzamento com AT/INSS via SAF-T.

* **Inventário e Compras**: Gestão de stock, rastreamento por lote/nº série, ordens de compra.

---

## 4. Estratégia de Localização e Customização

### 4.1 Mapeamento de Métodos de Customização

| Método              | Aplicação para Moçambique                                     | Vantagens / Desvantagens                      |
| ------------------- | ------------------------------------------------------------- | --------------------------------------------- |
| **Custom Apps**     | Encapsular lógica fiscal (SAF-T, integração AT, certificação) | Mantém core intacto; requer expertise Frappe  |
| **Custom Fields**   | NUIT, códigos fiscais, campos p/ benefícios em espécie        | Simples; não cobre lógica complexa            |
| **Server Scripts**  | Geração XML SAF-T, validação 3%, integração API               | Flexível; precisa de boa estrutura            |
| **Client Scripts**  | Validações em tempo real (ex.: NUIT válido)                   | Feedback rápido; não executa lógica crítica   |
| **Hooks**           | Executar envio à AT após submissão de fatura                  | Integração suave; exige conhecimento profundo |
| **Print Formats**   | Layout fiscal da fatura (QR code, nº certificação)            | Controle visual; não altera dados             |
| **API Integration** | Comunicação com sistemas da AT                                | Automação; depende de documentação AT         |

---

## 5. Integração com a Autoridade Tributária

* **Base técnica**: ERPNext é API-first; Frappe permite criar endpoints e consumir APIs externas.
* **Exemplos internacionais**:

  * *Índia*: e-faturação via API, geração IRN e QR code.
  * *Arábia Saudita*: integração ZATCA (CSID, clearance).
  * *Burundi*: app fiscal EBMS.
* **Para Moçambique**: Desenvolver *Custom App* que:

  * Gere XML SAF-T (vendas e folha) conforme especificações AT.
  * Envie faturas e folhas de pagamento via API ou exporte para upload no portal e-Declaração.
  * Implemente hashes/checksums para integridade.

---

## 6. Arquitetura de Hospedagem e Multi-Tenancy

**Cenário recomendado (AWS + Multi-site):**

* **Multi-tenancy por “site”** no mesmo *bench* (cada cliente com DB e arquivos isolados).
* Escalabilidade horizontal (novas instâncias em EC2 ou ECS).
* Backups automáticos (S3 + replicação em outra região).
* Monitoramento de performance (CloudWatch + métricas ERPNext).
* Atualizações centralizadas, mantendo custom app de localização compatível.

---

## 7. Modelo de Negócio SaaS

### 7.1 Proposta de Valor

* ERP pronto e certificado para Moçambique.
* Hospedagem segura na AWS, escalável e com backups.
* Sem custo de licença, preço baseado em **recursos e serviços**.
* Suporte local e atualização contínua conforme alterações fiscais.

### 7.2 Modelos de Preço

| Modelo                                     | Adequação                               | Potencial no Mercado                  |
| ------------------------------------------ | --------------------------------------- | ------------------------------------- |
| **Baseado em recursos** (CPU, DB, storage) | Alinha custo ao uso real                | Alto (PMEs e empresas em crescimento) |
| **Por nível** (Básico, Pro, Premium)       | Diferencia por módulos e SLA            | Alto (segmentação clara)              |
| **Freemium**                               | Atrai volume, upsell p/ versão completa | Médio (boa para marketing inicial)    |
| **Por uso** (transações SAF-T)             | Complementar a outro modelo             | Médio (pode gerar custo imprevisível) |

---

## 8. Estratégia de Implementação

* **Custom App Moçambique**: plano de contas, regras de IVA, SAF-T vendas/folha, integração AT, cálculos de benefícios em espécie.
* **Certificação AT**: iniciar cedo para reduzir risco regulatório.
* **Equipa**: devs Frappe/Python, especialista fiscal, suporte.
* **Gestão da mudança**: identificar *Project Champions* nos clientes, oferecer formação e suporte contínuo.
* **Serviços adicionais**: migração de dados, integração com bancos/gateways locais, relatórios executivos.

---

## 9. Conclusão

O ERPNext, quando localizado para Moçambique, oferece uma plataforma robusta, de baixo custo de entrada e escalável para conformidade fiscal em 2025. A oportunidade reside em **unir tecnologia, conhecimento fiscal e um modelo SaaS adaptado**, garantindo que empresas cumpram requisitos cada vez mais exigentes sem penalizar produtividade ou orçamento.

Com a arquitetura multi-tenant na AWS, *Custom App* certificado e um modelo de preços justo, a proposta pode ser não só competitiva, mas líder no segmento de ERPs cloud para PMEs e médias empresas no país.