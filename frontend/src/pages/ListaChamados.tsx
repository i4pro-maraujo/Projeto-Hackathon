import React, { useState, useEffect } from 'react';
import { Chamado, StatusChamado, CriticidadeChamado, ChamadosResponse } from '../types';

const ListaChamados: React.FC = () => {
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtros, setFiltros] = useState({
    status: '',
    criticidade: '',
    busca_texto: ''
  });
  const [paginacao, setPaginacao] = useState({
    page: 1,
    size: 20,
    total: 0,
    pages: 0
  });

  useEffect(() => {
    const fetchChamados = async () => {
      try {
        setLoading(true);
        
        // Simular dados mockados por enquanto
        const mockChamados: Chamado[] = [
          {
            id: 1,
            numero_wex: "WEX-2025-001",
            cliente_solicitante: "Empresa ABC Ltda",
            descricao: "Sistema apresentando lentidão no módulo de relatórios",
            status: StatusChamado.ABERTO,
            criticidade: CriticidadeChamado.ALTA,
            data_criacao: "2025-10-06T14:30:00",
            data_atualizacao: "2025-10-06T14:30:00",
            sla_limite: "2025-10-07T14:30:00",
            tags_automaticas: ["performance", "relatórios"],
            score_qualidade: 75,
            ambiente_informado: true,
            possui_anexos: false,
            total_followups: 2
          },
          {
            id: 2,
            numero_wex: "WEX-2025-002",
            cliente_solicitante: "Empresa XYZ Corp",
            descricao: "Erro 500 ao tentar acessar dashboard",
            status: StatusChamado.EM_ANALISE,
            criticidade: CriticidadeChamado.CRITICA,
            data_criacao: "2025-10-06T13:15:00",
            data_atualizacao: "2025-10-06T15:45:00",
            sla_limite: "2025-10-06T17:15:00",
            tags_automaticas: ["erro", "dashboard"],
            score_qualidade: 90,
            ambiente_informado: true,
            possui_anexos: true,
            total_followups: 1
          }
        ];

        setTimeout(() => {
          setChamados(mockChamados);
          setPaginacao(prev => ({ ...prev, total: mockChamados.length, pages: 1 }));
          setLoading(false);
        }, 800);
      } catch (error) {
        console.error('Erro ao carregar chamados:', error);
        setLoading(false);
      }
    };

    fetchChamados();
  }, [filtros, paginacao.page]);

  const handleFiltroChange = (field: string, value: string) => {
    setFiltros(prev => ({ ...prev, [field]: value }));
    setPaginacao(prev => ({ ...prev, page: 1 }));
  };

  const getStatusColor = (status: StatusChamado) => {
    const colors = {
      [StatusChamado.ABERTO]: '#e74c3c',
      [StatusChamado.EM_ANALISE]: '#f39c12',
      [StatusChamado.PENDENTE]: '#f1c40f',
      [StatusChamado.RESOLVIDO]: '#27ae60',
      [StatusChamado.FECHADO]: '#95a5a6'
    };
    return colors[status] || '#95a5a6';
  };

  const getCriticidadeColor = (criticidade: CriticidadeChamado) => {
    const colors = {
      [CriticidadeChamado.BAIXA]: '#27ae60',
      [CriticidadeChamado.MEDIA]: '#f39c12',
      [CriticidadeChamado.ALTA]: '#e67e22',
      [CriticidadeChamado.CRITICA]: '#e74c3c'
    };
    return colors[criticidade] || '#95a5a6';
  };

  if (loading) {
    return <div className="loading">Carregando chamados...</div>;
  }

  return (
    <div className="lista-chamados">
      <h1>Lista de Chamados</h1>

      <div className="filtros-container">
        <div className="filtro-grupo">
          <label>Status:</label>
          <select 
            value={filtros.status} 
            onChange={(e) => handleFiltroChange('status', e.target.value)}
          >
            <option value="">Todos</option>
            {Object.values(StatusChamado).map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>
        </div>

        <div className="filtro-grupo">
          <label>Criticidade:</label>
          <select 
            value={filtros.criticidade} 
            onChange={(e) => handleFiltroChange('criticidade', e.target.value)}
          >
            <option value="">Todas</option>
            {Object.values(CriticidadeChamado).map(crit => (
              <option key={crit} value={crit}>{crit}</option>
            ))}
          </select>
        </div>

        <div className="filtro-grupo">
          <label>Buscar:</label>
          <input 
            type="text"
            placeholder="Número WEX, cliente ou descrição..."
            value={filtros.busca_texto}
            onChange={(e) => handleFiltroChange('busca_texto', e.target.value)}
          />
        </div>

        <button className="btn-limpar" onClick={() => setFiltros({ status: '', criticidade: '', busca_texto: '' })}>
          Limpar Filtros
        </button>
      </div>

      <div className="chamados-table">
        <div className="table-header">
          <div className="col-numero">Número WEX</div>
          <div className="col-cliente">Cliente</div>
          <div className="col-status">Status</div>
          <div className="col-criticidade">Criticidade</div>
          <div className="col-score">Score</div>
          <div className="col-data">Data Criação</div>
          <div className="col-acoes">Ações</div>
        </div>

        {chamados.map(chamado => (
          <div key={chamado.id} className="table-row">
            <div className="col-numero">
              <strong>{chamado.numero_wex}</strong>
            </div>
            <div className="col-cliente">
              {chamado.cliente_solicitante}
            </div>
            <div className="col-status">
              <span 
                className="status-badge" 
                style={{ backgroundColor: getStatusColor(chamado.status) }}
              >
                {chamado.status}
              </span>
            </div>
            <div className="col-criticidade">
              <span 
                className="criticidade-badge"
                style={{ color: getCriticidadeColor(chamado.criticidade) }}
              >
                {chamado.criticidade}
              </span>
            </div>
            <div className="col-score">
              <div className="score-bar">
                <div 
                  className="score-fill" 
                  style={{ width: `${chamado.score_qualidade}%` }}
                ></div>
                <span className="score-text">{chamado.score_qualidade}%</span>
              </div>
            </div>
            <div className="col-data">
              {new Date(chamado.data_criacao).toLocaleDateString('pt-BR')}
            </div>
            <div className="col-acoes">
              <a href={`/chamados/${chamado.id}`} className="btn-visualizar">
                Ver Detalhes
              </a>
            </div>
          </div>
        ))}
      </div>

      {chamados.length === 0 && (
        <div className="empty-state">
          <p>Nenhum chamado encontrado com os filtros aplicados.</p>
        </div>
      )}

      <div className="paginacao">
        <span>
          Mostrando {chamados.length} de {paginacao.total} chamados
        </span>
      </div>
    </div>
  );
};

export default ListaChamados;