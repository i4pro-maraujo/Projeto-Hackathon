"""
Teste simples do módulo WEX AI Engine
Verifica se as funcionalidades de IA estão funcionando corretamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wex_ai_engine import wex_ai
from datetime import datetime

def test_triagem_automatica():
    """Testa a funcionalidade de triagem automática"""
    print("=== Teste de Triagem Automática ===")
    
    # Chamado de exemplo
    chamado_teste = {
        'id': 'TEST001',
        'titulo': 'Sistema WEX não carrega relatórios',
        'descricao': 'O sistema WEX está apresentando erro 500 ao tentar carregar os relatórios financeiros. O problema ocorre desde ontem às 14h. Usuários não conseguem acessar os dados.',
        'cliente_solicitante': 'Empresa ABC',
        'anexos_count': 2
    }
    
    try:
        resultado = wex_ai.realizar_triagem(chamado_teste)
        print(f"✅ Triagem realizada com sucesso!")
        print(f"Score total: {resultado.score_total}")
        print(f"Decisão: {resultado.decisao}")
        print(f"Motivos: {resultado.motivos}")
        print(f"Sugestões: {resultado.sugestoes}")
        print(f"Tags sugeridas: {resultado.tags_sugeridas}")
        print(f"Criticidade: {resultado.criticidade_sugerida}")
        print(f"Confiança: {resultado.confianca}")
        return True
    except Exception as e:
        print(f"❌ Erro na triagem: {e}")
        return False

def test_sugestoes_followup():
    """Testa a geração de sugestões de follow-up"""
    print("\n=== Teste de Sugestões de Follow-up ===")
    
    # Chamado de exemplo
    chamado_teste = {
        'id': 'TEST002',
        'titulo': 'Erro de conexão com banco de dados',
        'descricao': 'Sistema perdendo conexão com banco MySQL. Erro intermitente que afeta módulo de vendas.',
        'cliente_solicitante': 'Empresa XYZ',
        'status': 'Em Andamento'
    }
    
    try:
        sugestoes = wex_ai.gerar_sugestoes_followup(chamado_teste)
        print(f"✅ Sugestões geradas com sucesso!")
        print(f"Total de sugestões: {len(sugestoes)}")
        
        for i, sugestao in enumerate(sugestoes[:3], 1):  # Mostrar apenas as 3 primeiras
            print(f"\nSugestão {i}:")
            print(f"  Título: {sugestao.titulo}")
            print(f"  Tipo: {sugestao.tipo}")
            print(f"  Confiança: {sugestao.confianca}")
            print(f"  Motivo: {sugestao.motivo}")
        
        return True
    except Exception as e:
        print(f"❌ Erro nas sugestões: {e}")
        return False

def test_verificacao_dependencias():
    """Verifica se as dependências estão instaladas"""
    print("\n=== Verificação de Dependências ===")
    
    try:
        import sklearn
        print("✅ scikit-learn disponível")
        
        import numpy
        print("✅ numpy disponível")
        
        import requests
        print("✅ requests disponível")
        
        print("✅ Todas as dependências básicas estão disponíveis")
        return True
        
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🤖 Iniciando testes do WEX AI Engine...")
    print("=" * 50)
    
    testes_passaram = []
    
    # Verificar dependências
    testes_passaram.append(test_verificacao_dependencias())
    
    # Teste de triagem
    testes_passaram.append(test_triagem_automatica())
    
    # Teste de sugestões
    testes_passaram.append(test_sugestoes_followup())
    
    print("\n" + "=" * 50)
    print("📊 Resultados dos Testes:")
    print(f"✅ Testes que passaram: {sum(testes_passaram)}")
    print(f"❌ Testes que falharam: {len(testes_passaram) - sum(testes_passaram)}")
    
    if all(testes_passaram):
        print("\n🎉 Todos os testes passaram! O módulo AI está funcionando.")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique a configuração.")
    
    print("\n💡 Nota: Para funcionalidade completa da IA, certifique-se de que:")
    print("   - As dependências estão instaladas (pip install -r requirements.txt)")
    print("   - A chave da Hugging Face está configurada corretamente")
    print("   - A conexão com internet está disponível para APIs externas")

if __name__ == "__main__":
    main()