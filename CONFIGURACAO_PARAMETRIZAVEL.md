# 🔧 Sistema de Configuração Parametrizável - WEX Intelligence

## 📋 Visão Geral

O sistema WEX Intelligence agora possui um **sistema de configuração parametrizável** que permite ajustar todos os parâmetros da triagem automática sem modificar o código fonte. Todas as configurações estão centralizadas no arquivo `triagem_config.json`.

## 📁 Arquivos do Sistema

### **Principais:**
- `triagem_config.json` - **Arquivo de configuração principal**
- `config_manager.py` - **Gerenciador de configurações**
- `wex_ai_engine.py` - **Motor de IA (atualizado para usar configurações)**
- `test_config_sistema.py` - **Testes de validação**

---

## ⚙️ Configurações Disponíveis

### **1. Thresholds de Decisão**
```json
"thresholds": {
  "aprovacao_automatica": 70,    // Score >= 70: Aprovado automaticamente
  "revisao_humana": 50,          // Score 50-69: Necessita revisão humana
  "recusa_automatica": 49        // Score < 50: Recusado automaticamente
}
```

### **2. Pesos das Categorias**
```json
"pesos_categorias": {
  "anexos": 0.30,          // 30% do score total
  "descricao": 0.25,       // 25% do score total
  "info_tecnicas": 0.25,   // 25% do score total
  "contexto": 0.20         // 20% do score total
}
```
> **⚠️ IMPORTANTE:** A soma dos pesos deve ser **1.0** (100%)

### **3. Pontuação por Critério**

#### **Anexos (máximo 30 pontos):**
```json
"anexos": {
  "criterios": {
    "todos_obrigatorios_presentes": {"pontos": 20},
    "formato_correto": {"pontos": 5},
    "tamanho_adequado": {"pontos": 3},
    "nomes_descritivos": {"pontos": 2}
  }
}
```

#### **Descrição (máximo 25 pontos):**
```json
"descricao": {
  "criterios": {
    "clara_detalhada": {"pontos": 15},
    "palavras_chave_tecnicas": {"pontos": 5},
    "estrutura_organizada": {"pontos": 3},
    "ausencia_erros": {"pontos": 2}
  }
}
```

#### **Informações Técnicas (máximo 25 pontos):**
```json
"info_tecnicas": {
  "criterios": {
    "cliente_identificado": {"pontos": 10},
    "criticidade_apropriada": {"pontos": 5},
    "titulo_descritivo": {"pontos": 5},
    "data_hora_validas": {"pontos": 3},
    "numero_wex_correto": {"pontos": 2}
  }
}
```

#### **Contexto (máximo 20 pontos):**
```json
"contexto": {
  "criterios": {
    "problema_definido": {"pontos": 10},
    "impacto_mencionado": {"pontos": 5},
    "urgencia_justificada": {"pontos": 3},
    "tentativas_solucao": {"pontos": 2}
  }
}
```

### **4. Limites de Conteúdo**
```json
"limites_conteudo": {
  "min_descricao_chars": 50,
  "max_descricao_chars": 5000,
  "min_titulo_chars": 10,
  "max_titulo_chars": 200,
  "max_anexo_size_mb": 50
}
```

### **5. Palavras-Chave por Criticidade**
```json
"palavras_chave": {
  "criticidade_critica": ["sistema parado", "falha crítica", "emergência"],
  "criticidade_alta": ["erro grave", "sistema lento", "problema urgente"],
  "criticidade_media": ["erro menor", "problema intermitente"],
  "criticidade_baixa": ["dúvida", "melhoria", "consulta"]
}
```

---

## 🛠️ Como Usar

### **1. Modificar Configurações**

#### **Edição Manual:**
```bash
# Editar o arquivo diretamente
code backend/triagem_config.json
```

#### **Via Código Python:**
```python
from config_manager import get_config_manager

# Obter o gerenciador
config_manager = get_config_manager()

# Modificar um threshold
config_manager.config.thresholds['aprovacao_automatica'] = 75

# Salvar alterações
config_manager.save_config(backup=True)
```

### **2. Acessar Configurações no Código**

#### **Método Direto:**
```python
from config_manager import get_config_manager

config_manager = get_config_manager()
threshold = config_manager.get_threshold('aprovacao_automatica')  # Retorna 70
peso = config_manager.get_peso_categoria('anexos')  # Retorna 0.30
pontos = config_manager.get_pontuacao_criterio('anexos', 'todos_obrigatorios_presentes')  # Retorna 20
```

#### **Métodos de Conveniência:**
```python
from config_manager import get_threshold, get_peso_categoria, get_pontuacao_criterio

threshold = get_threshold('aprovacao_automatica')
peso = get_peso_categoria('anexos')
pontos = get_pontuacao_criterio('anexos', 'todos_obrigatorios_presentes')
```

### **3. Hot-Reload Automático**
O sistema possui **hot-reload automático**. Qualquer alteração no arquivo `triagem_config.json` é automaticamente detectada e aplicada sem necessidade de reiniciar a aplicação.

---

## 🔍 Funcionalidades Avançadas

### **1. Versionamento**
```json
"metadata": {
  "created": "2025-10-09",
  "updated": "2025-10-09 16:17:46",
  "description": "Configurações de pontuação da triagem automática",
  "schema_version": "1.0"
}
```

### **2. Backup Automático**
```python
# Salvar com backup automático
config_manager.save_config(backup=True)

# Arquivo de backup criado: triagem_config.backup_20251009_161746.json
```

### **3. Validação de Schema**
O sistema valida automaticamente:
- ✅ Presença de seções obrigatórias
- ✅ Tipos de dados corretos
- ✅ Soma dos pesos (deve ser ≈ 1.0)
- ✅ Valores de threshold válidos

### **4. Configurações Avançadas**
```json
"configuracoes_avancadas": {
  "deteccao_similaridade": {
    "threshold_similaridade": 0.70,
    "max_chamados_similares": 5
  },
  "timeouts": {
    "max_tempo_triagem_ms": 5000,
    "timeout_ia_ms": 3000
  }
}
```

---

## 🧪 Testes e Validação

### **Executar Testes Completos:**
```bash
cd backend
python test_config_sistema.py
```

### **Testes Inclusos:**
- ✅ **Carregamento de configurações**
- ✅ **Métodos de acesso**
- ✅ **Integração com IA**
- ✅ **Cálculo de scores**
- ✅ **Modificação de configurações**
- ✅ **Resumo das configurações**

---

## 📊 Exemplos Práticos

### **Cenário 1: Aumentar Exigência de Aprovação**
```json
// Para aprovar apenas chamados excelentes
"thresholds": {
  "aprovacao_automatica": 85,  // Era 70
  "revisao_humana": 60,        // Era 50
  "recusa_automatica": 59      // Era 49
}
```

### **Cenário 2: Valorizar Mais a Descrição**
```json
// Para dar mais importância à qualidade da descrição
"pesos_categorias": {
  "anexos": 0.20,        // Era 0.30
  "descricao": 0.40,     // Era 0.25 (+15%)
  "info_tecnicas": 0.25,
  "contexto": 0.15       // Era 0.20
}
```

### **Cenário 3: Ajustar Pontuação de Critérios**
```json
// Para valorizar mais a identificação do cliente
"info_tecnicas": {
  "criterios": {
    "cliente_identificado": {"pontos": 15},  // Era 10
    "criticidade_apropriada": {"pontos": 3}, // Era 5
    // ... outros critérios ajustados proporcionalmente
  }
}
```

---

## 🚨 Importantes

### **⚠️ Cuidados ao Modificar:**
1. **Sempre faça backup** antes de modificar configurações
2. **Valide a soma dos pesos** (deve ser 1.0)
3. **Teste após modificações** usando `test_config_sistema.py`
4. **Documente mudanças** importantes

### **🔧 Manutenção:**
- **Arquivo de configuração:** `backend/triagem_config.json`
- **Logs de carregamento:** Verifique logs para erros de validação
- **Backups:** Salvos automaticamente como `triagem_config.backup_*.json`

---

## 📈 Benefícios

### **✅ Flexibilidade:**
- Ajustar parâmetros sem modificar código
- Testar diferentes configurações rapidamente
- Reverter mudanças facilmente

### **✅ Manutenibilidade:**
- Configurações centralizadas
- Versionamento de configurações
- Backup automático

### **✅ Performance:**
- Hot-reload sem reinicialização
- Validação rápida de schema
- Cache inteligente de configurações

### **✅ Auditoria:**
- Histórico de mudanças via backups
- Validação automática de integridade
- Logs detalhados de carregamento

---

**📚 Para mais informações sobre a triagem automática, consulte o documento `Triagem.md`**

**🔄 Última atualização:** 09 de Outubro de 2025  
**✅ Status:** Sistema implementado e testado com sucesso