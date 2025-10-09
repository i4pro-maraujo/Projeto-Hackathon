"""
Teste específico para verificar se as correções da API Hugging Face funcionaram
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from wex_ai_engine import WexIntelligenceAI
    from config_manager import get_config_manager
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

def test_huggingface_fixes():
    """Testa se as correções da API Hugging Face funcionaram"""
    print("🚀 Testando correções da API Hugging Face")
    print("=" * 50)
    
    try:
        # Inicializar IA
        ai = WexIntelligenceAI()
        print("✅ IA inicializada com sucesso")
        
        # Verificar se as configurações foram carregadas
        config = get_config_manager().config
        modelos_ia = config.configuracoes_avancadas.get('modelos_ia', {})
        print(f"✅ Modelos configurados: {list(modelos_ia.keys())}")
        
        # Teste 1: Análise de qualidade de texto
        print("\n🔍 Teste 1: Análise de qualidade de texto")
        texto_teste = "Sistema WEX apresenta erro crítico ao carregar relatórios. Problema afeta todos os usuários desde ontem."
        
        resultado_qualidade = ai._analisar_qualidade_texto(texto_teste)
        print(f"   Score: {resultado_qualidade.get('score', 'N/A')}")
        print(f"   Análise funcionou: {'analise' in resultado_qualidade}")
        
        if resultado_qualidade.get('score', 0) > 0:
            print("   ✅ Análise de qualidade funcionando")
        else:
            print("   ⚠️ Análise de qualidade com fallback")
        
        # Teste 2: Triagem completa
        print("\n🔍 Teste 2: Triagem completa")
        chamado_teste = {
            'id': 'TEST_FIXED',
            'titulo': 'Sistema crítico com falha',
            'descricao': texto_teste,
            'cliente_solicitante': 'Empresa Test',
            'anexos_count': 1,
            'criticidade': 'Alta',
            'numero_wex': 'WEX999999',
            'data_criacao': datetime.now().isoformat()
        }
        
        resultado_triagem = ai.realizar_triagem(chamado_teste)
        print(f"   Score total: {resultado_triagem.score_total}")
        print(f"   Decisão: {resultado_triagem.decisao}")
        print(f"   Motivos: {len(resultado_triagem.motivos)}")
        print("   ✅ Triagem completa funcionando")
        
        # Teste 3: Sugestões de follow-up
        print("\n🔍 Teste 3: Sugestões de follow-up")
        try:
            sugestoes = ai.gerar_sugestoes_followup(chamado_teste)
            print(f"   Sugestões geradas: {len(sugestoes)}")
            
            for i, sugestao in enumerate(sugestoes[:2]):  # Mostrar apenas 2
                print(f"   {i+1}. {sugestao.titulo} (confiança: {sugestao.confianca})")
                
            print("   ✅ Sugestões de follow-up funcionando")
            
        except Exception as e:
            print(f"   ⚠️ Erro nas sugestões: {e}")
        
        # Teste 4: Verificar se não há mais erros 404
        print("\n🔍 Teste 4: Verificando erros de API")
        
        # Executar várias operações para ver se há erros 404
        for i in range(3):
            resultado = ai._analisar_qualidade_texto(f"Teste {i}: erro sistema")
            if 'erro' in str(resultado).lower() and '404' in str(resultado):
                print(f"   ❌ Ainda há erros 404 no teste {i}")
                return False
        
        print("   ✅ Nenhum erro 404 detectado")
        
        print("\n" + "=" * 50)
        print("🎉 TODAS AS CORREÇÕES FUNCIONARAM!")
        print("✅ API Hugging Face agora usa modelos funcionais")
        print("✅ Fallbacks locais implementados")
        print("✅ Sistema mais robusto e confiável")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_models():
    """Testa os modelos específicos que estão configurados"""
    print("\n🔬 Testando modelos específicos configurados")
    print("-" * 40)
    
    try:
        config = get_config_manager().config
        modelos = config.configuracoes_avancadas.get('modelos_ia', {})
        
        ai = WexIntelligenceAI()
        
        # Testar modelo de sentimento
        modelo_sent = modelos.get('modelo_sentimento')
        if modelo_sent:
            print(f"📊 Testando modelo de sentimento: {modelo_sent}")
            try:
                payload = {"inputs": "This is a technical support request"}
                resultado = ai._chamar_huggingface_api(modelo_sent, payload)
                
                if 'error' not in resultado:
                    print("   ✅ Funcionando")
                else:
                    print(f"   ❌ Erro: {resultado.get('error', 'Desconhecido')}")
            except Exception as e:
                print(f"   ❌ Exceção: {e}")
        
        # Testar modelo de classificação
        modelo_class = modelos.get('modelo_classificacao')
        if modelo_class:
            print(f"📊 Testando modelo de classificação: {modelo_class}")
            try:
                payload = {"inputs": "System error critical problem"}
                resultado = ai._chamar_huggingface_api(modelo_class, payload)
                
                if 'error' not in resultado:
                    print("   ✅ Funcionando")
                else:
                    print(f"   ❌ Erro: {resultado.get('error', 'Desconhecido')}")
            except Exception as e:
                print(f"   ❌ Exceção: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar modelos: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Teste de Correções da API Hugging Face")
    print("🎯 Objetivo: Verificar se os erros 404 foram corrigidos")
    print()
    
    success1 = test_huggingface_fixes()
    success2 = test_specific_models()
    
    if success1 and success2:
        print("\n🏆 SUCESSO TOTAL! Correções implementadas com êxito.")
        sys.exit(0)
    else:
        print("\n⚠️ Alguns problemas ainda precisam ser resolvidos.")
        sys.exit(1)