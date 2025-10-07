# 🚀 WEX Intelligence - Instruções de Execução (Atualizado)

## 📡 **Nova Configuração de Portas**

A partir de agora, o sistema roda em **duas portas separadas** para evitar conflitos:

### **🎯 Configuração Atual:**
- **📡 Backend API**: `http://localhost:8000` (apenas APIs)
- **🌐 Interface Frontend**: `http://localhost:3000` (interface HTML)
- **📚 Documentação**: `http://localhost:8000/docs`

---

## 🔧 **Como Executar o Sistema**

### **⚡ Opção 1: Scripts Automatizados (Recomendado)**

#### **1️⃣ Iniciar Backend API (Terminal 1)**
```bash
# Windows CMD
.\backend\start_server.bat

# Windows PowerShell  
.\backend\start_server.ps1
```

#### **2️⃣ Iniciar Interface Frontend (Terminal 2)**
```bash
# Windows CMD
.\backend\start_frontend.bat

# Windows PowerShell
.\backend\start_frontend.ps1
```

### **⚡ Opção 2: Execução Manual**

#### **1️⃣ Backend API (Terminal 1)**
```bash
cd backend
venv\Scripts\activate
python start_backend_api.py
```

#### **2️⃣ Interface Frontend (Terminal 2)**
```bash
cd backend  
venv\Scripts\activate
python start_frontend_server.py
```

### **⚡ Opção 3: Uso Individual**

#### **Apenas APIs (para desenvolvimento/testes)**
```bash
cd backend
python start_backend_api.py
# Acesse: http://localhost:8000/docs
```

#### **Apenas Interface (conecta às APIs automaticamente)**
```bash
cd backend
python start_frontend_server.py
# Acesse: http://localhost:3000
```

---

## 🌐 **Acessos do Sistema**

### **Interface Principal**
- **🖥️ Interface Web**: http://localhost:3000
- **📊 Dashboard completo, listagem de chamados, módulos de IA**

### **Backend API**
- **📡 Health Check**: http://localhost:8000/
- **📚 Documentação Swagger**: http://localhost:8000/docs
- **🔍 Teste de APIs**: http://localhost:8000/redoc

### **Principais Endpoints**
- `GET /chamados` - Listar chamados
- `GET /chamados/{id}` - Detalhes do chamado
- `GET /dashboard/metricas` - Métricas do dashboard
- `POST /chamados/{id}/followups` - Criar follow-up
- `GET /api/chamados/{id}/triagem` - IA Triagem
- `GET /api/chamados/{id}/sugestoes-followup` - IA Sugestões

---

## ✅ **Benefícios da Nova Configuração**

### **🚀 Performance**
- **APIs otimizadas**: Backend focado apenas em servir dados
- **Interface rápida**: Servidor HTTP simples para arquivos estáticos
- **Sem conflitos**: Ambos rodam simultaneamente sem interferência

### **🔧 Desenvolvimento**
- **Independência**: Cada serviço pode ser reiniciado separadamente
- **Debug facilitado**: Logs separados para API e Interface
- **Flexibilidade**: Pode usar apenas APIs ou apenas Interface

### **🛡️ Segurança**
- **Separação de responsabilidades**: API e Interface isoladas
- **CORS configurado**: Comunicação segura entre as portas
- **Controle granular**: Diferentes configurações por serviço

---

## 🔍 **Status dos Serviços**

### **✅ Quando tudo está funcionando:**
```
🚀 Backend API: http://localhost:8000 (rodando)
🌐 Interface: http://localhost:3000 (rodando)
📡 Comunicação: Interface → API (funcionando)
```

### **❌ Solução de Problemas:**

#### **Porta 8000 em uso:**
```bash
# Verificar processo
netstat -ano | findstr :8000
# Finalizar processo se necessário
taskkill /PID <PID_NUMBER> /F
```

#### **Porta 3000 em uso:**
```bash
# Verificar processo
netstat -ano | findstr :3000
# Finalizar processo se necessário
taskkill /PID <PID_NUMBER> /F
```

#### **Erro de CORS:**
- Verifique se ambos os serviços estão rodando
- Confirme que as URLs estão corretas nos logs

---

## 📁 **Arquivos de Configuração**

### **Criados/Atualizados:**
- `backend/start_backend_api.py` - Servidor API dedicado
- `backend/start_frontend_server.py` - Servidor Interface dedicado  
- `backend/start_server.bat` - Script Windows para API
- `backend/start_frontend.bat` - Script Windows para Interface
- `backend/start_server.ps1` - Script PowerShell para API
- `backend/start_frontend.ps1` - Script PowerShell para Interface

### **Modificados:**
- `backend/main.py` - Removido servimento de arquivos estáticos
- Interface HTML - Mantém `API_BASE = 'http://localhost:8000'`

---

## 🎯 **Próximos Passos**

### **Para desenvolvimento contínuo:**
1. **Sempre iniciar ambos os serviços** para funcionalidade completa
2. **Usar http://localhost:3000** para interface principal
3. **Usar http://localhost:8000/docs** para testar APIs
4. **Verificar logs separados** em cada terminal

### **Para deploy em produção:**
- **API**: Configurar servidor ASGI (Gunicorn/Uvicorn)
- **Interface**: Servir via Nginx ou servidor web dedicado
- **Proxy reverso**: Configurar roteamento único se necessário

---

**Status:** 🎉 **CONFIGURAÇÃO DE PORTAS IMPLEMENTADA COM SUCESSO!**  
**Data:** 07 de Outubro de 2025  
**Benefício:** Ambos os serviços rodam simultaneamente sem conflitos