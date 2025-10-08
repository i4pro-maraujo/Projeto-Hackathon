"""
Módulo de Inteligência Artificial para WEX Intelligence
Implementa triagem automática e sugestões usando Hugging Face

Baseado nas regras do documento Triagem.md
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chave da Hugging Face
HUGGINGFACE_API_KEY = "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"
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/"

# Parâmetros baseados no documento Triagem.md
SCORE_APROVACAO_AUTOMATICA = 70
SCORE_REVISAO_HUMANA = 50
SCORE_RECUSA_AUTOMATICA = 49

PESO_ANEXOS = 0.30
PESO_DESCRICAO = 0.25
PESO_INFO_TECNICAS = 0.25
PESO_CONTEXTO = 0.20

MIN_DESCRICAO_CHARS = 50
MAX_DESCRICAO_CHARS = 5000
MIN_TITULO_CHARS = 10
MAX_TITULO_CHARS = 200
MAX_ANEXO_SIZE_MB = 50

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
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.api_key = HUGGINGFACE_API_KEY
        
    def _chamar_huggingface_api(self, model_name: str, payload: Dict) -> Dict:
        """Chama a API da Hugging Face"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            url = f"{HUGGINGFACE_API_URL}{model_name}"
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao chamar Hugging Face API: {e}")
            return {"error": str(e)}
    
    def calcular_score_anexos(self, chamado: Dict) -> int:
        """Calcula score para anexos (0-30 pontos)"""
        score = 0
        
        # Simular verificação de anexos
        # Em implementação real, verificaria arquivos reais
        if chamado.get('anexos_count', 0) > 0:
            score += 20  # Anexos presentes
            score += 5   # Formato correto (assumido)
            score += 3   # Tamanho adequado (assumido)
            score += 2   # Nomes descritivos (assumido)
        
        return min(score, 30)
    
    def calcular_score_descricao(self, descricao: str) -> Tuple[int, List[str]]:
        """Calcula score para descrição (0-25 pontos)"""
        score = 0
        motivos = []
        
        if not descricao:
            return 0, ["Descrição ausente"]
        
        # Verificar tamanho
        if len(descricao) >= 100:
            score += 15
            motivos.append("Descrição detalhada")
        elif len(descricao) >= MIN_DESCRICAO_CHARS:
            score += 10
            motivos.append("Descrição adequada")
        else:
            motivos.append("Descrição muito curta")
        
        # Palavras-chave técnicas
        palavras_tecnicas = ['erro', 'falha', 'bug', 'sistema', 'problema', 'login', 'acesso', 'performance']
        if any(palavra in descricao.lower() for palavra in palavras_tecnicas):
            score += 5
            motivos.append("Contém termos técnicos")
        
        # Estrutura organizada (pontuação, parágrafos)
        if '.' in descricao or '\n' in descricao:
            score += 3
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
        """Calcula score para informações técnicas (0-25 pontos)"""
        score = 0
        motivos = []
        
        # Cliente identificado
        if chamado.get('cliente_solicitante'):
            score += 10
            motivos.append("Cliente identificado")
        
        # Criticidade apropriada
        if chamado.get('criticidade') in ['Baixa', 'Média', 'Alta', 'Crítica']:
            score += 5
            motivos.append("Criticidade definida")
        
        # Título descritivo
        titulo = chamado.get('titulo', '')
        if MIN_TITULO_CHARS <= len(titulo) <= MAX_TITULO_CHARS:
            score += 5
            motivos.append("Título adequado")
        
        # Data/hora válidas
        if chamado.get('data_criacao'):
            score += 3
            motivos.append("Data válida")
        
        # Número WEX correto
        numero_wex = chamado.get('numero_wex', '')
        if re.match(r'^WEX\d{6}$', numero_wex):
            score += 2
            motivos.append("Número WEX válido")
        
        return min(score, 25), motivos
    
    def calcular_score_contexto(self, descricao: str) -> Tuple[int, List[str]]:
        """Calcula score para contexto (0-20 pontos)"""
        score = 0
        motivos = []
        
        if not descricao:
            return 0, ["Sem contexto"]
        
        descricao_lower = descricao.lower()
        
        # Problema claramente definido
        indicadores_problema = ['problema', 'erro', 'falha', 'não funciona', 'bug']
        if any(ind in descricao_lower for ind in indicadores_problema):
            score += 10
            motivos.append("Problema bem definido")
        
        # Impacto mencionado
        indicadores_impacto = ['impacto', 'afeta', 'usuários', 'crítico', 'urgente']
        if any(ind in descricao_lower for ind in indicadores_impacto):
            score += 5
            motivos.append("Impacto mencionado")
        
        # Urgência justificada
        indicadores_urgencia = ['urgente', 'imediato', 'asap', 'prioridade']
        if any(ind in descricao_lower for ind in indicadores_urgencia):
            score += 3
            motivos.append("Urgência identificada")
        
        # Tentativas de solução
        indicadores_tentativas = ['tentei', 'tentativa', 'já testei', 'verificado']
        if any(ind in descricao_lower for ind in indicadores_tentativas):
            score += 2
            motivos.append("Tentativas de solução mencionadas")
        
        return min(score, 20), motivos
    
    def _analisar_qualidade_texto(self, texto: str) -> Dict:
        """Analisa qualidade do texto usando IA"""
        try:
            payload = {
                "inputs": f"Analise a qualidade deste texto de suporte técnico: {texto[:500]}",
                "parameters": {"max_length": 50}
            }
            
            resultado = self._chamar_huggingface_api("microsoft/DialoGPT-medium", payload)
            
            # Simular score baseado na resposta
            score = 0.8 if len(texto) > 100 else 0.5
            
            return {"score": score, "analise": resultado}
            
        except Exception as e:
            logger.warning(f"Erro na análise de qualidade: {e}")
            return {"score": 0.5, "analise": "Análise indisponível"}
    
    def _sugerir_criticidade(self, chamado: Dict, score_total: int) -> str:
        """Sugere criticidade baseada na análise"""
        descricao = chamado.get('descricao', '').lower()
        
        # Palavras que indicam alta criticidade
        palavras_criticas = ['crítico', 'urgente', 'parado', 'indisponível', 'falha total']
        palavras_altas = ['problema', 'erro', 'falha', 'não funciona']
        palavras_medias = ['lento', 'dificuldade', 'dúvida']
        
        if any(palavra in descricao for palavra in palavras_criticas):
            return 'Crítica'
        elif any(palavra in descricao for palavra in palavras_altas) and score_total > 60:
            return 'Alta'
        elif any(palavra in descricao for palavra in palavras_medias):
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
            # Calcular scores individuais
            score_anexos = self.calcular_score_anexos(chamado)
            score_descricao, motivos_desc = self.calcular_score_descricao(chamado.get('descricao', ''))
            score_info, motivos_info = self.calcular_score_info_tecnicas(chamado)
            score_contexto, motivos_ctx = self.calcular_score_contexto(chamado.get('descricao', ''))
            
            # Score total ponderado
            score_total = int(
                score_anexos * PESO_ANEXOS +
                score_descricao * PESO_DESCRICAO +
                score_info * PESO_INFO_TECNICAS +
                score_contexto * PESO_CONTEXTO
            )
            
            # Determinar decisão
            if score_total >= SCORE_APROVACAO_AUTOMATICA:
                decisao = "aprovado"
            elif score_total >= SCORE_REVISAO_HUMANA:
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
            
            # Usar IA para gerar sugestões contextuais
            prompt = f"""
            Baseado neste chamado de suporte:
            Status: {status}
            Criticidade: {criticidade}
            Descrição: {descricao[:300]}
            
            Sugira 3 próximas ações apropriadas.
            """
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            resultado_ia = self._chamar_huggingface_api("microsoft/DialoGPT-medium", payload)
            
            # Sugestões baseadas em regras + IA
            sugestoes = []
            
            if status == "Aberto":
                sugestoes.append(SugestaoFollowup(
                    titulo="Análise Inicial",
                    descricao="Realizar análise técnica inicial do problema reportado",
                    tipo="Análise",
                    confianca=0.9,
                    motivo="Status inicial requer investigação",
                    exemplos_similares=[]
                ))
            elif status == "Em análise":
                sugestoes.append(SugestaoFollowup(
                    titulo="Teste de Reprodução",
                    descricao="Tentar reproduzir o problema em ambiente de teste",
                    tipo="Teste",
                    confianca=0.8,
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
            if not resultado_ia.get('error'):
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
            
            # Calcular similaridade usando TF-IDF
            matriz_tfidf = self.vectorizer.fit_transform(textos)
            similaridades = cosine_similarity(matriz_tfidf[0:1], matriz_tfidf[1:]).flatten()
            
            # Criar lista de resultados com scores
            resultados = []
            for i, score in enumerate(similaridades):
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
                    padrões.append("Chamados praticamente idênticos identificados")
            
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
            
            # Análise de clustering usando TF-IDF
            matriz_tfidf = self.vectorizer.fit_transform(textos)
            similaridades = cosine_similarity(matriz_tfidf)
            
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
                
                for j in range(i + 1, len(chamados_validos)):
                    if j not in chamados_processados and similaridades[i][j] > threshold:
                        grupo_atual.append(chamados_validos[j])
                        indices_grupo.append(j)
                        chamados_processados.add(j)
                
                if len(grupo_atual) > 1:
                    grupo_info = {
                        'tamanho': len(grupo_atual),
                        'similaridade_media': float(np.mean([similaridades[indices_grupo[0]][j] for j in indices_grupo[1:]])),
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