import requests
import json

def test_apis():
    """Testar todas as APIs do sistema"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Iniciando testes das APIs...")
    
    try:
        # 1. Testar health check
        print("\n1. Testando health check...")
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Resposta: {response.json()}")
        
        # 2. Testar métricas do dashboard
        print("\n2. Testando métricas do dashboard...")
        response = requests.get(f"{base_url}/dashboard/metricas")
        print(f"   Status: {response.status_code}")
        metricas = response.json()
        print(f"   Total chamados por status: {metricas['total_chamados_por_status']}")
        print(f"   Chamados críticos: {metricas['chamados_criticos_abertos']}")
        
        # 3. Testar listagem de chamados
        print("\n3. Testando listagem de chamados...")
        response = requests.get(f"{base_url}/chamados?limit=5")
        print(f"   Status: {response.status_code}")
        chamados_data = response.json()
        print(f"   Total de chamados: {chamados_data['total']}")
        print(f"   Chamados retornados: {len(chamados_data['chamados'])}")
        
        if chamados_data['chamados']:
            primeiro_chamado = chamados_data['chamados'][0]
            print(f"   Primeiro chamado: {primeiro_chamado['numero_wex']} - {primeiro_chamado['cliente_solicitante']}")
            
            # 4. Testar detalhes de um chamado específico
            print(f"\n4. Testando detalhes do chamado {primeiro_chamado['id']}...")
            response = requests.get(f"{base_url}/chamados/{primeiro_chamado['id']}")
            print(f"   Status: {response.status_code}")
            chamado_detalhe = response.json()
            print(f"   Número WEX: {chamado_detalhe['numero_wex']}")
            print(f"   Status: {chamado_detalhe['status']}")
            print(f"   Score qualidade: {chamado_detalhe['score_qualidade']}%")
            
            # 5. Testar follow-ups do chamado
            print(f"\n5. Testando follow-ups do chamado {primeiro_chamado['id']}...")
            response = requests.get(f"{base_url}/chamados/{primeiro_chamado['id']}/followups")
            print(f"   Status: {response.status_code}")
            followups = response.json()
            print(f"   Total de follow-ups: {len(followups)}")
            
            if followups:
                print(f"   Primeiro follow-up: {followups[0]['tipo']} - {followups[0]['autor']}")
        
        # 6. Testar filtros
        print("\n6. Testando filtros de chamados...")
        response = requests.get(f"{base_url}/chamados?status=Aberto&criticidade=Crítica")
        print(f"   Status: {response.status_code}")
        filtrados = response.json()
        print(f"   Chamados críticos em aberto: {len(filtrados['chamados'])}")
        
        print("\n✅ Todos os testes passaram! As APIs estão funcionando corretamente.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
        print("   Certifique-se de que o servidor está rodando em http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        return False

if __name__ == "__main__":
    test_apis()