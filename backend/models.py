from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum
import json

class StatusChamado(str, Enum):
    ABERTO = "Aberto"
    EM_ANALISE = "Em análise"
    PENDENTE = "Pendente"
    RESOLVIDO = "Resolvido"
    FECHADO = "Fechado"

class CriticidadeChamado(str, Enum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    CRITICA = "Crítica"

class TipoFollowUp(str, Enum):
    PUBLICACAO = "Publicação"
    DESENVOLVIMENTO = "Desenvolvimento"
    ANALISE = "Análise"
    OUTROS = "Outros"

class Chamado(Base):
    __tablename__ = "chamados"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    numero_wex = Column(String(50), unique=True, index=True, nullable=False)
    cliente_solicitante = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=False)
    status = Column(String(20), default=StatusChamado.ABERTO.value, nullable=False)
    criticidade = Column(String(20), default=CriticidadeChamado.MEDIA.value, nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    sla_limite = Column(DateTime, nullable=True)
    tags_automaticas = Column(Text, default="[]", nullable=True)  # JSON como string
    score_qualidade = Column(Integer, default=0, nullable=False)  # 0-100
    ambiente_informado = Column(Boolean, default=False, nullable=False)
    possui_anexos = Column(Boolean, default=False, nullable=False)
    
    # Relacionamento com follow-ups
    followups = relationship("FollowUp", back_populates="chamado", cascade="all, delete-orphan")
    
    @property
    def tags_automaticas_list(self):
        try:
            return json.loads(self.tags_automaticas) if self.tags_automaticas else []
        except:
            return []
    
    def to_dict(self):
        return {
            "id": self.id,
            "numero_wex": self.numero_wex,
            "cliente_solicitante": self.cliente_solicitante,
            "descricao": self.descricao,
            "status": self.status,
            "criticidade": self.criticidade,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "data_atualizacao": self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            "sla_limite": self.sla_limite.isoformat() if self.sla_limite else None,
            "tags_automaticas": self.tags_automaticas_list,
            "score_qualidade": self.score_qualidade,
            "ambiente_informado": self.ambiente_informado,
            "possui_anexos": self.possui_anexos,
            "total_followups": len(self.followups) if self.followups else 0
        }

class FollowUp(Base):
    __tablename__ = "followups"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chamado_id = Column(Integer, ForeignKey("chamados.id"), nullable=False)
    tipo = Column(String(20), default=TipoFollowUp.OUTROS.value, nullable=False)
    descricao = Column(Text, nullable=False)
    data_criacao = Column(DateTime, default=func.now(), nullable=False)
    autor = Column(String(100), nullable=False)
    anexos = Column(Text, default="[]", nullable=True)  # JSON como string
    
    # Relacionamento com chamado
    chamado = relationship("Chamado", back_populates="followups")
    
    @property
    def anexos_list(self):
        try:
            return json.loads(self.anexos) if self.anexos else []
        except:
            return []
    
    def to_dict(self):
        return {
            "id": self.id,
            "chamado_id": self.chamado_id,
            "tipo": self.tipo,
            "descricao": self.descricao,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "autor": self.autor,
            "anexos": self.anexos_list
        }