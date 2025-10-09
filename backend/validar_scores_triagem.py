"""
Script para validar os scores dos chamados criados
e demonstrar como estão alinhados com os critérios de triagem
"""

import json
from database import SessionLocal
from models import Chamado, FollowUp

def load_triagem_config():
    """Carrega configurações de triagem"""
    with open('triagem_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def calcular_score_anexos(chamado, config):
    """Calcula score baseado em anexos"""
    criterios = config['pontuacao_criterios']['anexos']['criterios']
    score = 0
    detalhes = []
    
    if chamado.possui_anexos:
        score += criterios['todos_obrigatorios_presentes']['pontos']  # 20
        score += criterios['formato_correto']['pontos']  # 5
        score += criterios['tamanho_adequado']['pontos']  # 3
        score += criterios['nomes_descritivos']['pontos']  # 2
        detalhes.append("✅ Anexos presentes e bem formatados")
    else:
        detalhes.append("❌ Sem anexos")
    
    return score, detalhes

def calcular_score_descricao(chamado, config):
    """Calcula score baseado na descrição"""
    criterios = config['pontuacao_criterios']['descricao']['criterios']
    score = 0
    detalhes = []
    
    desc_len = len(chamado.descricao)
    palavras_tecnicas = config['palavras_chave']['tecnicas']
    
    # Descrição clara e detalhada (>100 chars)
    if desc_len >= 100:
        score += criterios['clara_detalhada']['pontos']  # 40
        detalhes.append(f"✅ Descrição detalhada ({desc_len} chars)")
    else:
        detalhes.append(f"❌ Descrição muito curta ({desc_len} chars)")
    
    # Palavras-chave técnicas
    palavras_encontradas = [p for p in palavras_tecnicas if p.lower() in chamado.descricao.lower()]
    if palavras_encontradas:
        score += criterios['palavras_chave_tecnicas']['pontos']  # 20
        detalhes.append(f"✅ Palavras técnicas: {palavras_encontradas}")
    else:
        detalhes.append("❌ Sem palavras-chave técnicas")
    
    # Estrutura organizada (heurística simples)
    if '\n' in chamado.descricao and ':' in chamado.descricao:
        score += criterios['estrutura_organizada']['pontos']  # 20
        detalhes.append("✅ Texto bem estruturado")
    else:
        detalhes.append("❌ Texto mal estruturado")
    
    # Ausência de erros (heurística simples)
    if desc_len > 50 and chamado.descricao[0].isupper():
        score += criterios['ausencia_erros']['pontos']  # 20
        detalhes.append("✅ Boa qualidade de escrita")
    else:
        detalhes.append("❌ Problemas de escrita")
    
    return score, detalhes

def calcular_score_info_tecnicas(chamado, config):
    """Calcula score baseado em informações técnicas"""
    criterios = config['pontuacao_criterios']['info_tecnicas']['criterios']
    score = 0
    detalhes = []
    
    # Cliente identificado
    if chamado.cliente_solicitante and len(chamado.cliente_solicitante) > 10:
        score += criterios['cliente_identificado']['pontos']  # 10
        detalhes.append("✅ Cliente bem identificado")
    else:
        detalhes.append("❌ Cliente mal identificado")
    
    # Criticidade apropriada (heurística)
    palavras_criticas = config['palavras_chave']['criticidade_critica']
    palavras_altas = config['palavras_chave']['criticidade_alta']
    
    tem_palavras_criticas = any(p in chamado.descricao.lower() for p in palavras_criticas)
    tem_palavras_altas = any(p in chamado.descricao.lower() for p in palavras_altas)
    
    if ((chamado.criticidade == "Crítica" and tem_palavras_criticas) or 
        (chamado.criticidade == "Alta" and tem_palavras_altas) or
        (chamado.criticidade in ["Baixa", "Média"])):
        score += criterios['criticidade_apropriada']['pontos']  # 5
        detalhes.append("✅ Criticidade apropriada")
    else:
        detalhes.append("❌ Criticidade inadequada")
    
    # Título descritivo (usando número WEX como proxy)
    if chamado.numero_wex and "WEX-2025-" in chamado.numero_wex:
        score += criterios['titulo_descritivo']['pontos']  # 5
        detalhes.append("✅ Identificação clara")
    else:
        detalhes.append("❌ Identificação inadequada")
    
    # Data e hora válidas
    if chamado.data_criacao:
        score += criterios['data_hora_validas']['pontos']  # 3
        detalhes.append("✅ Datas válidas")
    
    # Número WEX correto
    if chamado.numero_wex and chamado.numero_wex.startswith("WEX-2025-"):
        score += criterios['numero_wex_correto']['pontos']  # 2
        detalhes.append("✅ Número WEX correto")
    else:
        detalhes.append("❌ Número WEX incorreto")
    
    return score, detalhes

def calcular_score_contexto(chamado, config):
    """Calcula score baseado no contexto"""
    criterios = config['pontuacao_criterios']['contexto']['criterios']
    score = 0
    detalhes = []
    
    desc_lower = chamado.descricao.lower()
    
    # Problema definido
    palavras_problema = ['problema', 'erro', 'falha', 'indisponível', 'bug', 'issue']
    if any(p in desc_lower for p in palavras_problema):
        score += criterios['problema_definido']['pontos']  # 10
        detalhes.append("✅ Problema bem definido")
    else:
        detalhes.append("❌ Problema mal definido")
    
    # Impacto mencionado
    palavras_impacto = ['impacto', 'usuários', 'clientes', 'afetados', 'perdas', 'perda']
    if any(p in desc_lower for p in palavras_impacto):
        score += criterios['impacto_mencionado']['pontos']  # 5
        detalhes.append("✅ Impacto mencionado")
    else:
        detalhes.append("❌ Impacto não mencionado")
    
    # Urgência justificada
    palavras_urgencia = ['urgente', 'crítico', 'emergência', 'parado', 'indisponível']
    if any(p in desc_lower for p in palavras_urgencia):
        score += criterios['urgencia_justificada']['pontos']  # 3
        detalhes.append("✅ Urgência justificada")
    else:
        detalhes.append("❌ Urgência não justificada")
    
    # Tentativas de solução
    palavras_tentativas = ['tentamos', 'testamos', 'verificamos', 'restart', 'reiniciar']
    if any(p in desc_lower for p in palavras_tentativas):
        score += criterios['tentativas_solucao']['pontos']  # 2
        detalhes.append("✅ Tentativas mencionadas")
    else:
        detalhes.append("❌ Sem tentativas mencionadas")
    
    return score, detalhes

def analisar_chamado(chamado, config):
    """Analisa um chamado completo"""
    pesos = config['pesos_categorias']
    thresholds = config['thresholds']
    
    # Obter máximos por categoria do config
    max_anexos = config['pontuacao_criterios']['anexos']['total_maximo']  # 30
    max_descricao = config['pontuacao_criterios']['descricao']['total_maximo']  # 25  
    max_info = config['pontuacao_criterios']['info_tecnicas']['total_maximo']  # 25
    max_contexto = config['pontuacao_criterios']['contexto']['total_maximo']  # 20
    
    # Calcular scores brutos por categoria
    score_anexos_bruto, det_anexos = calcular_score_anexos(chamado, config)
    score_desc_bruto, det_desc = calcular_score_descricao(chamado, config)
    score_info_bruto, det_info = calcular_score_info_tecnicas(chamado, config)
    score_contexto_bruto, det_contexto = calcular_score_contexto(chamado, config)
    
    # Limitar aos máximos da categoria
    score_anexos = min(score_anexos_bruto, max_anexos)
    score_desc = min(score_desc_bruto, max_descricao)
    score_info = min(score_info_bruto, max_info)
    score_contexto = min(score_contexto_bruto, max_contexto)
    
    # Converter para escala 0-100 aplicando os pesos
    # Cada categoria contribui com sua porcentagem para o total de 100
    score_final = (
        (score_anexos / max_anexos) * (pesos['anexos'] * 100) +
        (score_desc / max_descricao) * (pesos['descricao'] * 100) + 
        (score_info / max_info) * (pesos['info_tecnicas'] * 100) +
        (score_contexto / max_contexto) * (pesos['contexto'] * 100)
    )
    
    # Determinar decisão
    if score_final >= thresholds['aprovacao_automatica']:
        decisao = "🟢 APROVAÇÃO AUTOMÁTICA"
    elif score_final >= thresholds['revisao_humana']:
        decisao = "🟡 REVISÃO HUMANA"
    else:
        decisao = "🔴 RECUSA AUTOMÁTICA"
    
    return {
        'score_final': score_final,
        'decisao': decisao,
        'breakdown': {
            'anexos': score_anexos,
            'descricao': score_desc,
            'info_tecnicas': score_info,
            'contexto': score_contexto
        },
        'breakdown_max': {
            'anexos': max_anexos,
            'descricao': max_descricao,
            'info_tecnicas': max_info,
            'contexto': max_contexto
        },
        'detalhes': {
            'anexos': det_anexos,
            'descricao': det_desc,
            'info_tecnicas': det_info,
            'contexto': det_contexto
        }
    }

def main():
    """Função principal de validação"""
    print("🔍 VALIDAÇÃO DOS SCORES DOS CHAMADOS CRIADOS")
    print("=" * 70)
    
    config = load_triagem_config()
    db = SessionLocal()
    
    try:
        chamados = db.query(Chamado).order_by(Chamado.id).all()
        
        for i, chamado in enumerate(chamados, 1):
            analise = analisar_chamado(chamado, config)
            
            print(f"\n📋 CHAMADO {i}: {chamado.numero_wex}")
            print(f"🏢 Cliente: {chamado.cliente_solicitante}")
            print(f"📊 Score Final: {analise['score_final']:.1f}/100")
            print(f"⚖️ Decisão: {analise['decisao']}")
            print(f"🎯 Score Original: {chamado.score_qualidade}")
            
            print("\n📈 Breakdown por Categoria:")
            breakdown = analise['breakdown']
            breakdown_max = analise['breakdown_max']
            print(f"   📎 Anexos: {breakdown['anexos']:.1f}/{breakdown_max['anexos']}")
            print(f"   📝 Descrição: {breakdown['descricao']:.1f}/{breakdown_max['descricao']}") 
            print(f"   🔧 Info Técnicas: {breakdown['info_tecnicas']:.1f}/{breakdown_max['info_tecnicas']}")
            print(f"   🎯 Contexto: {breakdown['contexto']:.1f}/{breakdown_max['contexto']}")
            
            if i <= 3:  # Mostrar detalhes dos primeiros 3
                print("\n🔍 Detalhes da Análise:")
                for categoria, detalhes in analise['detalhes'].items():
                    print(f"   {categoria.upper()}:")
                    for detalhe in detalhes:
                        print(f"     {detalhe}")
            
            print("-" * 70)
        
        print(f"\n📊 RESUMO FINAL:")
        print(f"Total de chamados analisados: {len(chamados)}")
        
        aprovados = sum(1 for c in chamados if analisar_chamado(c, config)['score_final'] >= 70)
        revisao = sum(1 for c in chamados if 50 <= analisar_chamado(c, config)['score_final'] < 70)
        recusados = sum(1 for c in chamados if analisar_chamado(c, config)['score_final'] < 50)
        
        print(f"🟢 Aprovação automática: {aprovados}")
        print(f"🟡 Revisão humana: {revisao}")  
        print(f"🔴 Recusa automática: {recusados}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()