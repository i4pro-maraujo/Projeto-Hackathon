"""
Teste direto da API da Hugging Face para diagnosticar o problema 404
"""

import requests
import json

def test_huggingface_api():
    """Testa diferentes endpoints da Hugging Face"""
    
    # Chave da API
    api_key = "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"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    print("🔍 Testando API da Hugging Face...")
    print("=" * 50)
    
    # 1. Testar se o modelo existe no Hub
    print("1. Verificando se o modelo existe no Hub...")
    try:
        hub_url = "https://huggingface.co/microsoft/DialoGPT-medium"
        response = requests.get(hub_url, timeout=10)
        print(f"   Hub Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Modelo existe no Hub")
        else:
            print("   ❌ Modelo não encontrado no Hub")
    except Exception as e:
        print(f"   ❌ Erro ao acessar Hub: {e}")
    
    print("-" * 30)
    
    # 2. Testar endpoint da Inference API atual (que está dando erro)
    print("2. Testando endpoint atual (que está falhando)...")
    try:
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        payload = {"inputs": "Hello, how are you?"}
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 404:
            print("   ❌ Confirmado: 404 Not Found")
        elif response.status_code == 200:
            print("   ✅ API funcionando")
        else:
            print(f"   ⚠️ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro na chamada: {e}")
    
    print("-" * 30)
    
    # 3. Testar modelos alternativos mais adequados para análise de texto
    print("3. Testando modelos alternativos...")
    
    modelos_alternativos = [
        "cardiffnlp/twitter-roberta-base-sentiment-latest",  # Análise de sentimento
        "microsoft/DialoGPT-small",  # Versão menor do DialoGPT
        "distilbert-base-uncased",  # Modelo para classificação
        "nlptown/bert-base-multilingual-uncased-sentiment",  # Multilingual sentiment
    ]
    
    for modelo in modelos_alternativos:
        try:
            api_url = f"https://api-inference.huggingface.co/models/{modelo}"
            payload = {"inputs": "This is a technical support request about system errors."}
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            print(f"   {modelo}: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"      ✅ Funcionando! Response sample: {str(response.json())[:100]}...")
            elif response.status_code == 503:
                print("      ⏳ Modelo carregando...")
            elif response.status_code == 404:
                print("      ❌ Não encontrado")
            else:
                print(f"      ⚠️ Status: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Erro: {e}")
    
    print("-" * 30)
    
    # 4. Verificar informações da API key
    print("4. Verificando informações da API key...")
    try:
        # Endpoint para verificar status da API key
        whoami_url = "https://huggingface.co/api/whoami-v2"
        response = requests.get(whoami_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ API Key válida para: {user_info.get('name', 'N/A')}")
            print(f"   Tipo: {user_info.get('type', 'N/A')}")
        else:
            print("   ❌ API Key pode estar inválida")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("=" * 50)
    print("🏁 Teste concluído")

if __name__ == "__main__":
    test_huggingface_api()