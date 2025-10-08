from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database import get_db, create_database
from models import Chamado, FollowUp, StatusChamado, CriticidadeChamado, TipoFollowUp
from schemas import (
    ChamadoResponse, ChamadoCreate, ChamadoUpdate, ChamadoFiltros,
    FollowUpResponse, FollowUpCreate, FollowUpUpdate,
    DashboardMetricas, TriagemAutomaticaResponse, SugestaoFollowUpResponse,
    ChamadosRelacionadosResponse, RelatorioIA
)
import json
import re
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_
import os
from collections import Counter
import math
# Importar nossa IA
from wex_ai_engine import wex_ai

# Configurar logging
logger = logging.getLogger(__name__)

# Configuração do lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_database()
    yield
    # Shutdown
    pass

# Criar instância do FastAPI
app = FastAPI(
    title="WEX Intelligence API",
    description="API para Sistema de Triagem Automática de Chamados",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
def read_root():
    return {"message": "WEX Intelligence API", "version": "1.0.0", "docs": "/docs", "interface": "http://localhost:3000"}

@app.get("/api/health")
def health_check():
    return {"message": "WEX Intelligence API is running!", "version": "1.0.0"}

# === ENDPOINTS DE CHAMADOS ===

@app.get("/chamados", response_model=dict)
def listar_chamados(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(20, ge=1, le=100, description="Limite de registros por página"),
    status: Optional[List[str]] = Query(None, description="Filtrar por status"),
    criticidade: Optional[List[str]] = Query(None, description="Filtrar por criticidade"),
    cliente: Optional[str] = Query(None, description="Filtrar por cliente"),
    busca_texto: Optional[str] = Query(None, description="Busca textual"),
    db: Session = Depends(get_db)
):
    """Listar todos os chamados com filtros e paginação"""
    
    query = db.query(Chamado)
    
    # Aplicar filtros
    if status:
        query = query.filter(Chamado.status.in_(status))
    
    if criticidade:
        query = query.filter(Chamado.criticidade.in_(criticidade))
    
    if cliente:
        query = query.filter(Chamado.cliente_solicitante.ilike(f"%{cliente}%"))
    
    if busca_texto:
        query = query.filter(
            or_(
                Chamado.descricao.ilike(f"%{busca_texto}%"),
                Chamado.numero_wex.ilike(f"%{busca_texto}%"),
                Chamado.cliente_solicitante.ilike(f"%{busca_texto}%")
            )
        )
    
    # Contar total de registros (antes da paginação)
    total = query.count()
    
    # Aplicar paginação e ordenação
    chamados = query.order_by(Chamado.data_criacao.desc()).offset(skip).limit(limit).all()
    
    # Converter para dict
    chamados_dict = [chamado.to_dict() for chamado in chamados]
    
    return {
        "chamados": chamados_dict,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }

@app.get("/chamados/{chamado_id}", response_model=dict)
def obter_chamado(chamado_id: int, db: Session = Depends(get_db)):
    """Obter detalhes de um chamado específico"""
    
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    return chamado.to_dict()

@app.post("/chamados", response_model=dict)
def criar_chamado(chamado: ChamadoCreate, db: Session = Depends(get_db)):
    """Criar um novo chamado"""
    
    # Verificar se número WEX já existe
    if db.query(Chamado).filter(Chamado.numero_wex == chamado.numero_wex).first():
        raise HTTPException(status_code=400, detail="Número WEX já existe")
    
    # Criar chamado
    db_chamado = Chamado(
        numero_wex=chamado.numero_wex,
        cliente_solicitante=chamado.cliente_solicitante,
        descricao=chamado.descricao,
        status=chamado.status.value,
        criticidade=chamado.criticidade.value,
        sla_limite=chamado.sla_limite,
        tags_automaticas=json.dumps(chamado.tags_automaticas),
        score_qualidade=chamado.score_qualidade,
        ambiente_informado=chamado.ambiente_informado,
        possui_anexos=chamado.possui_anexos
    )
    
    db.add(db_chamado)
    db.commit()
    db.refresh(db_chamado)
    
    return db_chamado.to_dict()

# === ENDPOINTS DE FOLLOW-UPS ===

@app.get("/chamados/{chamado_id}/followups", response_model=List[dict])
def listar_followups(chamado_id: int, db: Session = Depends(get_db)):
    """Listar follow-ups de um chamado"""
    
    # Verificar se chamado existe
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    followups = db.query(FollowUp).filter(
        FollowUp.chamado_id == chamado_id
    ).order_by(FollowUp.data_criacao.desc()).all()
    
    return [followup.to_dict() for followup in followups]

@app.post("/chamados/{chamado_id}/followups", response_model=dict)
def criar_followup(chamado_id: int, followup: FollowUpCreate, db: Session = Depends(get_db)):
    """Criar um novo follow-up para um chamado"""
    
    # Verificar se chamado existe
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Criar follow-up
    db_followup = FollowUp(
        chamado_id=chamado_id,
        tipo=followup.tipo.value,
        descricao=followup.descricao,
        autor=followup.autor,
        anexos=json.dumps(followup.anexos)
    )
    
    db.add(db_followup)
    db.commit()
    db.refresh(db_followup)
    
    return db_followup.to_dict()

# === ENDPOINTS DE DASHBOARD ===

@app.get("/dashboard/metricas", response_model=dict)
def obter_metricas_dashboard(db: Session = Depends(get_db)):
    """Obter métricas para o dashboard"""
    
    # Total de chamados por status
    status_counts = db.query(
        Chamado.status, func.count(Chamado.id)
    ).group_by(Chamado.status).all()
    
    total_por_status = {status: count for status, count in status_counts}
    
    # Chamados críticos em aberto
    chamados_criticos = db.query(Chamado).filter(
        and_(
            Chamado.criticidade == CriticidadeChamado.CRITICA.value,
            Chamado.status.in_([
                StatusChamado.ABERTO.value,
                StatusChamado.EM_ANALISE.value,
                StatusChamado.PENDENTE.value
            ])
        )
    ).count()
    
    # Distribuição por criticidade
    criticidade_counts = db.query(
        Chamado.criticidade, func.count(Chamado.id)
    ).group_by(Chamado.criticidade).all()
    
    distribuicao_criticidade = {crit: count for crit, count in criticidade_counts}
    
    # Chamados novos hoje
    hoje = datetime.now().date()
    chamados_hoje = db.query(Chamado).filter(
        func.date(Chamado.data_criacao) == hoje
    ).count()
    
    # Chamados vencidos (SLA ultrapassado)
    agora = datetime.now()
    chamados_vencidos = db.query(Chamado).filter(
        and_(
            Chamado.sla_limite < agora,
            Chamado.status.in_([
                StatusChamado.ABERTO.value,
                StatusChamado.EM_ANALISE.value,
                StatusChamado.PENDENTE.value
            ])
        )
    ).count()
    
    # Tempo médio de resolução (chamados resolvidos nos últimos 30 dias)
    trinta_dias_atras = datetime.now() - timedelta(days=30)
    chamados_resolvidos = db.query(Chamado).filter(
        and_(
            Chamado.status == StatusChamado.RESOLVIDO.value,
            Chamado.data_atualizacao >= trinta_dias_atras
        )
    ).all()
    
    tempo_medio = None
    if chamados_resolvidos:
        tempos = []
        for chamado in chamados_resolvidos:
            if chamado.data_criacao and chamado.data_atualizacao:
                diff = chamado.data_atualizacao - chamado.data_criacao
                tempos.append(diff.total_seconds() / 3600)  # em horas
        
        if tempos:
            tempo_medio = sum(tempos) / len(tempos)
    
    return {
        "total_chamados_por_status": total_por_status,
        "chamados_criticos_abertos": chamados_criticos,
        "tempo_medio_resolucao": tempo_medio,
        "distribuicao_por_criticidade": distribuicao_criticidade,
        "chamados_novos_hoje": chamados_hoje,
        "chamados_vencidos": chamados_vencidos
    }

# ====== SISTEMA DE IA - TRIAGEM AUTOMÁTICA ======

def extrair_indicadores_criticidade(descricao: str, numero_wex: str, cliente: str) -> Dict[str, Any]:
    """Extrai indicadores de criticidade de um chamado"""
    
    # Palavras-chave por nível de criticidade
    palavras_criticas = [
        "parado", "travado", "não funciona", "indisponível", "erro crítico",
        "sistema fora", "down", "crash", "quebrado", "não consegue",
        "urgente", "emergência", "produção parada", "impacto alto",
        "falha total", "sem acesso"
    ]
    
    palavras_altas = [
        "lento", "problema", "erro", "falha", "demora", "timeout",
        "performance", "não carrega", "instável", "intermitente",
        "dificuldade", "bloqueio", "limitação", "pendência"
    ]
    
    palavras_medias = [
        "dúvida", "ajuda", "como", "orientação", "suporte",
        "configuração", "permissão", "acesso", "tutorial",
        "explicação", "procedimento"
    ]
    
    palavras_baixas = [
        "melhoria", "sugestão", "otimização", "enhancement",
        "feature", "gostaria", "poderia", "seria possível",
        "futuro", "versão", "atualização"
    ]
    
    descricao_lower = descricao.lower()
    
    # Contar ocorrências por categoria
    count_critica = sum(1 for palavra in palavras_criticas if palavra in descricao_lower)
    count_alta = sum(1 for palavra in palavras_altas if palavra in descricao_lower)
    count_media = sum(1 for palavra in palavras_medias if palavra in descricao_lower)
    count_baixa = sum(1 for palavra in palavras_baixas if palavra in descricao_lower)
    
    # Verificar indicadores contextuais
    fatores = []
    
    # Horário de abertura (assumindo que chamados fora do horário comercial são mais críticos)
    agora = datetime.now()
    if agora.hour < 8 or agora.hour > 18 or agora.weekday() >= 5:
        fatores.append("Abertura fora do horário comercial")
        count_critica += 0.5
    
    # Cliente específico (alguns clientes podem ter prioridade)
    if "vip" in cliente.lower() or "premium" in cliente.lower():
        fatores.append("Cliente prioritário identificado")
        count_alta += 1
    
    # Ambiente mencionado
    ambientes_criticos = ["produção", "prod", "production", "prd"]
    if any(amb in descricao_lower for amb in ambientes_criticos):
        fatores.append("Ambiente de produção mencionado")
        count_critica += 1
    
    # Números/códigos de erro
    if re.search(r'erro\s*\d+|error\s*\d+|\d{3,4}\s*erro', descricao_lower):
        fatores.append("Código de erro específico mencionado")
        count_alta += 0.5
    
    # Determinar criticidade sugerida
    scores = {
        'critica': count_critica,
        'alta': count_alta,
        'media': count_media,
        'baixa': count_baixa
    }
    
    criticidade_sugerida = max(scores, key=scores.get)
    confianca = min(scores[criticidade_sugerida] / max(len(descricao.split()) * 0.1, 1), 1.0)
    
    # Mapear para enum
    mapa_criticidade = {
        'critica': CriticidadeChamado.CRITICA,
        'alta': CriticidadeChamado.ALTA,
        'media': CriticidadeChamado.MEDIA,
        'baixa': CriticidadeChamado.BAIXA
    }
    
    return {
        'criticidade': mapa_criticidade[criticidade_sugerida],
        'confianca': confianca,
        'fatores': fatores,
        'scores': scores
    }

def calcular_score_qualidade(descricao: str, numero_wex: str, cliente: str) -> int:
    """Calcula score de qualidade do chamado (0-100)"""
    score = 50  # Base
    
    # Critérios de qualidade
    if len(descricao) > 50:
        score += 15  # Descrição detalhada
    
    if len(descricao) > 200:
        score += 10  # Descrição muito detalhada
    
    # Informações estruturadas
    if re.search(r'passos|steps|procedimento|reproduz', descricao.lower()):
        score += 15  # Passos para reproduzir
    
    if re.search(r'erro|error|mensagem', descricao.lower()):
        score += 10  # Mensagem de erro mencionada
    
    if re.search(r'ambiente|versão|browser|sistema', descricao.lower()):
        score += 10  # Informações de ambiente
    
    if re.search(r'anexo|print|imagem|log', descricao.lower()):
        score += 10  # Indica anexos/evidências
    
    # Penalizações
    if len(descricao) < 20:
        score -= 25  # Descrição muito curta
    
    if descricao.lower().count('não funciona') > 0 and len(descricao) < 50:
        score -= 15  # Descrição genérica
    
    return max(0, min(100, score))

def sugerir_tags_automaticas(descricao: str, numero_wex: str, cliente: str) -> List[str]:
    """Sugere tags automáticas baseadas no conteúdo"""
    tags = []
    descricao_lower = descricao.lower()
    
    # Tags por categoria
    if any(word in descricao_lower for word in ['login', 'acesso', 'senha', 'autenticação']):
        tags.append('acesso')
    
    if any(word in descricao_lower for word in ['relatório', 'dashboard', 'gráfico', 'dados']):
        tags.append('relatórios')
    
    if any(word in descricao_lower for word in ['lento', 'performance', 'demora', 'timeout']):
        tags.append('performance')
    
    if any(word in descricao_lower for word in ['integração', 'api', 'webservice', 'importação']):
        tags.append('integração')
    
    if any(word in descricao_lower for word in ['mobile', 'celular', 'app', 'android', 'ios']):
        tags.append('mobile')
    
    if any(word in descricao_lower for word in ['browser', 'chrome', 'firefox', 'internet']):
        tags.append('web')
    
    if any(word in descricao_lower for word in ['permissão', 'perfil', 'usuário', 'grupo']):
        tags.append('permissões')
    
    if any(word in descricao_lower for word in ['banco', 'database', 'sql', 'consulta']):
        tags.append('banco-dados')
    
    return tags

# ================== TRIAGEM AUTOMÁTICA ==================

@app.post("/api/chamados/triagem-automatica", response_model=dict)
async def triagem_automatica_nova(request: dict):
    """Executa triagem automática para dados de um novo chamado usando IA real"""
    
    try:
        # Validar dados obrigatórios
        if not request.get('descricao'):
            raise HTTPException(status_code=400, detail="Descrição é obrigatória")
        if not request.get('numero_wex'):
            raise HTTPException(status_code=400, detail="Número WEX é obrigatório")
        if not request.get('cliente_solicitante'):
            raise HTTPException(status_code=400, detail="Cliente solicitante é obrigatório")
        
        # Estruturar dados do chamado
        chamado_dict = {
            'numero_wex': request.get('numero_wex'),
            'titulo': f"Chamado {request.get('numero_wex')}",
            'descricao': request.get('descricao'),
            'cliente_solicitante': request.get('cliente_solicitante'),
            'criticidade': request.get('criticidade', 'Média'),
            'status': 'Aberto'
        }
        
        # Executar triagem com IA real
        resultado_triagem = wex_ai.realizar_triagem(chamado_dict)
        
        # Determinar se deve ser aceito (score > 50 baseado no documento Triagem.md)
        aceito = resultado_triagem.score_total > 50
        decisao = "aceito" if aceito else "recusado"
        
        return {
            "numero_wex": request.get('numero_wex'),
            "score": resultado_triagem.score_total,
            "decisao": decisao,
            "justificativa": resultado_triagem.observacoes,
            "motivos": resultado_triagem.motivos,
            "criticidade_sugerida": resultado_triagem.criticidade_sugerida,
            "prioridade_sugerida": "Alta" if resultado_triagem.score_total > 70 else "Média",
            "categoria_sugerida": "Técnico",
            "tempo_resposta_estimado": "4 horas" if resultado_triagem.score_total > 70 else "24 horas",
            "departamento_sugerido": "Suporte",
            "tags_sugeridas": resultado_triagem.tags_sugeridas,
            "sugestoes_melhoria": resultado_triagem.sugestoes,
            "observacoes": resultado_triagem.observacoes,
            "score_qualidade_atual": resultado_triagem.score_total,
            "score_qualidade_sugerido": resultado_triagem.score_total,
            "tempo_processamento_ms": resultado_triagem.tempo_processamento_ms,
            "ia_utilizada": True,
            "metadados_ia": {
                "modelo_usado": "wex-ai-engine",
                "tempo_processamento": resultado_triagem.tempo_processamento_ms / 1000,
                "confianca_analise": resultado_triagem.confianca
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na triagem automática: {str(e)}")
        return {
            "numero_wex": request.get('numero_wex', 'N/A'),
            "score": 5,  # Score médio como fallback
            "decisao": "necessita_revisao",
            "justificativa": f"Erro na análise automática: {str(e)}",
            "criticidade_sugerida": request.get('criticidade', 'Média'),
            "prioridade_sugerida": "Média",
            "categoria_sugerida": "Técnico",
            "tempo_resposta_estimado": "24 horas",
            "departamento_sugerido": "Suporte",
            "tags_sugeridas": [],
            "sugestoes_melhoria": [],
            "observacoes": f"Sistema de IA temporariamente indisponível. Revisar manualmente.",
            "score_qualidade_atual": 0,
            "score_qualidade_sugerido": 0,
            "tempo_processamento_ms": 0,
            "ia_utilizada": False,
            "erro_ia": str(e),
            "metadados_ia": {
                "modelo_usado": "fallback",
                "tempo_processamento": 0,
                "confianca_analise": 0
            }
        }

@app.post("/api/chamados/{chamado_id}/triagem", response_model=dict)
async def triagem_automatica(chamado_id: int, db: Session = Depends(get_db)):
    """Executa triagem automática de um chamado específico usando IA real"""
    
    try:
        # Buscar o chamado
        chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
        if not chamado:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")
        
        # Converter chamado para dict para a IA
        chamado_dict = {
            'id': chamado.id,
            'numero_wex': chamado.numero_wex,
            'titulo': f"Chamado {chamado.numero_wex}",  # Usar número WEX como título
            'descricao': chamado.descricao,
            'cliente_solicitante': chamado.cliente_solicitante,
            'criticidade': chamado.criticidade.value if hasattr(chamado.criticidade, 'value') else str(chamado.criticidade),
            'status': chamado.status.value if hasattr(chamado.status, 'value') else str(chamado.status),
            'data_criacao': chamado.data_criacao.isoformat() if chamado.data_criacao else None,
            'anexos_count': 0  # Simular contagem de anexos
        }
        
        # Executar triagem com IA real
        resultado_triagem = wex_ai.realizar_triagem(chamado_dict)
        
        return {
            "id_chamado": chamado_id,
            "score_total": resultado_triagem.score_total,
            "score_breakdown": resultado_triagem.score_breakdown,
            "decisao": resultado_triagem.decisao,
            "criticidade_atual": chamado.criticidade.value if hasattr(chamado.criticidade, 'value') else str(chamado.criticidade),
            "criticidade_sugerida": resultado_triagem.criticidade_sugerida,
            "confianca": resultado_triagem.confianca,
            "fatores_identificados": resultado_triagem.motivos,
            "sugestoes_melhoria": resultado_triagem.sugestoes,
            "tags_sugeridas": resultado_triagem.tags_sugeridas,
            "tempo_processamento_ms": resultado_triagem.tempo_processamento_ms,
            "observacoes": resultado_triagem.observacoes,
            "score_qualidade_atual": getattr(chamado, 'score_qualidade', 0) or 0,
            "score_qualidade_sugerido": resultado_triagem.score_total,
            "metadados_ia": {
                "modelo_usado": "wex-ai-engine",
                "tempo_processamento": resultado_triagem.tempo_processamento_ms / 1000.0,
                "confianca_analise": resultado_triagem.confianca
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na triagem automática: {str(e)}")
        return {
            "id_chamado": chamado_id,
            "score_total": 0,
            "score_breakdown": {},
            "decisao": "erro",
            "criticidade_atual": "N/A",
            "criticidade_sugerida": "N/A",
            "confianca": 0.0,
            "fatores_identificados": [],
            "sugestoes_melhoria": [],
            "tags_sugeridas": [],
            "tempo_processamento_ms": 0,
            "observacoes": f"Erro na análise de IA: {str(e)}",
            "score_qualidade_atual": 0,
            "score_qualidade_sugerido": 0,
            "erro_ia": str(e),
            "metadados_ia": {
                "modelo_usado": "fallback",
                "tempo_processamento": 0,
                "confianca_analise": 0
            }
        }

@app.post("/api/triagem/aplicar/{chamado_id}")
async def aplicar_triagem(chamado_id: int, db: Session = Depends(get_db)):
    """Aplica as sugestões da triagem automática ao chamado usando IA real"""
    
    # Buscar o chamado
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Converter chamado para dict
    chamado_dict = {
        'id': chamado.id,
        'numero_wex': chamado.numero_wex,
        'titulo': f"Chamado {chamado.numero_wex}",
        'descricao': chamado.descricao,
        'cliente_solicitante': chamado.cliente_solicitante,
        'criticidade': chamado.criticidade.value if chamado.criticidade else 'Média',
        'status': chamado.status.value if chamado.status else 'Aberto',
        'data_criacao': chamado.data_criacao.isoformat() if chamado.data_criacao else None,
        'anexos_count': 0
    }
    
    # Executar triagem com IA
    resultado_triagem = wex_ai.realizar_triagem(chamado_dict)
    
    # Aplicar mudanças apenas se a decisão for "aprovado" ou "revisao"
    if resultado_triagem.decisao in ["aprovado", "revisao"]:
        criticidade_anterior = chamado.criticidade.value if chamado.criticidade else 'Média'
        
        # Mapear criticidade sugerida para enum
        criticidade_map = {
            'Baixa': CriticidadeChamado.BAIXA,
            'Média': CriticidadeChamado.MEDIA,
            'Alta': CriticidadeChamado.ALTA,
            'Crítica': CriticidadeChamado.CRITICA
        }
        
        nova_criticidade = criticidade_map.get(resultado_triagem.criticidade_sugerida, CriticidadeChamado.MEDIA)
        
        # Aplicar mudanças
        chamado.criticidade = nova_criticidade
        chamado.score_qualidade = resultado_triagem.score_total
        if resultado_triagem.tags_sugeridas:
            chamado.tags_automaticas = resultado_triagem.tags_sugeridas
        
        # Adicionar observação da IA
        observacao_ia = f"Triagem IA: Score {resultado_triagem.score_total}/100, Decisão: {resultado_triagem.decisao}"
        if hasattr(chamado, 'observacoes_ia'):
            chamado.observacoes_ia = observacao_ia
        
        db.commit()
        db.refresh(chamado)
        
        return {
            "success": True,
            "chamado_id": chamado_id,
            "decisao_ia": resultado_triagem.decisao,
            "score_final": resultado_triagem.score_total,
            "mudancas": {
                "criticidade": {
                    "anterior": criticidade_anterior,
                    "nova": nova_criticidade.value
                },
                "score_qualidade": resultado_triagem.score_total,
                "tags_adicionadas": resultado_triagem.tags_sugeridas
            },
            "motivos": resultado_triagem.motivos,
            "tempo_processamento": resultado_triagem.tempo_processamento_ms
        }
    else:
        return {
            "success": False,
            "chamado_id": chamado_id,
            "decisao_ia": resultado_triagem.decisao,
            "score_final": resultado_triagem.score_total,
            "motivo_recusa": "Chamado não atende aos critérios mínimos de qualidade",
            "sugestoes_melhoria": resultado_triagem.sugestoes,
            "score_necessario": 50
        }

# ====== SISTEMA DE SUGESTÕES DE FOLLOW-UP ======

def analisar_contexto_chamado(chamado: Chamado, db: Session) -> Dict[str, Any]:
    """Analisa o contexto do chamado para sugerir follow-ups apropriados"""
    
    # Buscar follow-ups existentes do chamado
    followups_existentes = db.query(FollowUp).filter(
        FollowUp.chamado_id == chamado.id
    ).order_by(FollowUp.data_criacao.desc()).all()
    
    # Analisar padrão de follow-ups
    tipos_existentes = [f.tipo for f in followups_existentes]
    
    # Tempo desde último follow-up
    tempo_desde_ultimo = None
    if followups_existentes:
        ultimo_followup = followups_existentes[0]
        tempo_desde_ultimo = (datetime.now() - ultimo_followup.data_criacao).total_seconds() / 3600  # horas
    
    # Tempo desde criação do chamado
    tempo_desde_criacao = (datetime.now() - chamado.data_criacao).total_seconds() / 3600  # horas
    
    return {
        'followups_existentes': followups_existentes,
        'tipos_existentes': tipos_existentes,
        'tempo_desde_ultimo': tempo_desde_ultimo,
        'tempo_desde_criacao': tempo_desde_criacao,
        'total_followups': len(followups_existentes)
    }

def gerar_sugestoes_followup(chamado: Chamado, contexto: Dict[str, Any]) -> Dict[str, Any]:
    """Gera sugestões inteligentes de follow-up baseadas no contexto"""
    
    sugestoes = []
    proximo_tipo = TipoFollowUp.OUTROS
    prioridade = "media"
    
    descricao_lower = chamado.descricao.lower()
    status = chamado.status
    criticidade = chamado.criticidade
    tempo_desde_criacao = contexto['tempo_desde_criacao']
    tempo_desde_ultimo = contexto['tempo_desde_ultimo']
    tipos_existentes = contexto['tipos_existentes']
    
    # Lógica baseada no status atual
    if status == StatusChamado.ABERTO:
        if not tipos_existentes or TipoFollowUp.ANALISE_INICIAL not in tipos_existentes:
            sugestoes.append("Realizar análise inicial do problema reportado")
            proximo_tipo = TipoFollowUp.ANALISE_INICIAL
            prioridade = "alta"
        elif TipoFollowUp.CONTATO_CLIENTE not in tipos_existentes:
            sugestoes.append("Entrar em contato com cliente para esclarecimentos adicionais")
            proximo_tipo = TipoFollowUp.CONTATO_CLIENTE
            prioridade = "alta"
        else:
            sugestoes.append("Iniciar investigação técnica detalhada")
            proximo_tipo = TipoFollowUp.ANALISE_TECNICA
    
    elif status == StatusChamado.EM_ANALISE:
        if TipoFollowUp.ANALISE_TECNICA not in tipos_existentes:
            sugestoes.append("Documentar análise técnica e achados preliminares")
            proximo_tipo = TipoFollowUp.ANALISE_TECNICA
        elif "teste" in descricao_lower or "reproduz" in descricao_lower:
            sugestoes.append("Executar testes para reproduzir o problema")
            proximo_tipo = TipoFollowUp.TESTE
        else:
            sugestoes.append("Atualizar status da investigação em andamento")
            proximo_tipo = TipoFollowUp.ATUALIZACAO_STATUS
    
    elif status == StatusChamado.PENDENTE:
        if tempo_desde_ultimo and tempo_desde_ultimo > 24:  # Mais de 24h sem follow-up
            sugestoes.append("Cobrar retorno do cliente - chamado pendente há mais de 24 horas")
            proximo_tipo = TipoFollowUp.CONTATO_CLIENTE
            prioridade = "alta"
        else:
            sugestoes.append("Acompanhar pendências em aberto")
            proximo_tipo = TipoFollowUp.ATUALIZACAO_STATUS
    
    elif status == StatusChamado.DESENVOLVIMENTO:
        if TipoFollowUp.DESENVOLVIMENTO not in tipos_existentes:
            sugestoes.append("Documentar início do desenvolvimento da solução")
            proximo_tipo = TipoFollowUp.DESENVOLVIMENTO
        else:
            sugestoes.append("Atualizar progresso do desenvolvimento")
            proximo_tipo = TipoFollowUp.ATUALIZACAO_STATUS
    
    elif status == StatusChamado.TESTE:
        if TipoFollowUp.TESTE not in tipos_existentes:
            sugestoes.append("Documentar execução dos testes da solução")
            proximo_tipo = TipoFollowUp.TESTE
        else:
            sugestoes.append("Validar resultados dos testes com cliente")
            proximo_tipo = TipoFollowUp.CONTATO_CLIENTE
    
    # Sugestões baseadas na criticidade
    if criticidade == CriticidadeChamado.CRITICA:
        if tempo_desde_ultimo is None or tempo_desde_ultimo > 2:  # Mais de 2h sem update
            sugestoes.insert(0, "URGENTE: Atualizar status - chamado crítico sem follow-up recente")
            prioridade = "alta"
    
    elif criticidade == CriticidadeChamado.ALTA:
        if tempo_desde_ultimo is None or tempo_desde_ultimo > 8:  # Mais de 8h sem update
            sugestoes.insert(0, "Priorizar atualização - chamado de alta criticidade")
            prioridade = "alta"
    
    # Sugestões baseadas no tempo
    if tempo_desde_criacao > 72:  # Mais de 3 dias
        sugestoes.append("Reavaliar criticidade e estratégia - chamado em aberto há mais de 3 dias")
        if prioridade != "alta":
            prioridade = "media"
    
    # Sugestões baseadas no conteúdo
    if any(word in descricao_lower for word in ['erro', 'bug', 'falha', 'problema']):
        if TipoFollowUp.ANALISE_TECNICA not in tipos_existentes:
            sugestoes.append("Realizar análise técnica detalhada do erro reportado")
    
    if any(word in descricao_lower for word in ['integração', 'api', 'webservice']):
        sugestoes.append("Verificar logs de integração e conectividade")
    
    if any(word in descricao_lower for word in ['performance', 'lento', 'demora']):
        sugestoes.append("Executar análise de performance e benchmarks")
    
    # Limitár número de sugestões
    sugestoes = sugestoes[:5]
    
    return {
        'sugestoes': sugestoes,
        'proximo_tipo': proximo_tipo,
        'prioridade': prioridade
    }

def buscar_followups_similares(chamado: Chamado, db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """Busca follow-ups de chamados similares para sugerir baseado no histórico"""
    
    # Buscar chamados com descrições similares (palavras-chave)
    palavras_chave = set(re.findall(r'\b\w{4,}\b', chamado.descricao.lower()))
    
    chamados_similares = db.query(Chamado).filter(
        and_(
            Chamado.id != chamado.id,
            Chamado.status == StatusChamado.RESOLVIDO  # Apenas chamados resolvidos
        )
    ).limit(50).all()  # Buscar mais para filtrar depois
    
    # Calcular similaridade baseada em palavras-chave
    candidatos = []
    for c in chamados_similares:
        palavras_candidato = set(re.findall(r'\b\w{4,}\b', c.descricao.lower()))
        intersecao = palavras_chave.intersection(palavras_candidato)
        
        if len(intersecao) >= 2:  # Pelo menos 2 palavras em comum
            score = len(intersecao) / len(palavras_chave.union(palavras_candidato))
            candidatos.append({
                'chamado': c,
                'score': score,
                'palavras_comuns': list(intersecao)
            })
    
    # Ordenar por score e pegar os melhores
    candidatos.sort(key=lambda x: x['score'], reverse=True)
    
    # Buscar follow-ups dos chamados similares
    followups_exemplos = []
    for candidato in candidatos[:limit]:
        followups = db.query(FollowUp).filter(
            FollowUp.chamado_id == candidato['chamado'].id
        ).order_by(FollowUp.data_criacao).all()
        
        if followups:
            followups_exemplos.append({
                'chamado_similar_id': candidato['chamado'].id,
                'score_similaridade': candidato['score'],
                'palavras_comuns': candidato['palavras_comuns'],
                'followups': [{'tipo': f.tipo.value, 'descricao': f.descricao[:100]} for f in followups]
            })
    
    return followups_exemplos

@app.get("/api/chamados/{chamado_id}/sugestoes-followup", response_model=dict)
async def sugestoes_followup(chamado_id: int, db: Session = Depends(get_db)):
    """Gera sugestões inteligentes para próximos follow-ups usando IA real"""
    
    try:
        # Buscar o chamado
        chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
        if not chamado:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")
        
        # Buscar follow-ups existentes do chamado
        followups_existentes = db.query(FollowUp).filter(
            FollowUp.chamado_id == chamado.id
        ).order_by(FollowUp.data_criacao.desc()).all()
        
        # Buscar chamados similares para contexto
        todos_chamados = db.query(Chamado).filter(Chamado.id != chamado_id).all()
        chamados_similares = []
        for c in todos_chamados[:20]:  # Limitar para performance
            chamados_similares.append({
                'id': c.id,
                'numero_wex': c.numero_wex,
                'descricao': c.descricao,
                'cliente_solicitante': c.cliente_solicitante,
                'criticidade': c.criticidade.value if hasattr(c.criticidade, 'value') else str(c.criticidade),
                'status': c.status.value if hasattr(c.status, 'value') else str(c.status)
            })
        
        # Converter chamado para dict
        chamado_dict = {
            'id': chamado.id,
            'numero_wex': chamado.numero_wex,
            'titulo': f"Chamado {chamado.numero_wex}",
            'descricao': chamado.descricao,
            'cliente_solicitante': chamado.cliente_solicitante,
            'criticidade': chamado.criticidade.value if hasattr(chamado.criticidade, 'value') else str(chamado.criticidade),
            'status': chamado.status.value if hasattr(chamado.status, 'value') else str(chamado.status),
            'data_criacao': chamado.data_criacao.isoformat() if chamado.data_criacao else None
        }
        
        # Gerar sugestões com IA
        sugestoes_ia = wex_ai.gerar_sugestoes_followup(chamado_dict, chamados_similares)
        
        # Calcular tempo desde criação e último follow-up
        agora = datetime.now()
        tempo_desde_criacao = int((agora - chamado.data_criacao).total_seconds() / 3600) if chamado.data_criacao else 0
        tempo_desde_ultimo = 0
        if followups_existentes:
            tempo_desde_ultimo = int((agora - followups_existentes[0].data_criacao).total_seconds() / 3600)
        
        # Buscar exemplos similares
        exemplos_historico = []
        if chamados_similares:
            for similar in chamados_similares[:3]:
                followups_similares = db.query(FollowUp).filter(
                    FollowUp.chamado_id == similar['id']
                ).limit(2).all()
                if followups_similares:
                    exemplos_historico.append({
                        'chamado_numero': similar['numero_wex'],
                        'cliente': similar['cliente_solicitante'],
                        'similaridade': 0.75,  # Score simulado
                        'followups': [
                            {
                                'tipo': f.tipo.value if hasattr(f.tipo, 'value') else str(f.tipo),
                                'descricao': f.descricao[:100] + "..." if len(f.descricao) > 100 else f.descricao
                            } for f in followups_similares
                        ]
                    })
        
        # Determinar próximo tipo sugerido baseado na IA
        proximo_tipo = "Análise"  # Default
        if sugestoes_ia:
            primeiro_tipo = sugestoes_ia[0].tipo
            if primeiro_tipo in ["Análise", "Comunicação", "Teste", "Resolução"]:
                proximo_tipo = primeiro_tipo
        
        return {
            "id_chamado": chamado_id,
            "sugestoes": [
                {
                    "titulo": s.titulo,
                    "descricao": s.descricao,
                    "tipo": s.tipo,
                    "confianca": s.confianca,
                    "motivo": s.motivo
                } for s in sugestoes_ia
            ],
            "proximo_tipo_sugerido": proximo_tipo,
            "prioridade": "Alta" if str(chamado.criticidade) in ["Alta", "Crítica"] else "Média",
            "contexto": {
                "status_atual": chamado.status.value if hasattr(chamado.status, 'value') else str(chamado.status),
                "criticidade": chamado.criticidade.value if hasattr(chamado.criticidade, 'value') else str(chamado.criticidade),
                "tempo_desde_criacao_horas": tempo_desde_criacao,
                "tempo_desde_ultimo_followup_horas": tempo_desde_ultimo,
                "total_followups_existentes": len(followups_existentes)
            },
            "exemplos_historico": exemplos_historico,
            "tipos_followup_existentes": [f.tipo.value if hasattr(f.tipo, 'value') else str(f.tipo) for f in followups_existentes],
            "metadados_ia": {
                "sugestoes_geradas": len(sugestoes_ia),
                "contexto_usado": len(chamados_similares),
                "modelo_usado": "wex-ai-engine",
                "tempo_processamento": 0.1,
                "confianca_analise": sum(s.confianca for s in sugestoes_ia) / len(sugestoes_ia) if sugestoes_ia else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar sugestões: {str(e)}")
        return {
            "id_chamado": chamado_id,
            "sugestoes": [],
            "proximo_tipo_sugerido": "Análise",
            "prioridade": "Média",
            "contexto": {
                "status_atual": "N/A",
                "criticidade": "N/A",
                "tempo_desde_criacao_horas": 0,
                "tempo_desde_ultimo_followup_horas": 0,
                "total_followups_existentes": 0
            },
            "exemplos_historico": [],
            "tipos_followup_existentes": [],
            "erro_ia": str(e),
            "metadados_ia": {
                "sugestoes_geradas": 0,
                "contexto_usado": 0,
                "modelo_usado": "fallback",
                "tempo_processamento": 0,
                "confianca_analise": 0
            }
        }

@app.post("/api/chamados/{chamado_id}/followup-sugerido")
async def criar_followup_sugerido(
    chamado_id: int, 
    sugestao_index: int,
    autor: str,
    db: Session = Depends(get_db)
):
    """Cria um follow-up baseado em uma sugestão específica"""
    
    # Buscar o chamado
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Gerar sugestões para pegar a específica
    contexto = analisar_contexto_chamado(chamado, db)
    sugestoes_result = gerar_sugestoes_followup(chamado, contexto)
    
    if sugestao_index >= len(sugestoes_result['sugestoes']):
        raise HTTPException(status_code=400, detail="Índice de sugestão inválido")
    
    descricao_sugerida = sugestoes_result['sugestoes'][sugestao_index]
    tipo_sugerido = sugestoes_result['proximo_tipo']
    
    # Criar o follow-up
    novo_followup = FollowUp(
        chamado_id=chamado_id,
        tipo=tipo_sugerido,
        descricao=f"[SUGESTÃO IA] {descricao_sugerida}",
        autor=autor,
        anexos=[]
    )
    
    db.add(novo_followup)
    db.commit()
    db.refresh(novo_followup)
    
    return {
        "success": True,
        "followup_criado": {
            "id": novo_followup.id,
            "tipo": novo_followup.tipo.value,
            "descricao": novo_followup.descricao,
            "autor": novo_followup.autor,
            "data_criacao": novo_followup.data_criacao
        }
    }

# ====== SISTEMA DE RELACIONAMENTO ENTRE CHAMADOS ======

def extrair_features_textuais(texto: str) -> Dict[str, Any]:
    """Extrai features de um texto para comparação"""
    texto_lower = texto.lower()
    
    # Remover stopwords básicas
    stopwords = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'do', 'da', 'dos', 'das',
        'e', 'ou', 'mas', 'se', 'que', 'com', 'por', 'para', 'em', 'no', 'na', 'nos', 'nas',
        'é', 'são', 'foi', 'foram', 'ser', 'estar', 'tem', 'ter', 'não', 'sim'
    }
    
    # Extrair palavras significativas
    palavras = set(re.findall(r'\b\w{3,}\b', texto_lower))
    palavras_significativas = palavras - stopwords
    
    # Extrair termos técnicos (palavras com maiúsculas, números, etc.)
    termos_tecnicos = set(re.findall(r'\b[A-Z][a-zA-Z]*\b|\b\w*\d+\w*\b', texto))
    
    # Extrair códigos de erro
    codigos_erro = set(re.findall(r'erro\s*\d+|error\s*\d+|\d{3,5}', texto_lower))
    
    # Extrair mensagens de erro (texto entre aspas)
    mensagens_erro = set(re.findall(r'"([^"]*)"', texto))
    
    return {
        'palavras_significativas': palavras_significativas,
        'termos_tecnicos': termos_tecnicos,
        'codigos_erro': codigos_erro,
        'mensagens_erro': mensagens_erro,
        'tamanho_texto': len(texto),
        'num_palavras': len(palavras)
    }

def calcular_similaridade_chamados(chamado1: Chamado, chamado2: Chamado) -> Dict[str, float]:
    """Calcula similaridade entre dois chamados"""
    
    # Extrair features de ambos os chamados
    features1 = extrair_features_textuais(chamado1.descricao)
    features2 = extrair_features_textuais(chamado2.descricao)
    
    scores = {}
    
    # Similaridade de palavras significativas (Jaccard)
    palavras1 = features1['palavras_significativas']
    palavras2 = features2['palavras_significativas']
    if palavras1 or palavras2:
        intersecao = len(palavras1.intersection(palavras2))
        uniao = len(palavras1.union(palavras2))
        scores['palavras'] = intersecao / uniao if uniao > 0 else 0
    else:
        scores['palavras'] = 0
    
    # Similaridade de termos técnicos
    tecnicos1 = features1['termos_tecnicos']
    tecnicos2 = features2['termos_tecnicos']
    if tecnicos1 or tecnicos2:
        intersecao_tec = len(tecnicos1.intersection(tecnicos2))
        uniao_tec = len(tecnicos1.union(tecnicos2))
        scores['termos_tecnicos'] = intersecao_tec / uniao_tec if uniao_tec > 0 else 0
    else:
        scores['termos_tecnicos'] = 0
    
    # Similaridade de códigos de erro
    erros1 = features1['codigos_erro']
    erros2 = features2['codigos_erro']
    scores['codigos_erro'] = 1.0 if erros1.intersection(erros2) else 0
    
    # Similaridade de mensagens de erro
    msgs1 = features1['mensagens_erro']
    msgs2 = features2['mensagens_erro']
    scores['mensagens_erro'] = 1.0 if msgs1.intersection(msgs2) else 0
    
    # Similaridade de cliente
    scores['cliente'] = 1.0 if chamado1.cliente_solicitante.lower() == chamado2.cliente_solicitante.lower() else 0
    
    # Similaridade de criticidade
    scores['criticidade'] = 1.0 if chamado1.criticidade == chamado2.criticidade else 0
    
    # Score final ponderado
    peso_palavras = 0.3
    peso_tecnicos = 0.2
    peso_erros = 0.2
    peso_mensagens = 0.15
    peso_cliente = 0.1
    peso_criticidade = 0.05
    
    score_final = (
        scores['palavras'] * peso_palavras +
        scores['termos_tecnicos'] * peso_tecnicos +
        scores['codigos_erro'] * peso_erros +
        scores['mensagens_erro'] * peso_mensagens +
        scores['cliente'] * peso_cliente +
        scores['criticidade'] * peso_criticidade
    )
    
    scores['score_final'] = score_final
    
    return scores

def identificar_padroes_chamados(chamados_similares: List[Chamado]) -> List[str]:
    """Identifica padrões comuns em um grupo de chamados similares"""
    padroes = []
    
    if len(chamados_similares) < 2:
        return padroes
    
    # Análise de clientes
    clientes = [c.cliente_solicitante for c in chamados_similares]
    cliente_counts = Counter(clientes)
    cliente_mais_comum = cliente_counts.most_common(1)[0]
    if cliente_mais_comum[1] > 1:
        padroes.append(f"Múltiplos chamados do cliente: {cliente_mais_comum[0]}")
    
    # Análise de criticidade
    criticidades = [c.criticidade for c in chamados_similares]
    criticidade_counts = Counter(criticidades)
    crit_mais_comum = criticidade_counts.most_common(1)[0]
    if crit_mais_comum[1] / len(chamados_similares) > 0.6:
        padroes.append(f"Padrão de criticidade: {crit_mais_comum[0].value}")
    
    # Análise temporal
    datas = [c.data_criacao for c in chamados_similares]
    datas_ordenadas = sorted(datas)
    if len(datas_ordenadas) >= 3:
        # Verificar se há concentração temporal
        primeira = datas_ordenadas[0]
        ultima = datas_ordenadas[-1]
        diferenca_total = (ultima - primeira).days
        
        if diferenca_total <= 7:
            padroes.append("Chamados concentrados em período de 7 dias")
        elif diferenca_total <= 30:
            padroes.append("Chamados concentrados em período de 30 dias")
    
    # Análise de termos técnicos comuns
    todos_termos = []
    for chamado in chamados_similares:
        features = extrair_features_textuais(chamado.descricao)
        todos_termos.extend(features['termos_tecnicos'])
    
    if todos_termos:
        termo_counts = Counter(todos_termos)
        termos_frequentes = [termo for termo, count in termo_counts.items() if count > 1]
        if termos_frequentes:
            padroes.append(f"Termos técnicos recorrentes: {', '.join(termos_frequentes[:3])}")
    
    # Análise de códigos de erro
    todos_erros = []
    for chamado in chamados_similares:
        features = extrair_features_textuais(chamado.descricao)
        todos_erros.extend(features['codigos_erro'])
    
    if todos_erros:
        erro_counts = Counter(todos_erros)
        erros_recorrentes = [erro for erro, count in erro_counts.items() if count > 1]
        if erros_recorrentes:
            padroes.append(f"Códigos de erro recorrentes: {', '.join(erros_recorrentes)}")
    
    return padroes

@app.get("/api/chamados/{chamado_id}/relacionados", response_model=dict)
async def buscar_chamados_relacionados(
    chamado_id: int, 
    limite: int = Query(default=10, le=50),
    score_minimo: float = Query(default=0.3, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """Busca chamados relacionados/similares ao chamado especificado usando IA real"""
    
    try:
        # Buscar o chamado principal
        chamado_principal = db.query(Chamado).filter(Chamado.id == chamado_id).first()
        if not chamado_principal:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")
        
        # Buscar todos os outros chamados (exceto o atual)
        outros_chamados = db.query(Chamado).filter(
            Chamado.id != chamado_id
        ).all()
        
        # Usar IA real para encontrar chamados similares
        resultado_ia = wex_ai.encontrar_chamados_similares(
            chamado_principal=chamado_principal,
            outros_chamados=outros_chamados,
            limite=limite,
            score_minimo=score_minimo
        )
        
        # Formatar resultados para o frontend
        chamados_similares = []
        for chamado_similar in resultado_ia.chamados_similares:
            chamados_similares.append({
                'id': chamado_similar['id'],
                'numero_wex': chamado_similar['numero_wex'],
                'cliente': chamado_similar['cliente'],
                'descricao': chamado_similar['descricao'][:200] + "..." if len(chamado_similar['descricao']) > 200 else chamado_similar['descricao'],
                'status': chamado_similar['status'],
                'criticidade': chamado_similar['criticidade'],
                'data_criacao': chamado_similar['data_criacao'],
                'score_similaridade': chamado_similar['score_similaridade'],
                'motivos': chamado_similar['motivos'],
                'detalhes_scores': chamado_similar['detalhes_scores']
            })
        
        return {
            "id_chamado": chamado_id,
            "chamado_principal": {
                "numero_wex": chamado_principal.numero_wex,
                "cliente": chamado_principal.cliente_solicitante,
                "descricao": chamado_principal.descricao[:200] + "..." if len(chamado_principal.descricao) > 200 else chamado_principal.descricao,
                "status": chamado_principal.status.value if hasattr(chamado_principal.status, 'value') else str(chamado_principal.status),
                "criticidade": chamado_principal.criticidade.value if hasattr(chamado_principal.criticidade, 'value') else str(chamado_principal.criticidade)
            },
            "chamados_similares": chamados_similares,
            "total_encontrados": resultado_ia.total_encontrados,
            "padroes_identificados": resultado_ia.padroes_identificados,
            "parametros_busca": {
                "score_minimo": score_minimo,
                "limite": limite
            },
            "metadados_ia": {
                "modelo_usado": resultado_ia.modelo_usado,
                "tempo_processamento": resultado_ia.tempo_processamento,
                "confianca_analise": resultado_ia.confianca_analise
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na busca de chamados relacionados: {str(e)}")
        # Fallback para resposta com erro
        try:
            chamado_principal = db.query(Chamado).filter(Chamado.id == chamado_id).first()
            if not chamado_principal:
                raise HTTPException(status_code=404, detail="Chamado não encontrado")
                
            return {
                "id_chamado": chamado_id,
                "chamado_principal": {
                    "numero_wex": chamado_principal.numero_wex,
                    "cliente": chamado_principal.cliente_solicitante,
                    "descricao": chamado_principal.descricao[:200] + "..." if len(chamado_principal.descricao) > 200 else chamado_principal.descricao,
                    "status": chamado_principal.status.value if hasattr(chamado_principal.status, 'value') else str(chamado_principal.status),
                    "criticidade": chamado_principal.criticidade.value if hasattr(chamado_principal.criticidade, 'value') else str(chamado_principal.criticidade)
                },
                "chamados_similares": [],
                "total_encontrados": 0,
                "padroes_identificados": [],
                "parametros_busca": {
                    "score_minimo": score_minimo,
                    "limite": limite
                },
                "erro_ia": f"Erro na análise de IA: {str(e)}",
                "metadados_ia": {
                    "modelo_usado": "fallback",
                    "tempo_processamento": 0,
                    "confianca_analise": 0
                }
            }
        except Exception as e2:
            logger.error(f"Erro crítico no endpoint relacionados: {str(e2)}")
            raise HTTPException(status_code=500, detail=f"Erro interno: {str(e2)}")

@app.get("/api/relatorios/padroes-ia")
async def relatorio_padroes_ia(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Gera relatório de padrões identificados pela IA real"""
    
    periodo_inicio = datetime.now() - timedelta(days=dias)
    
    # Buscar chamados do período
    chamados_periodo = db.query(Chamado).filter(
        Chamado.data_criacao >= periodo_inicio
    ).all()
    
    if not chamados_periodo:
        return {
            "periodo_inicio": periodo_inicio,
            "periodo_fim": datetime.now(),
            "total_chamados": 0,
            "padroes_globais": [],
            "grupos_similares": [],
            "distribuicao_criticidade": {},
            "clientes_mais_ativos": [],
            "insights_ia": [],
            "resumo": "Nenhum chamado encontrado no período especificado",
            "metadados_ia": {
                "modelo_usado": "sem_dados",
                "tempo_processamento": 0,
                "confianca_analise": 0
            }
        }
    
    try:
        # Usar IA real para gerar relatório de padrões
        resultado_ia = wex_ai.gerar_relatorio_padroes(
            chamados=chamados_periodo,
            periodo_dias=dias
        )
        
        # Estatísticas complementares
        criticidades = [c.criticidade.value if hasattr(c.criticidade, 'value') else str(c.criticidade) for c in chamados_periodo]
        dist_criticidade = Counter(criticidades)
        
        clientes = [c.cliente_solicitante for c in chamados_periodo]
        clientes_ativos = Counter(clientes).most_common(5)
        
        return {
            "periodo_inicio": periodo_inicio,
            "periodo_fim": datetime.now(),
            "total_chamados": len(chamados_periodo),
            "total_grupos_similares": resultado_ia.total_grupos_similares,
            "padroes_globais": resultado_ia.padroes_globais,
            "grupos_similares": resultado_ia.grupos_similares,
            "distribuicao_criticidade": {crit: count for crit, count in dist_criticidade.items()},
            "clientes_mais_ativos": [{"cliente": cliente, "total_chamados": count} for cliente, count in clientes_ativos],
            "insights_ia": resultado_ia.insights_ia,
            "tendencias": resultado_ia.tendencias,
            "recomendacoes": resultado_ia.recomendacoes,
            "resumo": resultado_ia.resumo,
            "metadados_ia": {
                "modelo_usado": resultado_ia.modelo_usado,
                "tempo_processamento": resultado_ia.tempo_processamento,
                "confianca_analise": resultado_ia.confianca_analise
            }
        }
        
    except Exception as e:
        # Fallback para método tradicional em caso de erro
        criticidades = [c.criticidade.value if hasattr(c.criticidade, 'value') else str(c.criticidade) for c in chamados_periodo]
        dist_criticidade = Counter(criticidades)
        
        clientes = [c.cliente_solicitante for c in chamados_periodo]
        clientes_ativos = Counter(clientes).most_common(5)
        
        return {
            "periodo_inicio": periodo_inicio,
            "periodo_fim": datetime.now(),
            "total_chamados": len(chamados_periodo),
            "total_grupos_similares": 0,
            "padroes_globais": [],
            "grupos_similares": [],
            "distribuicao_criticidade": {crit: count for crit, count in dist_criticidade.items()},
            "clientes_mais_ativos": [{"cliente": cliente, "total_chamados": count} for cliente, count in clientes_ativos],
            "insights_ia": [],
            "tendencias": [],
            "recomendacoes": [],
            "resumo": f"Erro na análise de IA: {str(e)}. Dados básicos disponíveis para {len(chamados_periodo)} chamados.",
            "erro_ia": f"Erro na análise de IA: {str(e)}",
            "metadados_ia": {
                "modelo_usado": "fallback",
                "tempo_processamento": 0,
                "confianca_analise": 0
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)