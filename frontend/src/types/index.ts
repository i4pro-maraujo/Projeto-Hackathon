export interface Chamado {
  id: number;
  numero_wex: string;
  cliente_solicitante: string;
  descricao: string;
  status: StatusChamado;
  criticidade: CriticidadeChamado;
  data_criacao: string;
  data_atualizacao: string;
  sla_limite?: string;
  tags_automaticas: string[];
  score_qualidade: number;
  ambiente_informado: boolean;
  possui_anexos: boolean;
  total_followups: number;
}

export enum StatusChamado {
  ABERTO = "Aberto",
  EM_ANALISE = "Em análise",
  PENDENTE = "Pendente", 
  RESOLVIDO = "Resolvido",
  FECHADO = "Fechado"
}

export enum CriticidadeChamado {
  BAIXA = "Baixa",
  MEDIA = "Média",
  ALTA = "Alta",
  CRITICA = "Crítica"
}

export enum TipoFollowUp {
  PUBLICACAO = "Publicação",
  DESENVOLVIMENTO = "Desenvolvimento",
  ANALISE = "Análise",
  OUTROS = "Outros"
}

export interface FollowUp {
  id: number;
  chamado_id: number;
  tipo: TipoFollowUp;
  descricao: string;
  data_criacao: string;
  autor: string;
  anexos: string[];
}

export interface DashboardMetricas {
  total_chamados_por_status: Record<string, number>;
  chamados_criticos_abertos: number;
  tempo_medio_resolucao?: number;
  distribuicao_por_criticidade: Record<string, number>;
  chamados_novos_hoje: number;
  chamados_vencidos: number;
}

export interface ChamadoFiltros {
  status?: StatusChamado[];
  criticidade?: CriticidadeChamado[];
  cliente?: string;
  data_inicio?: string;
  data_fim?: string;
  busca_texto?: string;
  page?: number;
  size?: number;
}

export interface ChamadosResponse {
  chamados: Chamado[];
  total: number;
  page: number;
  size: number;
  pages: number;
}