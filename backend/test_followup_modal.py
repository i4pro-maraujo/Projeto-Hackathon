#!/usr/bin/env python3
"""
Teste para validar a funcionalidade do modal de follow-up
"""

import requests
import json

def test_followup_creation():
    """Testa a criação de follow-up via API"""
    
    base_url = "http://localhost:8000"
    
    # Dados do follow-up para teste
    followup_data = {
        "tipo": "Publicação",
        "descricao": "Este é um follow-up de teste criado via API para validar a funcionalidade",
        "autor": "Sistema de Teste"
    }
    
    # ID do chamado para teste (vamos usar o chamado 1)
    chamado_id = 1
    
    try:
        # Fazer requisição POST para criar follow-up
        response = requests.post(
            f"{base_url}/chamados/{chamado_id}/followups",
            json=followup_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ Follow-up criado com sucesso!")
            return True
        else:
            print("❌ Erro ao criar follow-up")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_get_followups():
    """Testa a busca de follow-ups de um chamado"""
    
    base_url = "http://localhost:8000"
    chamado_id = 1
    
    try:
        response = requests.get(f"{base_url}/chamados/{chamado_id}/followups")
        
        print(f"\n=== Follow-ups do Chamado {chamado_id} ===")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            followups = response.json()
            print(f"Total de follow-ups: {len(followups)}")
            
            for i, followup in enumerate(followups, 1):
                print(f"\nFollow-up {i}:")
                print(f"  Tipo: {followup.get('tipo', 'N/A')}")
                print(f"  Descrição: {followup.get('descricao', 'N/A')[:50]}...")
                print(f"  Autor: {followup.get('autor', 'N/A')}")
                print(f"  Data: {followup.get('data_criacao', 'N/A')}")
                
            return True
        else:
            print("❌ Erro ao buscar follow-ups")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testando funcionalidade de Follow-up\n")
    
    # Primeiro, vamos ver os follow-ups existentes
    print("1. Verificando follow-ups existentes:")
    test_get_followups()
    
    print("\n" + "="*50)
    
    # Agora vamos criar um novo follow-up
    print("2. Criando novo follow-up:")
    success = test_followup_creation()
    
    if success:
        print("\n" + "="*50)
        print("3. Verificando follow-ups após criação:")
        test_get_followups()
    
    print("\n🏁 Teste concluído!")