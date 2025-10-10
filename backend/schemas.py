from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from models import StatusChamado, CriticidadeChamado, TipoFollowUp

# Schemas para Chamados
class ChamadoBase(BaseModel):
    numero_wex: str
    cliente_solicitante: str
    descricao: str
    status: StatusChamado = StatusChamado.ABERTO
    criticidade: CriticidadeChamado = CriticidadeChamado.MEDIA
    sla_limite: Optional[datetime] = None
    tags_automaticas: List[str] = Field(default_factory=list)
    score_qualidade: int = Field(default=0, ge=0, le=100)
    ambiente_informado: bool = False
    possui_anexos: bool = False

class ChamadoCreate(ChamadoBase):
    pass

class ChamadoUpdate(BaseModel):
    numero_wex: Optional[str] = None
    cliente_solicitante: Optional[str] = None
    descricao: Optional[str] = None
    status: Optional[StatusChamado] = None
    criticidade: Optional[CriticidadeChamado] = None
    sla_limite: Optional[datetime] = None
    tags_automaticas: Optional[List[str]] = None
    score_qualidade: Optional[int] = Field(None, ge=0, le=100)
    ambiente_informado: Optional[bool] = None
    possui_anexos: Optional[bool] = None

class ChamadoResponse(ChamadoBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime
    total_followups: int = 0

    class Config:
        from_attributes = True

# Schemas para Follow-ups
class FollowUpBase(BaseModel):
    tipo: TipoFollowUp = TipoFollowUp.OUTROS
    descricao: str
    autor: str
    anexos: List[str] = Field(default_factory=list)

class FollowUpCreate(FollowUpBase):
    pass

class FollowUpUpdate(BaseModel):
    tipo: Optional[TipoFollowUp] = None
    descricao: Optional[str] = None
    autor: Optional[str] = None
    anexos: Optional[List[str]] = None

class FollowUpResponse(FollowUpBase):
    id: int
    chamado_id: int
    data_criacao: datetime

    class Config:
        from_attributes = True

# Schema para métricas do dashboard
class DashboardMetricas(BaseModel):
    total_chamados_por_status: dict
    chamados_criticos_abertos: int
    tempo_medio_resolucao: Optional[float] = None  # em horas
    distribuicao_por_criticidade: dict
    chamados_novos_hoje: int
    chamados_vencidos: int

# Schema para filtros de busca
class ChamadoFiltros(BaseModel):
    status: Optional[List[StatusChamado]] = None
    criticidade: Optional[List[CriticidadeChamado]] = None
    cliente: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    busca_texto: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

# Schemas para Sistema de IA
class TriagemAutomaticaResponse(BaseModel):
    id_chamado: int
    criticidade_sugerida: CriticidadeChamado
    confianca: float = Field(ge=0.0, le=1.0)
    fatores_identificados: List[str]
    sugestoes_adicao: List[str]
    score_qualidade: int = Field(ge=0, le=100)

class SugestaoFollowUpResponse(BaseModel):
    id_chamado: int
    sugestoes: List[str]
    proximo_tipo_sugerido: TipoFollowUp
    prioridade: str  # "alta", "media", "baixa"
    
class ChamadosRelacionadosResponse(BaseModel):
    id_chamado: int
    chamados_similares: List[dict]  # [{"id": int, "score": float, "motivo": str}]
    padroes_identificados: List[str]

class RelatorioIA(BaseModel):
    periodo_inicio: datetime
    periodo_fim: datetime
    total_triagens: int
    assertividade_triagem: float  # percentual de acerto
    economia_tempo: float  # horas economizadas
    padroes_identificados: List[str]