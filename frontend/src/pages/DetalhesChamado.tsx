import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Chamado, FollowUp } from '../types';

const DetalhesChamado: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [chamado, setChamado] = useState<Chamado | null>(null);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetalhes = async () => {
      try {
        setLoading(true);
        
        // Mock do chamado
        const mockChamado: Chamado = {
          id: parseInt(id || '1'),
          numero_wex: "WEX-2025-001",
          cliente_solicitante: "Empresa ABC Ltda",
          descricao: "Sistema apresentando lentidão no módulo de relatórios. Os usuários relatam que as consultas estão demorando mais de 2 minutos para carregar, especialmente nos relatórios consolidados.",
          status: "Aberto" as any,
          criticidade: "Alta" as any,
          data_criacao: "2025-10-06T14:30:00",
          data_atualizacao: "2025-10-06T14:30:00",
          sla_limite: "2025-10-07T14:30:00",
          tags_automaticas: ["performance", "relatórios", "consultas"],
          score_qualidade: 75,
          ambiente_informado: true,
          possui_anexos: false,
          total_followups: 2
        };

        const mockFollowUps: FollowUp[] = [
          {
            id: 1,
            chamado_id: parseInt(id || '1'),
            tipo: "Análise" as any,
            descricao: "Iniciada análise dos logs do sistema para identificar gargalos de performance.",
            data_criacao: "2025-10-06T15:00:00",
            autor: "João Silva - Suporte Técnico",
            anexos: []
          },
          {
            id: 2,
            chamado_id: parseInt(id || '1'),
            tipo: "Desenvolvimento" as any,
            descricao: "Identificado problema na query de consolidação. Será necessário otimizar índices do banco.",
            data_criacao: "2025-10-06T16:30:00",
            autor: "Maria Santos - DBA",
            anexos: ["analise_performance.pdf"]
          }
        ];

        setTimeout(() => {
          setChamado(mockChamado);
          setFollowUps(mockFollowUps);
          setLoading(false);
        }, 800);
      } catch (error) {
        console.error('Erro ao carregar detalhes:', error);
        setLoading(false);
      }
    };

    if (id) {
      fetchDetalhes();
    }
  }, [id]);

  if (loading) {
    return <div className="loading">Carregando detalhes do chamado...</div>;
  }

  if (!chamado) {
    return <div className="error">Chamado não encontrado</div>;
  }

  return (
    <div className="detalhes-chamado">
      <div className="header-detalhes">
        <h1>{chamado.numero_wex}</h1>
        <div className="status-badges">
          <span className={`status-badge ${chamado.status.toLowerCase().replace(' ', '-')}`}>
            {chamado.status}
          </span>
          <span className={`criticidade-badge ${chamado.criticidade.toLowerCase()}`}>
            {chamado.criticidade}
          </span>
        </div>
      </div>

      <div className="info-grid">
        <div className="info-card">
          <h3>Informações Gerais</h3>
          <div className="info-row">
            <label>Cliente:</label>
            <span>{chamado.cliente_solicitante}</span>
          </div>
          <div className="info-row">
            <label>Data Criação:</label>
            <span>{new Date(chamado.data_criacao).toLocaleString('pt-BR')}</span>
          </div>
          <div className="info-row">
            <label>SLA Limite:</label>
            <span className="sla-limite">
              {chamado.sla_limite ? new Date(chamado.sla_limite).toLocaleString('pt-BR') : 'N/A'}
            </span>
          </div>
          <div className="info-row">
            <label>Score Qualidade:</label>
            <span className="score-qualidade">{chamado.score_qualidade}%</span>
          </div>
        </div>

        <div className="info-card">
          <h3>Características</h3>
          <div className="caracteristicas">
            <div className={`caracteristica ${chamado.ambiente_informado ? 'sim' : 'nao'}`}>
              {chamado.ambiente_informado ? '✓' : '✗'} Ambiente Informado
            </div>
            <div className={`caracteristica ${chamado.possui_anexos ? 'sim' : 'nao'}`}>
              {chamado.possui_anexos ? '✓' : '✗'} Possui Anexos
            </div>
            <div className="caracteristica">
              📎 {chamado.total_followups} Follow-ups
            </div>
          </div>
        </div>
      </div>

      <div className="descricao-card">
        <h3>Descrição do Problema</h3>
        <p>{chamado.descricao}</p>
      </div>

      {chamado.tags_automaticas.length > 0 && (
        <div className="tags-card">
          <h3>Tags Automáticas</h3>
          <div className="tags-container">
            {chamado.tags_automaticas.map((tag, index) => (
              <span key={index} className="tag">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="followups-card">
        <h3>Histórico de Follow-ups</h3>
        {followUps.length > 0 ? (
          <div className="followups-timeline">
            {followUps.map((followUp) => (
              <div key={followUp.id} className="followup-item">
                <div className="followup-header">
                  <span className={`followup-tipo ${followUp.tipo.toLowerCase()}`}>
                    {followUp.tipo}
                  </span>
                  <span className="followup-data">
                    {new Date(followUp.data_criacao).toLocaleString('pt-BR')}
                  </span>
                </div>
                <div className="followup-content">
                  <p>{followUp.descricao}</p>
                  <div className="followup-autor">
                    Por: {followUp.autor}
                  </div>
                  {followUp.anexos.length > 0 && (
                    <div className="followup-anexos">
                      <strong>Anexos:</strong>
                      {followUp.anexos.map((anexo, index) => (
                        <span key={index} className="anexo-link">
                          📎 {anexo}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-followups">Nenhum follow-up cadastrado ainda.</p>
        )}
      </div>

      <div className="acoes-container">
        <button className="btn-voltar" onClick={() => window.history.back()}>
          ← Voltar para Lista
        </button>
        <button className="btn-editar">
          ✏️ Editar Chamado
        </button>
        <button className="btn-followup">
          💬 Adicionar Follow-up
        </button>
      </div>
    </div>
  );
};

export default DetalhesChamado;