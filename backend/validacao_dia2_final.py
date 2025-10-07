"""
Validação Final do Dia 2 - WEX Intelligence
Teste automatizado de todas as funcionalidades implementadas no Dia 2
"""

import requests
import json
import time
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def testar_servidor_ativo():
    """Testa se o servidor está respondendo"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        print(f"✅ Servidor ativo - Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Servidor não responde: {e}")
        return False

def testar_api_chamados():
    """Testa a API de chamados com paginação"""
    try:
        # Teste básico
        response = requests.get(f"{BASE_URL}/chamados", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Chamados - Total: {len(data.get('chamados', []))}")
            
            # Teste com paginação
            response_pag = requests.get(f"{BASE_URL}/chamados?skip=0&limit=5", timeout=TIMEOUT)
            if response_pag.status_code == 200:
                data_pag = response_pag.json()
                print(f"✅ Paginação - Chamados retornados: {len(data_pag.get('chamados', []))}")
            
            return True
        else:
            print(f"❌ API Chamados falhou - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na API Chamados: {e}")
        return False

def testar_busca_avancada():
    """Testa funcionalidade de busca avançada"""
    try:
        # Teste de busca básica
        response = requests.get(f"{BASE_URL}/chamados?busca_texto=sistema", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Busca textual - Resultados: {len(data.get('chamados', []))}")
            return True
        else:
            print(f"❌ Busca falhou - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return False

def testar_filtros():
    """Testa filtros por status e criticidade"""
    try:
        # Teste filtro por status
        response = requests.get(f"{BASE_URL}/chamados?status=aberto", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtro Status - Chamados abertos: {len(data.get('chamados', []))}")
            
            # Teste filtro por criticidade
            response_crit = requests.get(f"{BASE_URL}/chamados?criticidade=alta", timeout=TIMEOUT)
            if response_crit.status_code == 200:
                data_crit = response_crit.json()
                print(f"✅ Filtro Criticidade - Chamados alta: {len(data_crit.get('chamados', []))}")
            
            return True
        else:
            print(f"❌ Filtros falharam - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro nos filtros: {e}")
        return False

def testar_detalhes_chamado():
    """Testa endpoint de detalhes do chamado"""
    try:
        # Primeiro pega lista de chamados
        response = requests.get(f"{BASE_URL}/chamados?limit=1", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            chamados = data.get('chamados', [])
            if chamados:
                chamado_id = chamados[0]['id']
                
                # Testa detalhes
                response_det = requests.get(f"{BASE_URL}/chamados/{chamado_id}", timeout=TIMEOUT)
                if response_det.status_code == 200:
                    chamado = response_det.json()
                    print(f"✅ Detalhes Chamado - ID: {chamado.get('id')} Score: {chamado.get('score_qualidade')}")
                    return True
                else:
                    print(f"❌ Detalhes falhou - Status: {response_det.status_code}")
                    return False
            else:
                print("❌ Nenhum chamado encontrado para testar detalhes")
                return False
        else:
            print(f"❌ Falha ao buscar chamados - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro nos detalhes: {e}")
        return False

def validar_interface_web():
    """Valida se a interface web carrega corretamente"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            html_content = response.text
            
            # Verifica elementos importantes
            elementos = [
                'WEX Intelligence',
                'filtroStatus',
                'filtroCriticidade', 
                'filtroBusca',
                'chamadosTableBody',
                'modalChamado',
                'pagination-container',
                'anexos-section',
                'search-highlight'
            ]
            
            elementos_encontrados = 0
            for elemento in elementos:
                if elemento in html_content:
                    elementos_encontrados += 1
                    print(f"✅ Interface - {elemento} presente")
                else:
                    print(f"❌ Interface - {elemento} ausente")
            
            print(f"✅ Interface Web - {elementos_encontrados}/{len(elementos)} elementos encontrados")
            return elementos_encontrados >= len(elementos) * 0.8  # 80% dos elementos devem estar presentes
        else:
            print(f"❌ Interface falhou - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na interface: {e}")
        return False

def main():
    """Executa validação completa"""
    print("="*60)
    print("VALIDAÇÃO FINAL DO DIA 2 - WEX INTELLIGENCE")
    print("="*60)
    print(f"Iniciando validação em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    resultados = []
    
    # Testes
    print("1. TESTANDO CONECTIVIDADE...")
    resultados.append(testar_servidor_ativo())
    
    print("\n2. TESTANDO API DE CHAMADOS...")
    resultados.append(testar_api_chamados())
    
    print("\n3. TESTANDO BUSCA AVANÇADA...")
    resultados.append(testar_busca_avancada())
    
    print("\n4. TESTANDO FILTROS...")
    resultados.append(testar_filtros())
    
    print("\n5. TESTANDO DETALHES CHAMADO...")
    resultados.append(testar_detalhes_chamado())
    
    print("\n6. TESTANDO INTERFACE WEB...")
    resultados.append(validar_interface_web())
    
    # Resultado final
    print("\n" + "="*60)
    print("RESULTADO FINAL")
    print("="*60)
    
    sucessos = sum(resultados)
    total = len(resultados)
    percentual = (sucessos / total) * 100
    
    print(f"Testes bem-sucedidos: {sucessos}/{total}")
    print(f"Taxa de sucesso: {percentual:.1f}%")
    
    if percentual >= 80:
        print("🎉 VALIDAÇÃO APROVADA - Sistema funcionando corretamente!")
        status = "APROVADO"
    else:
        print("⚠️  VALIDAÇÃO REPROVADA - Existem problemas que precisam ser corrigidos")
        status = "REPROVADO"
    
    print(f"\nValidação concluída em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Salvar resultado
    resultado_final = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "sucessos": sucessos,
        "total": total,
        "percentual": percentual,
        "detalhes": resultados
    }
    
    with open("validacao_dia2_resultado.json", "w") as f:
        json.dump(resultado_final, f, indent=2)
    
    print("\n✅ Resultado salvo em: validacao_dia2_resultado.json")
    
    return status == "APROVADO"

if __name__ == "__main__":
    main()