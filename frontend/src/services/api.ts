import axios from 'axios';
import { Chamado, FollowUp, DashboardMetricas, ChamadosResponse, ChamadoFiltros } from '../types';

const API_BASE_URL = 'http://localhost:8000';

// Configurar instância do Axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para requisições
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para respostas
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const chamadosAPI = {
  // Listar chamados com filtros
  async listarChamados(filtros: ChamadoFiltros = {}): Promise<ChamadosResponse> {
    const params = new URLSearchParams();
    
    if (filtros.page) params.append('skip', String((filtros.page - 1) * (filtros.size || 20)));
    if (filtros.size) params.append('limit', String(filtros.size));
    if (filtros.status) filtros.status.forEach(s => params.append('status', s));
    if (filtros.criticidade) filtros.criticidade.forEach(c => params.append('criticidade', c));
    if (filtros.cliente) params.append('cliente', filtros.cliente);
    if (filtros.busca_texto) params.append('busca_texto', filtros.busca_texto);
    
    const response = await api.get(`/chamados?${params.toString()}`);
    return response.data;
  },

  // Obter chamado específico
  async obterChamado(id: number): Promise<Chamado> {
    const response = await api.get(`/chamados/${id}`);
    return response.data;
  },

  // Criar novo chamado
  async criarChamado(chamado: Partial<Chamado>): Promise<Chamado> {
    const response = await api.post('/chamados', chamado);
    return response.data;
  },

  // Listar follow-ups de um chamado
  async listarFollowUps(chamadoId: number): Promise<FollowUp[]> {
    const response = await api.get(`/chamados/${chamadoId}/followups`);
    return response.data;
  },

  // Criar follow-up
  async criarFollowUp(chamadoId: number, followUp: Partial<FollowUp>): Promise<FollowUp> {
    const response = await api.post(`/chamados/${chamadoId}/followups`, followUp);
    return response.data;
  }
};

export const dashboardAPI = {
  // Obter métricas do dashboard
  async obterMetricas(): Promise<DashboardMetricas> {
    const response = await api.get('/dashboard/metricas');
    return response.data;
  }
};

export default api;