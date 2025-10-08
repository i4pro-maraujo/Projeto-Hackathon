"""
Script para testar todos os endpoints de IA da aplicação WEX Intelligence
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_triagem_automatica():
    """Teste do endpoint de triagem automática"""
    print("🧪 Testando Triagem Automática...")
    
    # Primeiro, buscar um chamado existente para testar triagem
    try:
        response = requests.get(f"http://localhost:8000/chamados?limit=1", timeout=10)
        if response.status_code != 200:
            print("❌ Não foi possível buscar chamados")
            return False
            
        data = response.json()
        chamados = data.get('chamados', [])
        if not chamados:
            print("❌ Nenhum chamado encontrado")
            return False
            
        chamado_id = chamados[0]['id']
        
        # Testar triagem
        response = requests.post(f"{BASE_URL}/chamados/{chamado_id}/triagem", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Score: {data.get('score_total', 'N/A')}")
            print(f"✅ Decisão: {data.get('decisao', 'N/A')}")
            print(f"✅ Confiança: {data.get('confianca', 'N/A')}")
            print(f"✅ IA funcionando: {'metadados_ia' in data}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_sugestoes_followup():
    """Teste do endpoint de sugestões de follow-up"""
    print("\n🧪 Testando Sugestões de Follow-up...")
    
    # Primeiro, buscar um chamado existente
    try:
        response = requests.get(f"http://localhost:8000/chamados?limit=1", timeout=10)
        if response.status_code != 200:
            print("❌ Não foi possível buscar chamados")
            return False
            
        data = response.json()
        chamados = data.get('chamados', [])
        if not chamados:
            print("❌ Nenhum chamado encontrado")
            return False
            
        chamado_id = chamados[0]['id']
        
        # Testar sugestões
        response = requests.get(f"{BASE_URL}/chamados/{chamado_id}/sugestoes-followup", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sugestões geradas: {len(data.get('sugestoes', []))}")
            print(f"✅ IA funcionando: {'metadados_ia' in data}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_chamados_relacionados():
    """Teste do endpoint de chamados relacionados"""
    print("\n🧪 Testando Chamados Relacionados...")
    
    try:
        # Buscar um chamado para teste
        response = requests.get(f"http://localhost:8000/chamados?limit=1", timeout=10)
        if response.status_code != 200:
            print("❌ Não foi possível buscar chamados")
            return False
            
        data = response.json()
        chamados = data.get('chamados', [])
        if not chamados:
            print("❌ Nenhum chamado encontrado")
            return False
            
        chamado_id = chamados[0]['id']
        
        # Testar similaridade
        response = requests.get(f"{BASE_URL}/chamados/{chamado_id}/relacionados", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chamados similares: {data.get('total_encontrados', 0)}")
            print(f"✅ IA funcionando: {'metadados_ia' in data}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_relatorios_padroes():
    """Teste do endpoint de relatórios de padrões"""
    print("\n🧪 Testando Relatórios de Padrões...")
    
    try:
        response = requests.get(f"{BASE_URL}/relatorios/padroes-ia?dias=30", timeout=15)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total chamados: {data.get('total_chamados', 0)}")
            print(f"✅ Grupos similares: {data.get('total_grupos_similares', 0)}")
            print(f"✅ IA funcionando: {'metadados_ia' in data}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def main():
    print("🚀 Testando funcionalidades de IA da WEX Intelligence")
    print("=" * 60)
    
    # Aguardar servidor estar pronto
    print("⏳ Aguardando servidor estar pronto...")
    time.sleep(2)
    
    testes_passaram = []
    
    # Executar testes
    testes_passaram.append(test_triagem_automatica())
    testes_passaram.append(test_sugestoes_followup())
    testes_passaram.append(test_chamados_relacionados())
    testes_passaram.append(test_relatorios_padroes())
    
    # Resultados
    print("\n" + "=" * 60)
    print("📊 Resultados dos Testes de IA:")
    print(f"✅ Testes que passaram: {sum(testes_passaram)}")
    print(f"❌ Testes que falharam: {len(testes_passaram) - sum(testes_passaram)}")
    
    if all(testes_passaram):
        print("\n🎉 Todos os endpoints de IA estão funcionando!")
    else:
        print("\n⚠️  Alguns endpoints de IA não estão funcionando corretamente.")
    
    print("\n💡 Lembre-se de verificar:")
    print("   - Backend rodando em http://localhost:8000")
    print("   - Dependências de IA instaladas")
    print("   - Módulo wex_ai_engine importado corretamente")

if __name__ == "__main__":
    main()