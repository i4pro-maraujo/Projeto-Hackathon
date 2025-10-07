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
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_
import os
from collections import Counter
import math

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

@app.post("/api/chamados/{chamado_id}/triagem", response_model=dict)
async def triagem_automatica(chamado_id: int, db: Session = Depends(get_db)):
    """Executa triagem automática de um chamado específico"""
    
    # Buscar o chamado
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Realizar análise de triagem
    resultado_triagem = extrair_indicadores_criticidade(
        chamado.descricao, 
        chamado.numero_wex, 
        chamado.cliente_solicitante
    )
    
    # Calcular score de qualidade
    score_qualidade = calcular_score_qualidade(
        chamado.descricao,
        chamado.numero_wex,
        chamado.cliente_solicitante
    )
    
    # Sugerir tags automáticas
    tags_sugeridas = sugerir_tags_automaticas(
        chamado.descricao,
        chamado.numero_wex,
        chamado.cliente_solicitante
    )
    
    # Gerar sugestões de melhoria
    sugestoes = []
    if score_qualidade < 70:
        if len(chamado.descricao) < 50:
            sugestoes.append("Adicionar mais detalhes na descrição do problema")
        if not re.search(r'erro|error', chamado.descricao.lower()):
            sugestoes.append("Incluir mensagens de erro específicas, se houver")
        if not re.search(r'ambiente|versão', chamado.descricao.lower()):
            sugestoes.append("Informar ambiente e versão do sistema")
        if not re.search(r'passos|procedimento', chamado.descricao.lower()):
            sugestoes.append("Detalhar passos para reproduzir o problema")
    
    # Atualizar chamado com dados da triagem (opcional - manter original para comparação)
    # chamado.criticidade = resultado_triagem['criticidade']
    # chamado.score_qualidade = score_qualidade
    # chamado.tags_automaticas = tags_sugeridas
    # db.commit()
    
    return {
        "id_chamado": chamado_id,
        "criticidade_atual": chamado.criticidade.value,
        "criticidade_sugerida": resultado_triagem['criticidade'].value,
        "confianca": resultado_triagem['confianca'],
        "fatores_identificados": resultado_triagem['fatores'],
        "sugestoes_adicao": sugestoes,
        "score_qualidade_atual": chamado.score_qualidade,
        "score_qualidade_sugerido": score_qualidade,
        "tags_atuais": chamado.tags_automaticas,
        "tags_sugeridas": tags_sugeridas,
        "detalhes_scores": resultado_triagem['scores']
    }

@app.post("/api/triagem/aplicar/{chamado_id}")
async def aplicar_triagem(chamado_id: int, db: Session = Depends(get_db)):
    """Aplica as sugestões da triagem automática ao chamado"""
    
    # Buscar o chamado
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Executar triagem
    resultado_triagem = extrair_indicadores_criticidade(
        chamado.descricao, 
        chamado.numero_wex, 
        chamado.cliente_solicitante
    )
    
    score_qualidade = calcular_score_qualidade(
        chamado.descricao,
        chamado.numero_wex,
        chamado.cliente_solicitante
    )
    
    tags_sugeridas = sugerir_tags_automaticas(
        chamado.descricao,
        chamado.numero_wex,
        chamado.cliente_solicitante
    )
    
    # Aplicar mudanças
    criticidade_anterior = chamado.criticidade
    chamado.criticidade = resultado_triagem['criticidade']
    chamado.score_qualidade = score_qualidade
    chamado.tags_automaticas = tags_sugeridas
    
    db.commit()
    db.refresh(chamado)
    
    return {
        "success": True,
        "chamado_id": chamado_id,
        "mudancas": {
            "criticidade": {
                "anterior": criticidade_anterior.value,
                "nova": chamado.criticidade.value
            },
            "score_qualidade": score_qualidade,
            "tags_adicionadas": tags_sugeridas
        }
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
    """Gera sugestões inteligentes para próximos follow-ups"""
    
    # Buscar o chamado
    chamado = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Analisar contexto
    contexto = analisar_contexto_chamado(chamado, db)
    
    # Gerar sugestões
    sugestoes_result = gerar_sugestoes_followup(chamado, contexto)
    
    # Buscar exemplos de chamados similares
    exemplos_historico = buscar_followups_similares(chamado, db)
    
    return {
        "id_chamado": chamado_id,
        "sugestoes_principais": sugestoes_result['sugestoes'],
        "proximo_tipo_sugerido": sugestoes_result['proximo_tipo'].value,
        "prioridade": sugestoes_result['prioridade'],
        "contexto": {
            "status_atual": chamado.status.value,
            "criticidade": chamado.criticidade.value,
            "tempo_desde_criacao_horas": contexto['tempo_desde_criacao'],
            "tempo_desde_ultimo_followup_horas": contexto['tempo_desde_ultimo'],
            "total_followups_existentes": contexto['total_followups']
        },
        "exemplos_historico": exemplos_historico,
        "tipos_followup_existentes": [tipo.value for tipo in contexto['tipos_existentes']]
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
    """Busca chamados relacionados/similares ao chamado especificado"""
    
    # Buscar o chamado principal
    chamado_principal = db.query(Chamado).filter(Chamado.id == chamado_id).first()
    if not chamado_principal:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Buscar todos os outros chamados (exceto o atual)
    outros_chamados = db.query(Chamado).filter(
        Chamado.id != chamado_id
    ).all()
    
    # Calcular similaridade com cada chamado
    similaridades = []
    for chamado in outros_chamados:
        scores = calcular_similaridade_chamados(chamado_principal, chamado)
        
        if scores['score_final'] >= score_minimo:
            # Identificar motivo principal da similaridade
            motivo_principal = max(
                {k: v for k, v in scores.items() if k != 'score_final'}.items(),
                key=lambda x: x[1]
            )
            
            motivos = []
            if scores['palavras'] > 0.3:
                motivos.append("Termos similares na descrição")
            if scores['termos_tecnicos'] > 0.5:
                motivos.append("Termos técnicos em comum")
            if scores['codigos_erro'] > 0:
                motivos.append("Mesmo código de erro")
            if scores['mensagens_erro'] > 0:
                motivos.append("Mensagens de erro idênticas")
            if scores['cliente'] > 0:
                motivos.append("Mesmo cliente")
            if scores['criticidade'] > 0:
                motivos.append("Mesma criticidade")
            
            similaridades.append({
                'id': chamado.id,
                'numero_wex': chamado.numero_wex,
                'cliente': chamado.cliente_solicitante,
                'descricao': chamado.descricao[:200] + "..." if len(chamado.descricao) > 200 else chamado.descricao,
                'status': chamado.status.value,
                'criticidade': chamado.criticidade.value,
                'data_criacao': chamado.data_criacao,
                'score_similaridade': round(scores['score_final'], 3),
                'motivos': motivos,
                'detalhes_scores': {k: round(v, 3) for k, v in scores.items()}
            })
    
    # Ordenar por score de similaridade
    similaridades.sort(key=lambda x: x['score_similaridade'], reverse=True)
    
    # Limitar resultados
    resultados_limitados = similaridades[:limite]
    
    # Identificar padrões nos chamados similares
    chamados_para_analise = [chamado_principal] + [
        db.query(Chamado).filter(Chamado.id == sim['id']).first()
        for sim in resultados_limitados[:5]  # Analisar apenas os 5 mais similares
    ]
    padroes = identificar_padroes_chamados(chamados_para_analise)
    
    return {
        "id_chamado": chamado_id,
        "chamado_principal": {
            "numero_wex": chamado_principal.numero_wex,
            "cliente": chamado_principal.cliente_solicitante,
            "descricao": chamado_principal.descricao[:200] + "..." if len(chamado_principal.descricao) > 200 else chamado_principal.descricao,
            "status": chamado_principal.status.value,
            "criticidade": chamado_principal.criticidade.value
        },
        "chamados_similares": resultados_limitados,
        "total_encontrados": len(similaridades),
        "padroes_identificados": padroes,
        "parametros_busca": {
            "score_minimo": score_minimo,
            "limite": limite
        }
    }

@app.get("/api/relatorios/padroes-ia")
async def relatorio_padroes_ia(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Gera relatório de padrões identificados pela IA"""
    
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
            "resumo": "Nenhum chamado encontrado no período especificado"
        }
    
    # Agrupar chamados por similaridade (clustering simples)
    grupos_similares = []
    chamados_processados = set()
    
    for i, chamado_base in enumerate(chamados_periodo):
        if chamado_base.id in chamados_processados:
            continue
            
        grupo_atual = [chamado_base]
        chamados_processados.add(chamado_base.id)
        
        for j, chamado_comp in enumerate(chamados_periodo):
            if i != j and chamado_comp.id not in chamados_processados:
                scores = calcular_similaridade_chamados(chamado_base, chamado_comp)
                if scores['score_final'] > 0.4:  # Threshold para agrupamento
                    grupo_atual.append(chamado_comp)
                    chamados_processados.add(chamado_comp.id)
        
        if len(grupo_atual) > 1:  # Apenas grupos com múltiplos chamados
            grupos_similares.append(grupo_atual)
    
    # Identificar padrões globais
    padroes_globais = []
    
    for grupo in grupos_similares:
        padroes_grupo = identificar_padroes_chamados(grupo)
        padroes_globais.extend([
            f"Grupo de {len(grupo)} chamados: {padrao}" 
            for padrao in padroes_grupo
        ])
    
    # Estatísticas de criticidade
    criticidades = [c.criticidade for c in chamados_periodo]
    dist_criticidade = Counter(criticidades)
    
    # Clientes mais ativos
    clientes = [c.cliente_solicitante for c in chamados_periodo]
    clientes_ativos = Counter(clientes).most_common(5)
    
    return {
        "periodo_inicio": periodo_inicio,
        "periodo_fim": datetime.now(),
        "total_chamados": len(chamados_periodo),
        "total_grupos_similares": len(grupos_similares),
        "padroes_globais": padroes_globais,
        "distribuicao_criticidade": {crit.value: count for crit, count in dist_criticidade.items()},
        "clientes_mais_ativos": [{"cliente": cliente, "total_chamados": count} for cliente, count in clientes_ativos],
        "resumo": f"Analisados {len(chamados_periodo)} chamados, identificados {len(grupos_similares)} grupos de chamados similares"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)