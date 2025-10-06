from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, create_database
from models import Chamado, FollowUp, StatusChamado, CriticidadeChamado, TipoFollowUp
from schemas import (
    ChamadoResponse, ChamadoCreate, ChamadoUpdate, ChamadoFiltros,
    FollowUpResponse, FollowUpCreate, FollowUpUpdate,
    DashboardMetricas
)
import json
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_
import os

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

# Montar arquivos estáticos
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Health check
@app.get("/")
def read_root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(index_path)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)