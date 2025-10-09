"""
Teste simples para verificar se o endpoint de triagem está funcionando
"""

import requests
import json

def test_triagem_endpoint():
    """Testa o endpoint de triagem para verificar o formato da resposta"""
    
    # URLs
    base_url = "http://localhost:8000"
    
    print("🧪 Testando endpoint de triagem automática")
    print("=" * 50)
    
    try:
        # 1. Primeiro, vamos listar os chamados para pegar um ID
        print("1. Buscando chamados disponíveis...")
        response = requests.get(f"{base_url}/chamados", params={"limit": 5})
        
        if response.status_code != 200:
            print(f"❌ Erro ao buscar chamados: {response.status_code}")
            return False
        
        chamados = response.json()
        if not chamados or len(chamados) == 0:
            print("❌ Nenhum chamado encontrado")
            return False
        
        chamado_id = chamados[0]['id']
        print(f"✅ Chamado encontrado: ID {chamado_id}")
        
        # 2. Testar triagem automática
        print(f"\n2. Testando triagem do chamado {chamado_id}...")
        response = requests.post(f"{base_url}/api/chamados/{chamado_id}/triagem")
        
        print(f"Status da resposta: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erro na triagem: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
        
        resultado = response.json()
        print("✅ Triagem executada com sucesso!")
        
        # 3. Verificar estrutura da resposta
        print("\n3. Verificando estrutura da resposta...")
        print(f"📊 Formato da resposta:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Verificar campos esperados pelo frontend
        campos_esperados = [
            'criticidade_atual',
            'criticidade_sugerida', 
            'confianca',
            'fatores_identificados',
            'sugestoes_melhoria',
            'tags_sugeridas',
            'score_total'
        ]
        
        print("\n4. Verificando campos necessários para o frontend...")
        for campo in campos_esperados:
            if campo in resultado:
                valor = resultado[campo]
                tipo = type(valor).__name__
                print(f"✅ {campo}: {tipo} = {valor}")
            else:
                print(f"❌ {campo}: AUSENTE")
        
        # Verificar se são arrays/listas
        print("\n5. Verificando se campos são arrays válidos...")
        arrays_esperados = ['fatores_identificados', 'sugestoes_melhoria', 'tags_sugeridas']
        
        for campo in arrays_esperados:
            if campo in resultado:
                valor = resultado[campo]
                if isinstance(valor, list):
                    print(f"✅ {campo}: Array com {len(valor)} itens")
                else:
                    print(f"⚠️ {campo}: Não é um array, é {type(valor).__name__}")
            else:
                print(f"❌ {campo}: AUSENTE")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        print("💡 Certifique-se de que o backend está rodando em http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Teste do Endpoint de Triagem - Diagnóstico de Erro Frontend")
    print("🎯 Objetivo: Verificar formato da resposta da API")
    print()
    
    success = test_triagem_endpoint()
    
    if success:
        print("\n🎉 Teste concluído! Verifique a estrutura da resposta acima.")
    else:
        print("\n⚠️ Teste falhou. Verifique se o backend está rodando.")
    
    print("\n💡 Após o teste, tente novamente a triagem no frontend.")