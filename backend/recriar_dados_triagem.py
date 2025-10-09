"""
Script para limpar e repovoar o banco de dados com dados coerentes 
aos parâmetros de triagem configurados no triagem_config.json

Criará cenários variados com scores de 0 a 100 baseados nos critérios:
- Anexos (30%): presença, formato, tamanho, nomes descritivos
- Descrição (25%): clareza, palavras-chave técnicas, estrutura, erros
- Info Técnicas (25%): cliente, criticidade, título, datas, número WEX
- Contexto (20%): problema definido, impacto, urgência, tentativas

Scores:
- 0-49: Recusa automática
- 50-69: Revisão humana  
- 70-100: Aprovação automática
"""

import json
import random
from datetime import datetime, timedelta
from database import SessionLocal
from models import Chamado, FollowUp, StatusChamado, CriticidadeChamado, TipoFollowUp

def load_triagem_config():
    """Carrega configurações de triagem"""
    with open('triagem_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def limpar_banco():
    """Remove todos os dados existentes"""
    db = SessionLocal()
    try:
        print("🧹 Limpando dados existentes...")
        db.query(FollowUp).delete()
        db.query(Chamado).delete()
        db.commit()
        print("✅ Banco limpo com sucesso!")
        return db
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao limpar banco: {e}")
        raise

def criar_chamados_score_baixo(db, config):
    """
    Cria chamados com score 0-49 (RECUSA AUTOMÁTICA)
    Problemas: descrições curtas, sem anexos, informações incompletas
    """
    print("\n📉 Criando chamados com SCORE BAIXO (0-49 pontos)...")
    
    chamados_ruins = [
        {
            "numero_wex": "WEX-2025-001",
            "cliente_solicitante": "Cliente A",  # Nome muito genérico
            "descricao": "Sistema não funciona",  # Muito curta (<50 chars)
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.CRITICA.value,  # Criticidade inadequada para problema vago
            "score_qualidade": 15,  # Score muito baixo
            "ambiente_informado": False,
            "possui_anexos": False,
            "tags_automaticas": "[]"
        },
        {
            "numero_wex": "WEX-2025-002", 
            "cliente_solicitante": "Empresa XYZ",
            "descricao": "erro",  # Extremamente curta
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.ALTA.value,
            "score_qualidade": 5,  # Score quase zero
            "ambiente_informado": False,
            "possui_anexos": False,
            "tags_automaticas": "[]"
        },
        {
            "numero_wex": "WEX-INVALID",  # Formato incorreto do número WEX
            "cliente_solicitante": "",  # Cliente não identificado
            "descricao": "problema no sistema ontem a noite nao sei o que aconteceu",  # Sem pontuação, sem estrutura
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.BAIXA.value,
            "score_qualidade": 25,
            "ambiente_informado": False,
            "possui_anexos": False,
            "tags_automaticas": "[]"
        },
        {
            "numero_wex": "WEX-2025-004",
            "cliente_solicitante": "Cliente Teste",
            "descricao": "Preciso de ajuda urgente mas não sei explicar direito o problema",  # Vaga, sem detalhes técnicos
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.CRITICA.value,  # Criticidade não justificada
            "score_qualidade": 35,
            "ambiente_informado": False,
            "possui_anexos": False,
            "tags_automaticas": "[]"
        },
        {
            "numero_wex": "WEX-2025-005",
            "cliente_solicitante": "ABC Corp",
            "descricao": "site fora do ar site fora do ar site fora do ar",  # Repetitiva, sem informações úteis
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.MEDIA.value,
            "score_qualidade": 20,
            "ambiente_informado": False,
            "possui_anexos": False,
            "tags_automaticas": "[]"
        }
    ]
    
    for dados in chamados_ruins:
        chamado = Chamado(**dados)
        db.add(chamado)
    
    print(f"✅ Criados {len(chamados_ruins)} chamados com score baixo")

def criar_chamados_score_medio(db, config):
    """
    Cria chamados com score 50-69 (REVISÃO HUMANA)
    Características: parcialmente completos, algumas informações faltando
    """
    print("\n📊 Criando chamados com SCORE MÉDIO (50-69 pontos)...")
    
    chamados_medios = [
        {
            "numero_wex": "WEX-2025-006",
            "cliente_solicitante": "TechSolutions Consulting Ltda",
            "descricao": "Sistema de vendas apresentando lentidão significativa desde ontem. Usuários relatam timeout nas consultas de relatórios. Problema afeta aproximadamente 30 usuários do setor comercial.",  # Descrição razoável mas sem detalhes técnicos
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.ALTA.value,
            "score_qualidade": 55,
            "ambiente_informado": True,
            "possui_anexos": False,  # Faltam anexos
            "tags_automaticas": '["lentidao", "timeout", "sistema-vendas"]'
        },
        {
            "numero_wex": "WEX-2025-007",
            "cliente_solicitante": "DataFlow Systems S.A.",
            "descricao": "Erro 500 ocorrendo na funcionalidade de cadastro de clientes. O problema acontece de forma intermitente, principalmente no período da manhã. Já tentamos limpar cache do navegador mas o erro persiste. Impacto: novos clientes não conseguem ser cadastrados.",
            "status": StatusChamado.EM_ANALISE.value,
            "criticidade": CriticidadeChamado.MEDIA.value,
            "score_qualidade": 62,
            "ambiente_informado": True,
            "possui_anexos": True,  # Tem anexos mas pode não ser suficiente
            "tags_automaticas": '["erro-500", "cadastro", "intermitente"]'
        },
        {
            "numero_wex": "WEX-2025-008",
            "cliente_solicitante": "InnovaCorp Tecnologia",
            "descricao": "Dashboard financeiro não está carregando os dados de vendas do mês atual. O problema começou após a última atualização do sistema. Usuários conseguem acessar dados históricos normalmente. Testamos em diferentes navegadores com o mesmo resultado.",
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.ALTA.value,
            "score_qualidade": 58,
            "ambiente_informado": True,
            "possui_anexos": False,
            "tags_automaticas": '["dashboard", "dados-vendas", "atualizacao"]'
        },
        {
            "numero_wex": "WEX-2025-009",
            "cliente_solicitante": "CloudFirst Technologies",
            "descricao": "API de integração retornando status 504 (Gateway Timeout) em algumas requisições. O problema afeta principalmente as consultas de estoque em tempo real. Já verificamos nossa infraestrutura e ela está normal. Solicitamos análise urgente pois impacta nossos clientes.",
            "status": StatusChamado.PENDENTE.value,
            "criticidade": CriticidadeChamado.ALTA.value,
            "score_qualidade": 65,
            "ambiente_informado": True,
            "possui_anexos": True,
            "tags_automaticas": '["api", "timeout", "estoque", "504"]'
        },
        {
            "numero_wex": "WEX-2025-010",
            "cliente_solicitante": "NextGen Software Ltda",
            "descricao": "Módulo de relatórios apresenta performance muito baixa. Relatórios que antes eram gerados em 30 segundos agora levam mais de 5 minutos. Problema identificado há 2 dias. Afeta todos os usuários do módulo financeiro (cerca de 15 pessoas).",
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.MEDIA.value,
            "score_qualidade": 60,
            "ambiente_informado": False,  # Ambiente não informado
            "possui_anexos": False,
            "tags_automaticas": '["performance", "relatorios", "lentidao"]'
        }
    ]
    
    for dados in chamados_medios:
        chamado = Chamado(**dados)
        db.add(chamado)
    
    print(f"✅ Criados {len(chamados_medios)} chamados com score médio")

def criar_chamados_score_alto(db, config):
    """
    Cria chamados com score 70-100 (APROVAÇÃO AUTOMÁTICA)
    Características: completos, bem estruturados, com todas as informações necessárias
    """
    print("\n📈 Criando chamados com SCORE ALTO (70-100 pontos)...")
    
    chamados_excelentes = [
        {
            "numero_wex": "WEX-2025-011",
            "cliente_solicitante": "DigitalBridge Corporation Brasil Ltda",
            "descricao": """DESCRIÇÃO DO PROBLEMA:
Sistema de autenticação apresentando falha crítica desde 09/10/2025 às 14:30h.

SINTOMAS IDENTIFICADOS:
- Erro 500 Internal Server Error na tela de login
- Mensagem específica: "Database connection timeout"
- Logs do servidor mostram falha na conexão com banco de dados principal
- Timeout configurado: 30 segundos (atingido consistentemente)

IMPACTO:
- 100% dos usuários impossibilitados de acessar o sistema
- Aproximadamente 200 usuários ativos afetados
- Produção completamente parada
- Perda estimada: R$ 50.000/hora

AMBIENTE:
- Produção - Servidor Principal (srv-prod-01)
- Banco de dados: PostgreSQL 13.4
- Aplicação: Java Spring Boot 2.7.0

TENTATIVAS DE SOLUÇÃO REALIZADAS:
1. Restart do serviço de aplicação - SEM SUCESSO
2. Verificação de conectividade de rede - OK
3. Análise de logs do banco - Identificado alto número de conexões ativas
4. Tentativa de restart do banco - EM ANDAMENTO

ANEXOS INCLUSOS:
- error.log (últimas 2 horas)
- screenshot_erro_login.png
- relatorio_conexoes_bd.pdf
- arquitetura_sistema.docx

CONTATO URGENTE:
João Silva - Coordenador TI - (11) 99999-0001
""",
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.CRITICA.value,
            "score_qualidade": 95,
            "ambiente_informado": True,
            "possui_anexos": True,
            "tags_automaticas": '["falha-critica", "autenticacao", "erro-500", "banco-dados", "producao-parada", "timeout"]'
        },
        {
            "numero_wex": "WEX-2025-012",
            "cliente_solicitante": "SmartSystems Brasil Soluções Digitais S.A.",
            "descricao": """SOLICITAÇÃO: Análise de performance do módulo de vendas

CONTEXTO:
Identificamos degradação na performance do sistema de vendas durante horários de pico (9h-12h e 14h-17h).

DETALHAMENTO TÉCNICO:
- Consultas SQL específicas apresentando tempo médio de 15 segundos
- Query principal: SELECT vendas com JOIN em 4 tabelas
- Índices verificados e estão ativos
- Plano de execução mostra table scan desnecessário

MÉTRICAS OBSERVADAS:
- Tempo médio de resposta: era 2s, agora 15s
- Usuários simultâneos no pico: 45-50
- CPU do servidor BD: 85% durante picos
- Memória: 78% de utilização

IMPACTO ATUAL:
- Vendedores reportam lentidão significativa
- Tempo de cadastro de vendas aumentou 700%
- Ainda não houve perda de vendas, mas há reclamações

ANÁLISES REALIZADAS:
1. Verificação de índices - OK
2. Análise do plano de execução - Identificado problema
3. Monitoramento de recursos - CPU e memória altos
4. Teste em ambiente de homologação - Problema reproduzido

PROPOSTA DE SOLUÇÃO:
Solicitamos otimização das queries principais e revisão dos índices da tabela vendas_detalhes.

DISPONIBILIDADE PARA TESTES:
Ambiente de homologação disponível 24/7
Janela de manutenção em produção: Sábados 22h-06h""",
            "status": StatusChamado.EM_ANALISE.value,
            "criticidade": CriticidadeChamado.ALTA.value,
            "score_qualidade": 88,
            "ambiente_informado": True,
            "possui_anexos": True,
            "tags_automaticas": '["performance", "vendas", "sql", "otimizacao", "analise", "indices"]'
        },
        {
            "numero_wex": "WEX-2025-013",
            "cliente_solicitante": "Enterprise Solutions Global Ltda",
            "descricao": """TÍTULO: Implementação de nova funcionalidade - Relatório de Vendas por Região

TIPO: Solicitação de desenvolvimento

ESPECIFICAÇÃO DETALHADA:
Necessitamos implementar um novo relatório que apresente as vendas consolidadas por região geográfica, com filtros avançados e exportação em múltiplos formatos.

REQUISITOS FUNCIONAIS:
1. Filtros disponíveis:
   - Período (data início/fim)
   - Região (Norte, Sul, Nordeste, Centro-Oeste, Sudeste)
   - Tipo de produto
   - Vendedor responsável

2. Dados a serem exibidos:
   - Total de vendas por região
   - Comparativo com período anterior
   - Top 10 produtos por região
   - Performance de vendedores por região

3. Formatos de exportação:
   - PDF com gráficos
   - Excel com planilhas separadas por região
   - CSV para integração com BI

REQUISITOS TÉCNICOS:
- Integração com base de dados atual (vendas)
- Performance: máximo 30 segundos para gerar relatório
- Responsivo para acesso mobile
- Logs de auditoria (quem gerou, quando)

PRAZO DESEJADO:
30 dias úteis a partir da aprovação

IMPACTO NO NEGÓCIO:
Esta funcionalidade permitirá análises estratégicas mais eficientes e tomada de decisão baseada em dados regionais, impactando diretamente no planejamento comercial.

APROVAÇÃO ORÇAMENTÁRIA:
Aprovado pela diretoria - Orçamento: R$ 50.000

CONTATOS:
- Maria Santos (Gerente Comercial): maria.santos@enterprise.com
- Carlos Lima (Analista de BI): carlos.lima@enterprise.com""",
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.MEDIA.value,
            "score_qualidade": 92,
            "ambiente_informado": True,
            "possui_anexos": True,
            "tags_automaticas": '["desenvolvimento", "relatorio", "vendas", "regiao", "bi", "especificacao"]'
        },
        {
            "numero_wex": "WEX-2025-014", 
            "cliente_solicitante": "TechAdvanced Innovation Corporation",
            "descricao": """ALERTA CRÍTICO: Sistema de pagamentos indisponível

HORÁRIO DO INCIDENTE: 09/10/2025 às 16:45h (horário de Brasília)

DESCRIÇÃO DETALHADA:
O gateway de pagamentos principal (PaymentGateway_v2.3) apresentou falha total, impossibilitando o processamento de transações financeiras.

EVIDÊNCIAS DO PROBLEMA:
- Status Code: 503 Service Unavailable
- Logs de erro: "Circuit breaker OPEN - too many failures"
- Último pagamento processado com sucesso: 16:44:23h
- Tentativas de retry: 50 (todas falharam)

IMPACTO CRÍTICO:
- 100% das transações de pagamento bloqueadas
- E-commerce fora do ar para finalização de compras
- Estimativa: 500 clientes tentando pagar neste momento
- Perda potencial: R$ 200.000/hora
- SLA comprometido (99.9% disponibilidade)

ARQUITETURA AFETADA:
- Gateway Principal: gateway-prod-01.payments.com
- Gateway Backup: gateway-prod-02.payments.com (também indisponível)
- Load Balancer: reportando ambos os gateways como "unhealthy"
- Banco de dados de transações: OK (conexões ativas)

DIAGNÓSTICO INICIAL:
1. Health check dos serviços: FAILED
2. Verificação de certificados SSL: OK (válidos até 2026)
3. Análise de conectividade: OK  
4. Monitoramento de recursos: CPU 98% nos gateways
5. Análise de logs: Alto volume de requisições suspeitas (possível DDoS)

AÇÕES IMEDIATAS EM ANDAMENTO:
- Ativação do gateway de contingência (AWS)
- Implementação de rate limiting  
- Análise de logs de segurança
- Comunicação com provedores de pagamento (Visa/MasterCard)

COMUNICAÇÃO:
- Equipe de TI: 100% mobilizada
- Diretoria: notificada
- Clientes: comunicado em andamento
- Imprensa: preparando nota oficial

CONTATO DE EMERGÊNCIA:
Pedro Oliveira (CTO) - (11) 99999-9999 (disponível 24h)""",
            "status": StatusChamado.ABERTO.value,
            "criticidade": CriticidadeChamado.CRITICA.value,
            "score_qualidade": 98,
            "ambiente_informado": True,
            "possui_anexos": True,
            "tags_automaticas": '["critico", "pagamentos", "gateway", "503", "circuit-breaker", "indisponivel", "ddos", "emergencia"]'
        },
        {
            "numero_wex": "WEX-2025-015",
            "cliente_solicitante": "Global Financial Services International Ltd",
            "descricao": """MANUTENÇÃO PROGRAMADA: Atualização do sistema de backup

TIPO: Manutenção preventiva agendada

OBJETIVO:
Atualizar o sistema de backup corporativo da versão 3.2 para 4.1, incluindo novos recursos de compressão e criptografia avançada.

JUSTIFICATIVA TÉCNICA:
A versão atual (3.2) apresenta limitações de performance e compatibilidade com novos sistemas operacionais. A versão 4.1 oferece:
- Compressão 40% mais eficiente
- Criptografia AES-256 nativa
- Suporte a backup incremental otimizado
- Interface web moderna
- API REST para integração

ESCOPO DA MANUTENÇÃO:
1. Backup completo do sistema atual
2. Instalação da nova versão em ambiente paralelo
3. Migração dos dados de configuração
4. Testes de integridade dos backups existentes
5. Validação da nova interface
6. Treinamento da equipe técnica

CRONOGRAMA DETALHADO:
- Sábado 12/10/2025:
  - 22:00h - Início dos trabalhos
  - 22:30h - Backup de segurança completo
  - 23:00h - Instalação da nova versão
  - 01:00h - Migração de configurações
  - 03:00h - Testes de funcionalidade
  - 05:00h - Rollback de contingência (se necessário)
  - 06:00h - Finalização e documentação

IMPACTO ESPERADO:
- Serviços de backup indisponíveis por 8 horas
- Sistemas principais não afetados
- Backups automáticos suspensos durante janela
- Equipe de plantão para monitoramento

PLANO DE CONTINGÊNCIA:
- Sistema atual mantido em standby por 72h
- Rollback automático em caso de falha crítica
- Backup manual disponível via scripts
- Equipe técnica em standby 24h pós-manutenção

COMUNICAÇÃO:
- Usuários notificados com 7 dias de antecedência
- Memo enviado para toda a diretoria
- Plantão técnico confirmado
- Procedimentos de emergência revisados

APROVAÇÕES OBTIDAS:
- Diretoria de TI: APROVADO
- Comitê de Mudanças: APROVADO  
- Compliance: APROVADO
- Auditoria Interna: APROVADO

RESPONSÁVEIS:
- Coordenador: Ana Costa (ana.costa@gfs.com)
- Técnico Sênior: Roberto Silva
- Backup Coordinator: Fernanda Lima""",
            "status": StatusChamado.PENDENTE.value,
            "criticidade": CriticidadeChamado.BAIXA.value,
            "score_qualidade": 85,
            "ambiente_informado": True,
            "possui_anexos": True,
            "tags_automaticas": '["manutencao", "backup", "atualizacao", "programada", "preventiva", "agendada"]'
        }
    ]
    
    for dados in chamados_excelentes:
        chamado = Chamado(**dados)
        db.add(chamado)
    
    print(f"✅ Criados {len(chamados_excelentes)} chamados com score alto")

def criar_followups_representativos(db):
    """Cria follow-ups que demonstram diferentes tipos de interação"""
    print("\n💬 Criando follow-ups representativos...")
    
    # Buscar alguns chamados para adicionar follow-ups
    chamados = db.query(Chamado).all()
    
    if len(chamados) < 4:
        print("⚠️ Poucos chamados disponíveis para follow-ups")
        return
    
    followups_data = [
        {
            "chamado_id": chamados[0].id,
            "tipo": TipoFollowUp.ANALISE.value,
            "descricao": "Análise inicial realizada. Identificado que o problema está relacionado à configuração do firewall.",
            "autor": "João Silva - Analista Sênior",
            "anexos": '["analise_firewall.pdf", "log_conexoes.txt"]'
        },
        {
            "chamado_id": chamados[1].id,
            "tipo": TipoFollowUp.DESENVOLVIMENTO.value,
            "descricao": "Iniciado desenvolvimento da correção. Estimativa de conclusão: 48 horas. Será necessário deploy em ambiente de homologação primeiro.",
            "autor": "Maria Santos - Desenvolvedora",
            "anexos": '["proposta_correcao.docx"]'
        },
        {
            "chamado_id": chamados[2].id,
            "tipo": TipoFollowUp.PUBLICACAO.value,
            "descricao": "Solução publicada em ambiente de produção com sucesso. Realizados testes de smoke e validação funcional. Monitoramento ativo por 24h.",
            "autor": "Carlos Lima - DevOps",
            "anexos": '["release_notes.pdf", "teste_smoke.html"]'
        },
        {
            "chamado_id": chamados[3].id,
            "tipo": TipoFollowUp.OUTROS.value,
            "descricao": "Cliente confirmou resolução do problema. Solicitado fechamento do chamado. Satisfação reportada: 9/10.",
            "autor": "Ana Costa - Relacionamento",
            "anexos": '[]'
        }
    ]
    
    for dados in followups_data:
        followup = FollowUp(**dados)
        db.add(followup)
    
    print(f"✅ Criados {len(followups_data)} follow-ups")

def main():
    """Função principal do script"""
    print("🚀 INICIANDO RECRIAÇÃO DE DADOS COERENTES COM TRIAGEM")
    print("=" * 60)
    
    # Carregar configurações
    config = load_triagem_config()
    print(f"📋 Configurações carregadas - Versão: {config['version']}")
    
    # Limpar banco
    db = limpar_banco()
    
    try:
        # Criar dados por categoria de score
        criar_chamados_score_baixo(db, config)
        criar_chamados_score_medio(db, config)
        criar_chamados_score_alto(db, config)
        
        # Commit para gerar os IDs dos chamados
        db.commit()
        
        criar_followups_representativos(db)
        
        # Commit final
        db.commit()
        
        # Verificar resultados
        total_chamados = db.query(Chamado).count()
        total_followups = db.query(FollowUp).count()
        
        print("\n" + "="*60)
        print("✅ RECRIAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 Total de chamados criados: {total_chamados}")
        print(f"💬 Total de follow-ups criados: {total_followups}")
        print("\n📈 DISTRIBUIÇÃO DE SCORES:")
        print("   🔴 Score 0-49 (Recusa): 5 chamados")
        print("   🟡 Score 50-69 (Revisão): 5 chamados") 
        print("   🟢 Score 70-100 (Aprovação): 5 chamados")
        print("\n🎯 CENÁRIOS CRIADOS:")
        print("   • Descrições extremamente curtas vs detalhadas")
        print("   • Clientes mal identificados vs bem especificados")
        print("   • Problemas vagos vs tecnicamente precisos")
        print("   • Sem anexos vs com anexos apropriados")
        print("   • Criticidade inadequada vs apropriada")
        print("   • Informações incompletas vs completas")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro durante criação: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()