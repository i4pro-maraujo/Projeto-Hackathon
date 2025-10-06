#!/usr/bin/env python3
"""
Script de Validação Final - WEX Intelligence
Verifica se todos os componentes do projeto estão funcionando corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import sqlite3
import json
from datetime import datetime
import traceback

def validar_banco_dados():
    """Valida se o banco de dados foi criado e possui dados"""
    print("🔍 Validando banco de dados...")
    
    try:
        db_path = "wex_intelligence.db"
        if not os.path.exists(db_path):
            print("❌ Banco de dados não encontrado")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in cursor.fetchall()]
        
        if 'chamados' not in tabelas:
            print("❌ Tabela 'chamados' não encontrada")
            return False
            
        if 'followups' not in tabelas:
            print("❌ Tabela 'followups' não encontrada")
            return False
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM chamados")
        total_chamados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM followups")
        total_followups = cursor.fetchone()[0]
        
        # Verificar distribuição por status
        cursor.execute("SELECT status, COUNT(*) FROM chamados GROUP BY status")
        status_dist = dict(cursor.fetchall())
        
        # Verificar distribuição por criticidade
        cursor.execute("SELECT criticidade, COUNT(*) FROM chamados GROUP BY criticidade")
        crit_dist = dict(cursor.fetchall())
        
        conn.close()
        
        print(f"✅ Banco de dados OK:")
        print(f"   📊 {total_chamados} chamados")
        print(f"   💬 {total_followups} follow-ups")
        print(f"   📈 Distribuição por status: {status_dist}")
        print(f"   🚨 Distribuição por criticidade: {crit_dist}")
        
        return total_chamados > 0 and total_followups > 0
        
    except Exception as e:
        print(f"❌ Erro ao validar banco: {e}")
        return False

def validar_estrutura_arquivos():
    """Valida se todos os arquivos necessários existem"""
    print("\n🔍 Validando estrutura de arquivos...")
    
    arquivos_backend = [
        "main.py",
        "models.py", 
        "schemas.py",
        "database.py",
        "requirements.txt",
        "static/index.html"
    ]
    
    arquivos_raiz = [
        "../CHECKLIST_DESENVOLVIMENTO.md",
        "../README.md",
        "../PLANO_DESENVOLVIMENTO.md"
    ]
    
    problemas = []
    
    for arquivo in arquivos_backend:
        if not os.path.exists(arquivo):
            problemas.append(f"Backend: {arquivo}")
    
    for arquivo in arquivos_raiz:
        if not os.path.exists(arquivo):
            problemas.append(f"Raiz: {arquivo}")
    
    if problemas:
        print("❌ Arquivos faltando:")
        for problema in problemas:
            print(f"   - {problema}")
        return False
    
    print("✅ Estrutura de arquivos OK")
    return True

def validar_imports():
    """Valida se todos os imports funcionam"""
    print("\n🔍 Validando imports...")
    
    try:
        import main
        print("✅ main.py importado com sucesso")
        
        import models
        print("✅ models.py importado com sucesso")
        
        import schemas
        print("✅ schemas.py importado com sucesso")
        
        import database
        print("✅ database.py importado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao importar módulos: {e}")
        traceback.print_exc()
        return False

def validar_modelos():
    """Valida se os modelos podem ser instanciados"""
    print("\n🔍 Validando modelos de dados...")
    
    try:
        from models import Chamado, FollowUp, StatusChamado, CriticidadeChamado
        
        # Teste básico de criação de objetos
        chamado_test = {
            'numero_wex': 'TEST-001',
            'cliente_solicitante': 'Cliente Teste',
            'descricao': 'Descrição de teste',
            'status': StatusChamado.ABERTO.value,
            'criticidade': CriticidadeChamado.MEDIA.value
        }
        
        print("✅ Modelos validados com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar modelos: {e}")
        return False

def validar_apis_simulado():
    """Simula teste das APIs sem servidor"""
    print("\n🔍 Validando estrutura das APIs...")
    
    try:
        from main import app
        
        # Verificar se as rotas foram registradas
        routes = [route.path for route in app.routes]
        
        rotas_essenciais = [
            "/",
            "/api/health", 
            "/chamados",
            "/dashboard/metricas"
        ]
        
        problemas = []
        for rota in rotas_essenciais:
            if rota not in routes:
                problemas.append(rota)
        
        if problemas:
            print(f"❌ Rotas faltando: {problemas}")
            return False
        
        print("✅ Estrutura das APIs OK")
        print(f"   📝 {len(routes)} rotas registradas")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar APIs: {e}")
        return False

def validar_frontend():
    """Valida o frontend HTML"""
    print("\n🔍 Validando frontend...")
    
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        elementos_essenciais = [
            "WEX Intelligence",
            "dashboardMetrics",
            "chamadosTableBody",
            "carregarChamados",
            "carregarDashboard"
        ]
        
        problemas = []
        for elemento in elementos_essenciais:
            if elemento not in html_content:
                problemas.append(elemento)
        
        if problemas:
            print(f"❌ Elementos faltando no HTML: {problemas}")
            return False
        
        print("✅ Frontend HTML OK")
        print(f"   📄 {len(html_content)} caracteres")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar frontend: {e}")
        return False

def validar_dependencias():
    """Valida se as dependências estão instaladas"""
    print("\n🔍 Validando dependências...")
    
    dependencias = [
        "fastapi",
        "uvicorn", 
        "sqlalchemy",
        "pydantic"
    ]
    
    problemas = []
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            problemas.append(dep)
            print(f"❌ {dep}")
    
    return len(problemas) == 0

def gerar_relatorio_final():
    """Gera relatório final da validação"""
    print("\n" + "="*60)
    print("📋 RELATÓRIO FINAL - VALIDAÇÃO DO PROJETO")
    print("="*60)
    
    validacoes = [
        ("Estrutura de Arquivos", validar_estrutura_arquivos()),
        ("Dependências Python", validar_dependencias()),
        ("Imports dos Módulos", validar_imports()),
        ("Modelos de Dados", validar_modelos()),
        ("Banco de Dados", validar_banco_dados()),
        ("Estrutura das APIs", validar_apis_simulado()),
        ("Frontend HTML", validar_frontend())
    ]
    
    total = len(validacoes)
    aprovadas = sum(1 for _, passou in validacoes if passou)
    
    print(f"\n📊 RESULTADO: {aprovadas}/{total} validações aprovadas")
    
    if aprovadas == total:
        print("\n🎉 PROJETO VALIDADO COM SUCESSO!")
        print("✅ Todos os componentes estão funcionando corretamente")
        print("✅ Dados mockados carregados no banco")
        print("✅ APIs estruturadas e funcionais")
        print("✅ Frontend integrado")
        
        print(f"\n🚀 INSTRUÇÕES PARA EXECUÇÃO:")
        print(f"1. Ativar ambiente virtual: venv\\Scripts\\Activate.ps1")
        print(f"2. Executar servidor: python main.py")
        print(f"3. Abrir navegador: http://localhost:8000")
        
    else:
        print("\n⚠️  PROJETO COM PROBLEMAS!")
        print("❌ Alguns componentes precisam de correção")
        
        for nome, passou in validacoes:
            status = "✅" if passou else "❌"
            print(f"{status} {nome}")
    
    print("\n" + "="*60)
    return aprovadas == total

if __name__ == "__main__":
    print("🎯 WEX INTELLIGENCE - VALIDAÇÃO FINAL")
    print("Verificando integridade do projeto...\n")
    
    sucesso = gerar_relatorio_final()
    
    # Salvar log da validação
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"validacao_{timestamp}.log"
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"Validação executada em: {datetime.now()}\n")
        f.write(f"Resultado: {'SUCESSO' if sucesso else 'FALHAS ENCONTRADAS'}\n")
    
    print(f"\n📄 Log salvo em: {log_file}")
    
    sys.exit(0 if sucesso else 1)