import React, { useState, useEffect } from 'react';
import { DashboardMetricas } from '../types';

const Dashboard: React.FC = () => {
  const [metricas, setMetricas] = useState<DashboardMetricas | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetricas = async () => {
      try {
        // Simular chamada da API por enquanto
        const mockMetricas: DashboardMetricas = {
          total_chamados_por_status: {
            "Aberto": 15,
            "Em análise": 8,
            "Pendente": 5,
            "Resolvido": 12,
            "Fechado": 10
          },
          chamados_criticos_abertos: 3,
          tempo_medio_resolucao: 24.5,
          distribuicao_por_criticidade: {
            "Baixa": 20,
            "Média": 18,
            "Alta": 10,
            "Crítica": 2
          },
          chamados_novos_hoje: 4,
          chamados_vencidos: 2
        };
        
        setTimeout(() => {
          setMetricas(mockMetricas);
          setLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Erro ao carregar métricas:', error);
        setLoading(false);
      }
    };

    fetchMetricas();
  }, []);

  if (loading) {
    return <div className="loading">Carregando dashboard...</div>;
  }

  if (!metricas) {
    return <div className="error">Erro ao carregar métricas</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dashboard - WEX Intelligence</h1>
      
      <div className="metrics-grid">
        <div className="metric-card critical">
          <h3>Chamados Críticos</h3>
          <div className="metric-value">{metricas.chamados_criticos_abertos}</div>
          <span>em aberto</span>
        </div>

        <div className="metric-card new">
          <h3>Novos Hoje</h3>
          <div className="metric-value">{metricas.chamados_novos_hoje}</div>
          <span>chamados</span>
        </div>

        <div className="metric-card overdue">
          <h3>Vencidos</h3>
          <div className="metric-value">{metricas.chamados_vencidos}</div>
          <span>SLA ultrapassado</span>
        </div>

        <div className="metric-card average">
          <h3>Tempo Médio</h3>
          <div className="metric-value">
            {metricas.tempo_medio_resolucao?.toFixed(1) || 'N/A'}h
          </div>
          <span>resolução</span>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-container">
          <h3>Distribuição por Status</h3>
          <div className="status-chart">
            {Object.entries(metricas.total_chamados_por_status).map(([status, count]) => (
              <div key={status} className="status-item">
                <span className="status-label">{status}:</span>
                <span className="status-count">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="chart-container">
          <h3>Distribuição por Criticidade</h3>
          <div className="criticidade-chart">
            {Object.entries(metricas.distribuicao_por_criticidade).map(([crit, count]) => (
              <div key={crit} className="criticidade-item">
                <span className="criticidade-label">{crit}:</span>
                <span className="criticidade-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;