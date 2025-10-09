"""
Testes para validar o sistema de configuração parametrizável
Verifica se o triagem_config.json está sendo usado corretamente
"""

import sys
import os
import json
from datetime import datetime

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config_manager import ConfigManager, get_config_manager
    from wex_ai_engine import WexIntelligenceAI
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

def test_config_loading():
    """Testa se as configurações são carregadas corretamente"""
    print("🔧 Testando carregamento de configurações...")
    
    try:
        config_manager = get_config_manager()
        config = config_manager.config
        
        # Verificar se as seções obrigatórias existem
        assert hasattr(config, 'thresholds'), "Seção 'thresholds' não encontrada"
        assert hasattr(config, 'pesos_categorias'), "Seção 'pesos_categorias' não encontrada"
        assert hasattr(config, 'pontuacao_criterios'), "Seção 'pontuacao_criterios' não encontrada"
        
        # Verificar thresholds
        assert config.thresholds.get('aprovacao_automatica') == 70, "Threshold de aprovação incorreto"
        assert config.thresholds.get('revisao_humana') == 50, "Threshold de revisão incorreto"
        
        # Verificar pesos (devem somar aproximadamente 1.0)
        total_pesos = sum(config.pesos_categorias.values())
        assert abs(total_pesos - 1.0) < 0.01, f"Soma dos pesos incorreta: {total_pesos}"
        
        print("✅ Configurações carregadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return False

def test_config_access_methods():
    """Testa os métodos de acesso às configurações"""
    print("🔍 Testando métodos de acesso...")
    
    try:
        config_manager = get_config_manager()
        
        # Testar métodos de conveniência
        threshold = config_manager.get_threshold('aprovacao_automatica')
        assert threshold == 70, f"Threshold incorreto: {threshold}"
        
        peso = config_manager.get_peso_categoria('anexos')
        assert peso == 0.30, f"Peso incorreto: {peso}"
        
        pontos = config_manager.get_pontuacao_criterio('anexos', 'todos_obrigatorios_presentes')
        assert pontos == 20, f"Pontuação incorreta: {pontos}"
        
        limite = config_manager.get_limite_conteudo('min_descricao_chars')
        assert limite == 50, f"Limite incorreto: {limite}"
        
        print("✅ Métodos de acesso funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos métodos de acesso: {e}")
        return False

def test_ia_integration():
    """Testa se a IA está usando as configurações"""
    print("🤖 Testando integração com IA...")
    
    try:
        ai = WexIntelligenceAI()
        
        # Testar se a IA tem acesso ao config_manager
        assert hasattr(ai, 'config_manager'), "IA não tem config_manager"
        
        # Chamado de teste
        chamado_teste = {
            'id': 'TEST001',
            'titulo': 'Sistema WEX apresenta erro crítico',
            'descricao': 'O sistema WEX está apresentando erro 500 ao tentar carregar os relatórios financeiros. O problema é crítico pois afeta todos os usuários. Erro ocorre desde ontem às 14h.',
            'cliente_solicitante': 'Empresa ABC',
            'anexos_count': 2,
            'criticidade': 'Crítica',
            'numero_wex': 'WEX123456',
            'data_criacao': datetime.now().isoformat()
        }
        
        # Executar triagem
        resultado = ai.realizar_triagem(chamado_teste)
        
        # Verificar se o resultado é válido
        assert resultado.score_total >= 0, "Score total inválido"
        assert resultado.score_total <= 100, "Score total acima do máximo"
        assert resultado.decisao in ['aprovado', 'recusado', 'revisao'], "Decisão inválida"
        assert isinstance(resultado.motivos, list), "Motivos devem ser uma lista"
        
        print(f"✅ IA integrada com sucesso! Score: {resultado.score_total}, Decisão: {resultado.decisao}")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração com IA: {e}")
        return False

def test_score_calculation():
    """Testa se os scores estão sendo calculados corretamente"""
    print("📊 Testando cálculo de scores...")
    
    try:
        ai = WexIntelligenceAI()
        config_manager = get_config_manager()
        
        # Chamado com pontuação máxima
        chamado_otimo = {
            'id': 'PERFECT',
            'titulo': 'Sistema WEX apresenta erro crítico de autenticação',
            'descricao': 'O sistema WEX está apresentando erro 500 crítico ao tentar fazer login. Problema afeta todos os usuários desde hoje às 09:00. Passos para reproduzir: 1) Acessar sistema, 2) Inserir credenciais, 3) Clicar em entrar. Mensagem de erro: "Falha na autenticação do usuário". Tentei limpar cache e cookies sem sucesso. Ambiente: Windows 10, Chrome 91. Anexo com print da tela disponível.',
            'cliente_solicitante': 'Empresa Premium',
            'anexos_count': 3,
            'criticidade': 'Crítica',
            'numero_wex': 'WEX999999',
            'data_criacao': datetime.now().isoformat()
        }
        
        resultado_otimo = ai.realizar_triagem(chamado_otimo)
        
        # Chamado com pontuação baixa
        chamado_ruim = {
            'id': 'BAD',
            'titulo': 'Erro',
            'descricao': 'Não funciona',
            'cliente_solicitante': '',
            'anexos_count': 0,
            'criticidade': '',
            'numero_wex': 'INVALID',
            'data_criacao': ''
        }
        
        resultado_ruim = ai.realizar_triagem(chamado_ruim)
        
        # Verificar se o chamado bom tem score maior que o ruim
        assert resultado_otimo.score_total > resultado_ruim.score_total, \
            f"Score do chamado bom ({resultado_otimo.score_total}) deve ser maior que o ruim ({resultado_ruim.score_total})"
        
        # Verificar thresholds
        threshold_aprovacao = config_manager.get_threshold('aprovacao_automatica')
        if resultado_otimo.score_total >= threshold_aprovacao:
            assert resultado_otimo.decisao == 'aprovado', "Chamado com score alto deve ser aprovado"
        
        print(f"✅ Cálculo de scores funcionando! Bom: {resultado_otimo.score_total}, Ruim: {resultado_ruim.score_total}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no cálculo de scores: {e}")
        return False

def test_config_modification():
    """Testa modificação e recarga de configurações"""
    print("🔄 Testando modificação de configurações...")
    
    try:
        config_manager = get_config_manager()
        
        # Salvar valor original
        threshold_original = config_manager.get_threshold('aprovacao_automatica')
        
        # Modificar configuração
        config_manager.config.thresholds['aprovacao_automatica'] = 80
        
        # Verificar mudança
        novo_threshold = config_manager.get_threshold('aprovacao_automatica')
        assert novo_threshold == 80, "Threshold não foi modificado"
        
        # Restaurar valor original
        config_manager.config.thresholds['aprovacao_automatica'] = threshold_original
        
        print("✅ Modificação de configurações funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na modificação de configurações: {e}")
        return False

def test_config_summary():
    """Testa o resumo das configurações"""
    print("📋 Testando resumo das configurações...")
    
    try:
        config_manager = get_config_manager()
        summary = config_manager.get_summary()
        
        # Verificar se o resumo tem as informações esperadas
        assert 'version' in summary, "Versão não encontrada no resumo"
        assert 'thresholds' in summary, "Thresholds não encontrados no resumo"
        assert 'total_criterios' in summary, "Total de critérios não encontrado"
        
        print("✅ Resumo das configurações funcionando!")
        print(f"📊 Resumo: {json.dumps(summary, indent=2, default=str)}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no resumo de configurações: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do sistema de configuração parametrizável")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_config_access_methods,
        test_ia_integration,
        test_score_calculation,
        test_config_modification,
        test_config_summary
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print("-" * 40)
        except Exception as e:
            print(f"❌ Teste falhou com exceção: {e}")
            results.append(False)
            print("-" * 40)
    
    # Resumo final
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 RESUMO DOS TESTES:")
    print(f"✅ Testes aprovados: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema de configuração está funcionando corretamente.")
        return True
    else:
        print("⚠️ ALGUNS TESTES FALHARAM. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)