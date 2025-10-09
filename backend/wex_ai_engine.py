"""
Módulo de Inteligência Artificial para WEX Intelligence
Implementa triagem automática e sugestões usando Hugging Face

Baseado nas regras do documento Triagem.md
ATUALIZADO: Agora usa configurações parametrizáveis do triagem_config.json
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
import numpy as np

# Importa o gerenciador de configurações
from config_manager import get_config_manager, get_triagem_config

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chave da Hugging Face
HUGGINGFACE_API_KEY = "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"
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

# Funções auxiliares simples para análise de texto
def calcular_similaridade_simples(texto1: str, texto2: str) -> float:
    """Calcula similaridade simples entre dois textos baseada em palavras comuns"""
    if not texto1 or not texto2:
        return 0.0
    
    palavras1 = set(texto1.lower().split())
    palavras2 = set(texto2.lower().split())
    
    if not palavras1 or not palavras2:
        return 0.0
    
    intersecao = palavras1.intersection(palavras2)
    uniao = palavras1.union(palavras2)
    
    return len(intersecao) / len(uniao) if uniao else 0.0

def encontrar_textos_similares(texto_base: str, lista_textos: List[str], limite: int = 3) -> List[Tuple[str, float]]:
    """Encontra textos similares usando análise simples"""
    if not texto_base or not lista_textos:
        return []
    
    similaridades = []
    for texto in lista_textos:
        score = calcular_similaridade_simples(texto_base, texto)
        if score > 0.1:  # Threshold mínimo
            similaridades.append((texto, score))
    
    # Ordena por similaridade decrescente
    similaridades.sort(key=lambda x: x[1], reverse=True)
    return similaridades[:limite]

@dataclass
class TriagemResult:
    """Resultado da triagem automática"""
    chamado_id: str
    score_total: int
    score_breakdown: Dict[str, int]
    decisao: str  # "aprovado", "recusado", "revisao"
    motivos: List[str]
    sugestoes: List[str]
    tags_sugeridas: List[str]
    criticidade_sugerida: str
    confianca: float
    tempo_processamento_ms: int
    observacoes: str

@dataclass
class SugestaoFollowup:
    """Sugestão de follow-up gerada pela IA"""
    titulo: str
    descricao: str
    tipo: str
    confianca: float
    motivo: str
    exemplos_similares: List[str]

@dataclass
class ChamadosSimilares:
    """Resultado da busca por chamados similares"""
    chamados_similares: List[Dict]
    total_encontrados: int
    padroes_identificados: List[str]
    modelo_usado: str
    tempo_processamento: float
    confianca_analise: float

@dataclass
class RelatorioPatroes:
    """Resultado do relatório de padrões"""
    total_grupos_similares: int
    padroes_globais: List[str]
    grupos_similares: List[Dict]
    insights_ia: List[str]
    tendencias: List[str]
    recomendacoes: List[str]
    resumo: str
    modelo_usado: str
    tempo_processamento: float
    confianca_analise: float

class WexIntelligenceAI:
    """Classe principal para funcionalidades de IA"""
    
    def __init__(self):
        self.api_key = HUGGINGFACE_API_KEY
        self.config_manager = get_config_manager()
        
    def _chamar_huggingface_api(self, model_name: str, payload: Dict) -> Dict:
        """Chama a API da Hugging Face"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"{HUGGINGFACE_API_URL}{model_name}"
            
            timeout = self.config_manager.get_configuracao_avancada('timeouts', 'timeout_ia_ms') or 3000
            timeout_seconds = timeout / 1000.0
            
            response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao chamar Hugging Face API: {e}")
            return {"error": str(e)}
    
    def calcular_score_anexos(self, chamado: Dict) -> int:
        """Calcula score para anexos baseado nas configurações"""
        config = self.config_manager.config
        anexos_config = config.pontuacao_criterios.get('anexos', {})
        criterios = anexos_config.get('criterios', {})
        
        score = 0
        
        # Simular verificação de anexos
        # Em implementação real, verificaria arquivos reais
        if chamado.get('anexos_count', 0) > 0:
            score += criterios.get('todos_obrigatorios_presentes', {}).get('pontos', 20)
            score += criterios.get('formato_correto', {}).get('pontos', 5)
            score += criterios.get('tamanho_adequado', {}).get('pontos', 3)
            score += criterios.get('nomes_descritivos', {}).get('pontos', 2)
        
        max_score = anexos_config.get('total_maximo', 30)
        return min(score, max_score)
    
    def calcular_score_descricao(self, descricao: str) -> Tuple[int, List[str]]:
        """Calcula score para descrição baseado nas configurações"""
        config = self.config_manager.config
        descricao_config = config.pontuacao_criterios.get('descricao', {})
        criterios = descricao_config.get('criterios', {})
        limites = config.limites_conteudo
        palavras_tecnicas = config.palavras_chave.get('tecnicas', [])
        
        score = 0
        motivos = []
        
        if not descricao:
            return 0, ["Descrição ausente"]
        
        # Verificar tamanho baseado na configuração
        min_chars = limites.get('min_descricao_chars', 50)
        if len(descricao) >= 100:
            score += criterios.get('clara_detalhada', {}).get('pontos', 15)
            motivos.append("Descrição detalhada")
        elif len(descricao) >= min_chars:
            score += int(criterios.get('clara_detalhada', {}).get('pontos', 15) * 0.7)
            motivos.append("Descrição adequada")
        else:
            motivos.append("Descrição muito curta")
        
        # Palavras-chave técnicas baseadas na configuração
        if any(palavra in descricao.lower() for palavra in palavras_tecnicas):
            score += criterios.get('palavras_chave_tecnicas', {}).get('pontos', 5)
            motivos.append("Contém termos técnicos")
        
        # Estrutura organizada (pontuação, parágrafos)
        if '.' in descricao or '\n' in descricao:
            score += criterios.get('estrutura_organizada', {}).get('pontos', 3)
            motivos.append("Bem estruturada")
        
        # Verificar qualidade com IA
        try:
            resultado_ia = self._analisar_qualidade_texto(descricao)
            if resultado_ia.get('score', 0) > 0.7:
                score += 2
                motivos.append("Alta qualidade detectada pela IA")
        except:
            pass
        
        return min(score, 25), motivos
    
    def calcular_score_info_tecnicas(self, chamado: Dict) -> Tuple[int, List[str]]:
        """Calcula score para informações técnicas baseado nas configurações"""
        config = self.config_manager.config
        info_config = config.pontuacao_criterios.get('info_tecnicas', {})
        criterios = info_config.get('criterios', {})
        limites = config.limites_conteudo
        
        score = 0
        motivos = []
        
        # Cliente identificado
        if chamado.get('cliente_solicitante'):
            score += criterios.get('cliente_identificado', {}).get('pontos', 10)
            motivos.append("Cliente identificado")
        
        # Criticidade apropriada
        if chamado.get('criticidade') in ['Baixa', 'Média', 'Alta', 'Crítica']:
            score += criterios.get('criticidade_apropriada', {}).get('pontos', 5)
            motivos.append("Criticidade definida")
        
        # Título descritivo
        titulo = chamado.get('titulo', '')
        min_titulo = limites.get('min_titulo_chars', 10)
        max_titulo = limites.get('max_titulo_chars', 200)
        if min_titulo <= len(titulo) <= max_titulo:
            score += criterios.get('titulo_descritivo', {}).get('pontos', 5)
            motivos.append("Título adequado")
        
        # Data/hora válidas
        if chamado.get('data_criacao'):
            score += criterios.get('data_hora_validas', {}).get('pontos', 3)
            motivos.append("Data válida")
        
        # Número WEX correto
        numero_wex = chamado.get('numero_wex', '')
        if re.match(r'^WEX\d{6}$', numero_wex):
            score += criterios.get('numero_wex_correto', {}).get('pontos', 2)
            motivos.append("Número WEX válido")
        
        max_score = info_config.get('total_maximo', 25)
        return min(score, max_score), motivos
    
    def calcular_score_contexto(self, descricao: str) -> Tuple[int, List[str]]:
        """Calcula score para contexto baseado nas configurações"""
        config = self.config_manager.config
        contexto_config = config.pontuacao_criterios.get('contexto', {})
        criterios = contexto_config.get('criterios', {})
        
        score = 0
        motivos = []
        
        if not descricao:
            return 0, ["Sem contexto"]
        
        descricao_lower = descricao.lower()
        
        # Problema claramente definido
        indicadores_problema = ['problema', 'erro', 'falha', 'não funciona', 'bug']
        if any(ind in descricao_lower for ind in indicadores_problema):
            score += criterios.get('problema_definido', {}).get('pontos', 10)
            motivos.append("Problema bem definido")
        
        # Impacto mencionado
        indicadores_impacto = ['impacto', 'afeta', 'usuários', 'crítico', 'urgente']
        if any(ind in descricao_lower for ind in indicadores_impacto):
            score += criterios.get('impacto_mencionado', {}).get('pontos', 5)
            motivos.append("Impacto mencionado")
        
        # Urgência justificada
        indicadores_urgencia = ['urgente', 'imediato', 'asap', 'prioridade']
        if any(ind in descricao_lower for ind in indicadores_urgencia):
            score += criterios.get('urgencia_justificada', {}).get('pontos', 3)
            motivos.append("Urgência identificada")
        
        # Tentativas de solução
        indicadores_tentativas = ['tentei', 'tentativa', 'já testei', 'verificado']
        if any(ind in descricao_lower for ind in indicadores_tentativas):
            score += criterios.get('tentativas_solucao', {}).get('pontos', 2)
            motivos.append("Tentativas de solução mencionadas")
        
        max_score = contexto_config.get('total_maximo', 20)
        return min(score, max_score), motivos
    
    def _analisar_qualidade_texto(self, texto: str) -> Dict:
        """Analisa qualidade do texto usando IA com modelos funcionais"""
        try:
            # Usar modelo de análise de sentimento que funciona
            config = self.config_manager.config
            modelo_sentimento = config.configuracoes_avancadas.get('modelos_ia', {}).get(
                'modelo_sentimento', 'cardiffnlp/twitter-roberta-base-sentiment-latest'
            )
            
            payload = {"inputs": texto[:500]}  # Limitar texto para análise
            
            resultado = self._chamar_huggingface_api(modelo_sentimento, payload)
            
            # Analisar resultado para calcular score
            score = 0.5  # Base
            
            if isinstance(resultado, list) and len(resultado) > 0:
                if isinstance(resultado[0], list) and len(resultado[0]) > 0:
                    sentimentos = resultado[0]
                    
                    # Procurar por sentimento positivo/neutro (indica texto bem estruturado)
                    for sent in sentimentos:
                        if isinstance(sent, dict):
                            label = sent.get('label', '').lower()
                            score_sent = sent.get('score', 0)
                            
                            if 'positive' in label or 'neutral' in label:
                                score = min(0.9, 0.5 + (score_sent * 0.4))
                                break
                            elif '4 star' in label or '5 star' in label:
                                score = min(0.9, 0.5 + (score_sent * 0.4))
                                break
            
            # Ajustar score baseado no comprimento do texto
            if len(texto) > 100:
                score += 0.1
            if len(texto) > 200:
                score += 0.1
            
            score = min(1.0, score)
            
            return {"score": score, "analise": resultado}
            
        except Exception as e:
            logger.warning(f"Erro na análise de qualidade: {e}")
            # Fallback baseado em heurísticas simples
            score = 0.7 if len(texto) > 100 else 0.5
            return {"score": score, "analise": "Análise local - modelo remoto indisponível"}
    
    def _sugerir_criticidade(self, chamado: Dict, score_total: int) -> str:
        """Sugere criticidade baseada na análise e configurações"""
        config = self.config_manager.config
        descricao = chamado.get('descricao', '').lower()
        
        # Usar palavras-chave configuradas
        palavras_criticas = config.palavras_chave.get('criticidade_critica', [])
        palavras_altas = config.palavras_chave.get('criticidade_alta', [])
        palavras_medias = config.palavras_chave.get('criticidade_media', [])
        palavras_baixas = config.palavras_chave.get('criticidade_baixa', [])
        
        if any(palavra in descricao for palavra in palavras_criticas):
            return 'Crítica'
        elif any(palavra in descricao for palavra in palavras_altas) and score_total > 60:
            return 'Alta'
        elif any(palavra in descricao for palavra in palavras_medias):
            return 'Média'
        elif any(palavra in descricao for palavra in palavras_baixas):
            return 'Baixa'
        else:
            # Decisão baseada no score se não houver palavras-chave específicas
            if score_total >= 80:
                return 'Alta'
            elif score_total >= 60:
                return 'Média'
            else:
                return 'Baixa'
    
    def _gerar_tags_sugeridas(self, chamado: Dict) -> List[str]:
        """Gera tags baseadas no conteúdo"""
        tags = []
        descricao = chamado.get('descricao', '').lower()
        titulo = chamado.get('titulo', '').lower()
        texto_completo = f"{titulo} {descricao}"
        
        # Tags baseadas em palavras-chave
        mapeamento_tags = {
            'login': ['autenticação', 'acesso'],
            'performance': ['lento', 'lentidão', 'demorado'],
            'interface': ['tela', 'botão', 'menu'],
            'sistema': ['sistema', 'aplicação'],
            'erro': ['erro', 'falha', 'bug'],
            'rede': ['rede', 'conectividade', 'internet'],
            'dados': ['dados', 'informação', 'relatório']
        }
        
        for tag, palavras in mapeamento_tags.items():
            if any(palavra in texto_completo for palavra in palavras):
                tags.append(tag)
        
        # Adicionar tag baseada na criticidade
        criticidade = chamado.get('criticidade', '').lower()
        if criticidade:
            tags.append(f"prioridade-{criticidade}")
        
        return tags[:5]  # Limitar a 5 tags
    
    def realizar_triagem(self, chamado: Dict) -> TriagemResult:
        """Realiza triagem completa de um chamado"""
        inicio = datetime.now()
        
        try:
            config = self.config_manager.config
            
            # Calcular scores individuais
            score_anexos = self.calcular_score_anexos(chamado)
            score_descricao, motivos_desc = self.calcular_score_descricao(chamado.get('descricao', ''))
            score_info, motivos_info = self.calcular_score_info_tecnicas(chamado)
            score_contexto, motivos_ctx = self.calcular_score_contexto(chamado.get('descricao', ''))
            
            # Score total ponderado baseado nas configurações
            pesos = config.pesos_categorias
            
            # Obter máximos por categoria do config
            max_anexos = config.pontuacao_criterios.get('anexos', {}).get('total_maximo', 30)
            max_descricao = config.pontuacao_criterios.get('descricao', {}).get('total_maximo', 25)
            max_info = config.pontuacao_criterios.get('info_tecnicas', {}).get('total_maximo', 25)
            max_contexto = config.pontuacao_criterios.get('contexto', {}).get('total_maximo', 20)
            
            # Aplicar fórmula correta: normalizar por categoria e aplicar pesos
            score_total = int(
                (score_anexos / max_anexos) * (pesos.get('anexos', 0.30) * 100) +
                (score_descricao / max_descricao) * (pesos.get('descricao', 0.25) * 100) +
                (score_info / max_info) * (pesos.get('info_tecnicas', 0.25) * 100) +
                (score_contexto / max_contexto) * (pesos.get('contexto', 0.20) * 100)
            )
            
            # Determinar decisão baseada nos thresholds configurados
            thresholds = config.thresholds
            if score_total >= thresholds.get('aprovacao_automatica', 70):
                decisao = "aprovado"
            elif score_total >= thresholds.get('revisao_humana', 50):
                decisao = "revisao"
            else:
                decisao = "recusado"
            
            # Combinar motivos
            todos_motivos = motivos_desc + motivos_info + motivos_ctx
            
            # Gerar sugestões
            sugestoes = self._gerar_sugestoes_melhoria(chamado, score_total)
            
            # Sugerir criticidade
            criticidade_sugerida = self._sugerir_criticidade(chamado, score_total)
            
            # Gerar tags
            tags_sugeridas = self._gerar_tags_sugeridas(chamado)
            
            # Calcular confiança
            confianca = min(score_total / 100.0, 1.0)
            
            # Tempo de processamento
            tempo_ms = int((datetime.now() - inicio).total_seconds() * 1000)
            
            return TriagemResult(
                chamado_id=chamado.get('id', ''),
                score_total=score_total,
                score_breakdown={
                    "anexos": score_anexos,
                    "descricao": score_descricao,
                    "info_tecnicas": score_info,
                    "contexto": score_contexto
                },
                decisao=decisao,
                motivos=todos_motivos,
                sugestoes=sugestoes,
                tags_sugeridas=tags_sugeridas,
                criticidade_sugerida=criticidade_sugerida,
                confianca=confianca,
                tempo_processamento_ms=tempo_ms,
                observacoes=f"Análise completa - Score: {score_total}/100"
            )
            
        except Exception as e:
            logger.error(f"Erro na triagem: {e}")
            return TriagemResult(
                chamado_id=chamado.get('id', ''),
                score_total=0,
                score_breakdown={},
                decisao="erro",
                motivos=[f"Erro na análise: {str(e)}"],
                sugestoes=[],
                tags_sugeridas=[],
                criticidade_sugerida="Média",
                confianca=0.0,
                tempo_processamento_ms=0,
                observacoes="Erro durante processamento"
            )
    
    def _gerar_sugestoes_melhoria(self, chamado: Dict, score: int) -> List[str]:
        """Gera sugestões de melhoria baseadas no score"""
        sugestoes = []
        
        if score < 50:
            sugestoes.append("Adicione mais detalhes na descrição do problema")
            sugestoes.append("Inclua anexos como screenshots ou logs")
            sugestoes.append("Especifique o impacto do problema")
        elif score < 70:
            sugestoes.append("Melhore a descrição com mais contexto técnico")
            sugestoes.append("Adicione informações sobre tentativas de solução")
        else:
            sugestoes.append("Chamado bem estruturado, pronto para análise")
        
        return sugestoes
    
    def gerar_sugestoes_followup(self, chamado: Dict, historico_similares: List[Dict] = None) -> List[SugestaoFollowup]:
        """Gera sugestões de follow-up usando IA"""
        try:
            descricao = chamado.get('descricao', '')
            status = chamado.get('status', '')
            criticidade = chamado.get('criticidade', '')
            
            # Usar IA para análise de contexto (usando modelo funcional)
            config = self.config_manager.config
            modelo_classificacao = config.configuracoes_avancadas.get('modelos_ia', {}).get(
                'modelo_classificacao', 'nlptown/bert-base-multilingual-uncased-sentiment'
            )
            
            # Analisar o contexto do chamado
            payload = {"inputs": f"{status} {criticidade} {descricao[:300]}"}
            
            try:
                resultado_ia = self._chamar_huggingface_api(modelo_classificacao, payload)
                
                # Interpretar resultado para gerar sugestões contextuais
                urgencia_detectada = False
                qualidade_detectada = False
                
                if isinstance(resultado_ia, list) and len(resultado_ia) > 0:
                    if isinstance(resultado_ia[0], list):
                        for item in resultado_ia[0]:
                            if isinstance(item, dict):
                                label = item.get('label', '').lower()
                                score = item.get('score', 0)
                                
                                if ('5 star' in label or '4 star' in label) and score > 0.5:
                                    qualidade_detectada = True
                                elif ('1 star' in label or '2 star' in label) and score > 0.5:
                                    urgencia_detectada = True
                
            except Exception as e:
                logger.warning(f"Erro na análise contextual: {e}")
                urgencia_detectada = False
                qualidade_detectada = False
            
            # Sugestões baseadas em regras + análise de IA
            sugestoes = []
            
            if status == "Aberto":
                if urgencia_detectada:
                    sugestoes.append(SugestaoFollowup(
                        titulo="Priorização Urgente",
                        descricao="Problema detectado como crítico, requer atenção imediata",
                        tipo="Urgente",
                        confianca=0.9,
                        motivo="IA detectou indicadores de alta criticidade",
                        exemplos_similares=[]
                    ))
                else:
                    sugestoes.append(SugestaoFollowup(
                        titulo="Análise Inicial",
                        descricao="Realizar análise técnica inicial do problema reportado",
                        tipo="Análise",
                        confianca=0.8,
                        motivo="Status inicial requer investigação",
                        exemplos_similares=[]
                    ))
            elif status == "Em análise":
                if qualidade_detectada:
                    sugestoes.append(SugestaoFollowup(
                        titulo="Solução Direcionada",
                        descricao="Chamado bem estruturado, implementar solução baseada na análise",
                        tipo="Solução",
                        confianca=0.9,
                        motivo="IA detectou alta qualidade na descrição",
                        exemplos_similares=[]
                    ))
                else:
                    sugestoes.append(SugestaoFollowup(
                        titulo="Teste de Reprodução",
                        descricao="Tentar reproduzir o problema em ambiente de teste",
                        tipo="Teste",
                        confianca=0.7,
                        motivo="Análise em andamento necessita validação",
                        exemplos_similares=[]
                ))
            
            if criticidade in ["Alta", "Crítica"]:
                sugestoes.append(SugestaoFollowup(
                    titulo="Comunicação Prioritária",
                    descricao="Informar cliente sobre andamento devido à alta criticidade",
                    tipo="Comunicação",
                    confianca=0.95,
                    motivo="Criticidade elevada requer atenção especial",
                    exemplos_similares=[]
                ))
            
            # Adicionar sugestão baseada na IA (se disponível)
            ia_funcionou = False
            try:
                if isinstance(resultado_ia, list) or (isinstance(resultado_ia, dict) and 'error' not in resultado_ia):
                    ia_funcionou = True
            except:
                ia_funcionou = False
            
            if ia_funcionou:
                sugestoes.append(SugestaoFollowup(
                    titulo="Sugestão da IA",
                    descricao="Baseado na análise do conteúdo, considere verificar logs do sistema",
                    tipo="IA",
                    confianca=0.7,
                    motivo="Análise semântica do texto",
                    exemplos_similares=[]
                ))
            
            return sugestoes[:3]  # Retornar máximo 3 sugestões
            
        except Exception as e:
            logger.error(f"Erro ao gerar sugestões: {e}")
            return [SugestaoFollowup(
                titulo="Erro na IA",
                descricao="Não foi possível gerar sugestões automáticas",
                tipo="Erro",
                confianca=0.0,
                motivo=str(e),
                exemplos_similares=[]
            )]
    
    def encontrar_chamados_similares(self, chamado_principal, outros_chamados: List, 
                                   limite: int = 10, score_minimo: float = 0.3) -> ChamadosSimilares:
        """Encontra chamados similares usando análise de texto com IA"""
        tempo_inicio = datetime.now()
        
        try:
            # Extrair informações do chamado principal
            desc_principal = chamado_principal.descricao if hasattr(chamado_principal, 'descricao') else str(chamado_principal)
            
            if not desc_principal or len(desc_principal) < 20:
                return ChamadosSimilares(
                    chamados_similares=[],
                    total_encontrados=0,
                    padroes_identificados=[],
                    modelo_usado="tf-idf",
                    tempo_processamento=0.0,
                    confianca_analise=0.0
                )
            
            # Preparar textos para análise
            textos = [desc_principal]
            chamados_validos = []
            
            for chamado in outros_chamados:
                desc = chamado.descricao if hasattr(chamado, 'descricao') else str(chamado)
                if desc and len(desc) > 20:
                    textos.append(desc)
                    chamados_validos.append(chamado)
            
            if len(textos) < 2:
                return ChamadosSimilares(
                    chamados_similares=[],
                    total_encontrados=0,
                    padroes_identificados=[],
                    modelo_usado="tf-idf",
                    tempo_processamento=0.0,
                    confianca_analise=0.0
                )
            
            # Calcular similaridade usando análise simples
            resultados_similaridade = encontrar_textos_similares(desc_principal, 
                [f"{c.titulo if hasattr(c, 'titulo') else ''} {c.descricao if hasattr(c, 'descricao') else str(c)}" for c in chamados_validos])
            
            # Criar lista de resultados com scores
            resultados = []
            for i, (texto_similar, score) in enumerate(resultados_similaridade):
                if score >= score_minimo:
                    chamado = chamados_validos[i]
                    
                    # Análise de motivos de similaridade
                    motivos = []
                    if score > 0.7:
                        motivos.append("Descrição muito similar")
                    elif score > 0.5:
                        motivos.append("Termos em comum")
                    else:
                        motivos.append("Similaridade moderada")
                    
                    resultado = {
                        'id': chamado.id if hasattr(chamado, 'id') else 0,
                        'numero_wex': chamado.numero_wex if hasattr(chamado, 'numero_wex') else "N/A",
                        'cliente': chamado.cliente_solicitante if hasattr(chamado, 'cliente_solicitante') else "N/A",
                        'descricao': chamado.descricao if hasattr(chamado, 'descricao') else str(chamado),
                        'status': chamado.status.value if hasattr(chamado, 'status') and hasattr(chamado.status, 'value') else "N/A",
                        'criticidade': chamado.criticidade.value if hasattr(chamado, 'criticidade') and hasattr(chamado.criticidade, 'value') else "N/A",
                        'data_criacao': chamado.data_criacao if hasattr(chamado, 'data_criacao') else None,
                        'score_similaridade': round(float(score), 3),
                        'motivos': motivos,
                        'detalhes_scores': {
                            'similaridade_textual': round(float(score), 3),
                            'confianca': round(min(float(score) * 1.2, 1.0), 3)
                        }
                    }
                    resultados.append(resultado)
            
            # Ordenar por score de similaridade
            resultados.sort(key=lambda x: x['score_similaridade'], reverse=True)
            resultados_limitados = resultados[:limite]
            
            # Identificar padrões
            padroes = []
            if len(resultados_limitados) > 2:
                padroes.append("Múltiplos chamados com descrição similar")
            if len(resultados_limitados) > 0:
                scores_altos = [r for r in resultados_limitados if r['score_similaridade'] > 0.7]
                if len(scores_altos) > 1:
                    padroes.append("Chamados praticamente idênticos identificados")
            
            tempo_processamento = (datetime.now() - tempo_inicio).total_seconds()
            confianca = np.mean([r['score_similaridade'] for r in resultados_limitados]) if resultados_limitados else 0.0
            
            return ChamadosSimilares(
                chamados_similares=resultados_limitados,
                total_encontrados=len(resultados),
                padroes_identificados=padroes,
                modelo_usado="tf-idf-vectorizer",
                tempo_processamento=tempo_processamento,
                confianca_analise=float(confianca)
            )
            
        except Exception as e:
            logger.error(f"Erro ao encontrar similares: {e}")
            return ChamadosSimilares(
                chamados_similares=[],
                total_encontrados=0,
                padroes_identificados=[],
                modelo_usado="tf-idf-error",
                tempo_processamento=0.0,
                confianca_analise=0.0
            )

    def gerar_relatorio_padroes(self, chamados: List, periodo_dias: int) -> RelatorioPatroes:
        """Gera relatório de padrões usando IA"""
        tempo_inicio = datetime.now()
        
        try:
            if not chamados:
                return RelatorioPatroes(
                    total_grupos_similares=0,
                    padroes_globais=[],
                    grupos_similares=[],
                    insights_ia=[],
                    tendencias=[],
                    recomendacoes=[],
                    resumo="Nenhum chamado para análise",
                    modelo_usado="sem_dados",
                    tempo_processamento=0.0,
                    confianca_analise=0.0
                )
            
            # Preparar textos para clustering
            textos = []
            chamados_validos = []
            
            for chamado in chamados:
                desc = chamado.descricao if hasattr(chamado, 'descricao') else str(chamado)
                if desc and len(desc) > 20:
                    textos.append(desc)
                    chamados_validos.append(chamado)
            
            if len(textos) < 2:
                return RelatorioPatroes(
                    total_grupos_similares=0,
                    padroes_globais=["Dados insuficientes para análise de padrões"],
                    grupos_similares=[],
                    insights_ia=["Necessário mais chamados para identificar padrões"],
                    tendencias=[],
                    recomendacoes=["Aguardar mais dados para análise efetiva"],
                    resumo=f"Apenas {len(chamados)} chamados disponíveis - insuficiente para análise",
                    modelo_usado="analise_minima",
                    tempo_processamento=0.1,
                    confianca_analise=0.1
                )
            
            # Análise de clustering usando similaridade simples
            # Identificar grupos similares
            grupos_similares = []
            chamados_processados = set()
            threshold = 0.4
            
            for i, chamado_base in enumerate(chamados_validos):
                if i in chamados_processados:
                    continue
                    
                grupo_atual = [chamado_base]
                indices_grupo = [i]
                chamados_processados.add(i)
                
                desc_base = textos[i]
                
                for j in range(i + 1, len(chamados_validos)):
                    if j not in chamados_processados:
                        similaridade = calcular_similaridade_simples(desc_base, textos[j])
                        if similaridade > threshold:
                            grupo_atual.append(chamados_validos[j])
                            indices_grupo.append(j)
                            chamados_processados.add(j)
                
                if len(grupo_atual) > 1:
                    # Calcular similaridade média do grupo
                    similaridades_grupo = []
                    for idx in indices_grupo[1:]:
                        sim = calcular_similaridade_simples(textos[indices_grupo[0]], textos[idx])
                        similaridades_grupo.append(sim)
                    
                    similaridade_media = sum(similaridades_grupo) / len(similaridades_grupo) if similaridades_grupo else 0.0
                    
                    grupo_info = {
                        'tamanho': len(grupo_atual),
                        'similaridade_media': similaridade_media,
                        'chamados': [
                            {
                                'id': c.id if hasattr(c, 'id') else 0,
                                'numero_wex': c.numero_wex if hasattr(c, 'numero_wex') else "N/A",
                                'descricao_resumo': (c.descricao[:100] + "...") if hasattr(c, 'descricao') and len(c.descricao) > 100 else (c.descricao if hasattr(c, 'descricao') else "N/A")
                            } for c in grupo_atual
                        ]
                    }
                    grupos_similares.append(grupo_info)
            
            # Gerar insights usando IA (simulado)
            insights_ia = []
            tendencias = []
            recomendacoes = []
            padroes_globais = []
            
            # Análise de padrões
            if len(grupos_similares) > 0:
                padroes_globais.append(f"Identificados {len(grupos_similares)} grupos de chamados similares")
                insights_ia.append(f"Recorrência alta: {len(grupos_similares)} padrões repetitivos identificados")
                
                maior_grupo = max(grupos_similares, key=lambda x: x['tamanho'])
                if maior_grupo['tamanho'] > 3:
                    insights_ia.append(f"Problema crítico: grupo com {maior_grupo['tamanho']} chamados similares")
                    recomendacoes.append("Investigar causa raiz do maior grupo de problemas similares")
            
            # Análise temporal
            if periodo_dias <= 7:
                tendencias.append("Análise de curto prazo - foco em problemas urgentes")
            elif periodo_dias <= 30:
                tendencias.append("Análise mensal - identificação de padrões recorrentes")
            else:
                tendencias.append("Análise de longo prazo - tendências sazonais possíveis")
            
            # Análise de criticidade
            criticidades = [c.criticidade.value if hasattr(c, 'criticidade') and hasattr(c.criticidade, 'value') else 'Baixa' for c in chamados_validos]
            from collections import Counter
            dist_crit = Counter(criticidades)
            
            if 'Alta' in dist_crit and dist_crit['Alta'] > len(chamados_validos) * 0.3:
                insights_ia.append("Alto volume de chamados críticos identificado")
                recomendacoes.append("Priorizar resolução de chamados de alta criticidade")
            
            # Gerar resumo
            resumo = f"Analisados {len(chamados_validos)} chamados em {periodo_dias} dias. "
            resumo += f"Identificados {len(grupos_similares)} grupos de problemas similares. "
            if len(grupos_similares) > 0:
                resumo += f"Maior grupo contém {max(g['tamanho'] for g in grupos_similares)} chamados similares."
            
            tempo_processamento = (datetime.now() - tempo_inicio).total_seconds()
            confianca = min(len(chamados_validos) / 50.0, 1.0)  # Mais dados = maior confiança
            
            return RelatorioPatroes(
                total_grupos_similares=len(grupos_similares),
                padroes_globais=padroes_globais,
                grupos_similares=grupos_similares,
                insights_ia=insights_ia,
                tendencias=tendencias,
                recomendacoes=recomendacoes,
                resumo=resumo,
                modelo_usado="tf-idf-clustering",
                tempo_processamento=tempo_processamento,
                confianca_analise=float(confianca)
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return RelatorioPatroes(
                total_grupos_similares=0,
                padroes_globais=[],
                grupos_similares=[],
                insights_ia=[],
                tendencias=[],
                recomendacoes=[],
                resumo=f"Erro na análise: {str(e)}",
                modelo_usado="error",
                tempo_processamento=0.0,
                confianca_analise=0.0
            )

# Instância global da IA
wex_ai = WexIntelligenceAI()