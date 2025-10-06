import random
import json
from datetime import datetime, timedelta
from database import SessionLocal
from models import Chamado, FollowUp, StatusChamado, CriticidadeChamado, TipoFollowUp

def generate_mock_data():
    """Gerar dados mockados realistas para o sistema"""
    
    db = SessionLocal()
    
    try:
        # Limpar dados existentes
        db.query(FollowUp).delete()
        db.query(Chamado).delete()
        db.commit()
        
        print("Dados anteriores removidos...")
        
        # Lista de clientes realistas
        clientes = [
            "Empresa ABC Tecnologia Ltda",
            "XYZ Corporation Brasil",
            "Inovação Digital S.A.",
            "TechSolutions Consulting",
            "DataFlow Systems",
            "CloudFirst Technologies",
            "NextGen Software",
            "DigitalBridge Corp",
            "SmartSystems Brasil",
            "FutureTech Solutions",
            "GlobalData Analytics",
            "InnovateCorp",
            "TechVanguard Ltd",
            "DigitalTransform S.A.",
            "CyberSolutions Group"
        ]
        
        # Tipos de problemas realistas
        problemas_templates = [
            {
                "base": "Sistema apresentando lentidão no módulo de {modulo}",
                "modulos": ["relatórios", "dashboard", "cadastro", "consultas", "processamento"],
                "tags": ["performance", "lentidão"],
                "criticidade_peso": {"Baixa": 0.2, "Média": 0.4, "Alta": 0.3, "Crítica": 0.1}
            },
            {
                "base": "Erro {erro} ao tentar acessar {funcionalidade}",
                "erros": ["500", "404", "403", "timeout"],
                "funcionalidades": ["dashboard", "relatórios", "configurações", "usuários", "sistema"],
                "tags": ["erro", "acesso"],
                "criticidade_peso": {"Baixa": 0.1, "Média": 0.2, "Alta": 0.4, "Crítica": 0.3}
            },
            {
                "base": "Problema de integração com {sistema} - {detalhe}",
                "sistemas": ["API externa", "banco de dados", "sistema legado", "serviço terceirizado"],
                "detalhes": ["dados não sincronizando", "falha na comunicação", "timeout nas requisições"],
                "tags": ["integração", "api"],
                "criticidade_peso": {"Baixa": 0.15, "Média": 0.35, "Alta": 0.35, "Crítica": 0.15}
            },
            {
                "base": "Solicitação de {tipo_solicitacao} para {objeto}",
                "tipo_solicitacoes": ["nova funcionalidade", "melhoria", "customização", "relatório personalizado"],
                "objetos": ["módulo de vendas", "dashboard gerencial", "processo de aprovação", "interface do usuário"],
                "tags": ["solicitação", "melhoria"],
                "criticidade_peso": {"Baixa": 0.4, "Média": 0.4, "Alta": 0.15, "Crítica": 0.05}
            },
            {
                "base": "Falha na {operacao} de {objeto} - {sintoma}",
                "operacoes": ["gravação", "consulta", "exclusão", "atualização"],
                "objetos": ["dados de cliente", "pedidos", "relatórios", "configurações"],
                "sintomas": ["dados não salvos", "informações incorretas", "processo interrompido"],
                "tags": ["falha", "dados"],
                "criticidade_peso": {"Baixa": 0.2, "Média": 0.3, "Alta": 0.3, "Crítica": 0.2}
            }
        ]
        
        # Gerar 50 chamados
        chamados_criados = []
        
        for i in range(1, 51):
            # Selecionar template aleatório
            template = random.choice(problemas_templates)
            
            # Gerar descrição baseada no template
            if "modulos" in template:
                descricao = template["base"].format(modulo=random.choice(template["modulos"]))
            elif "erros" in template:
                descricao = template["base"].format(
                    erro=random.choice(template["erros"]),
                    funcionalidade=random.choice(template["funcionalidades"])
                )
            elif "sistemas" in template:
                descricao = template["base"].format(
                    sistema=random.choice(template["sistemas"]),
                    detalhe=random.choice(template["detalhes"])
                )
            elif "tipo_solicitacoes" in template:
                descricao = template["base"].format(
                    tipo_solicitacao=random.choice(template["tipo_solicitacoes"]),
                    objeto=random.choice(template["objetos"])
                )
            else:  # falhas
                descricao = template["base"].format(
                    operacao=random.choice(template["operacoes"]),
                    objeto=random.choice(template["objetos"]),
                    sintoma=random.choice(template["sintomas"])
                )
            
            # Adicionar detalhes extras aleatoriamente
            detalhes_extras = [
                " Usuários relatam impacto na produtividade.",
                " Problema intermitente observado nas últimas horas.",
                " Solicitação urgente da direção.",
                " Afetando múltiplos usuários simultaneamente.",
                " Erro reproduzível em ambiente de produção.",
                " Necessário análise técnica detalhada.",
                " Problema relatado pelo cliente prioritário.",
                " Impacto em processos críticos do negócio."
            ]
            
            if random.random() < 0.6:  # 60% chance de adicionar detalhe extra
                descricao += random.choice(detalhes_extras)
            
            # Escolher criticidade baseada nos pesos do template
            criticidades = list(template["criticidade_peso"].keys())
            pesos = list(template["criticidade_peso"].values())
            criticidade = random.choices(criticidades, weights=pesos)[0]
            
            # Gerar status baseado na probabilidade
            status_opcoes = [
                (StatusChamado.ABERTO.value, 0.3),
                (StatusChamado.EM_ANALISE.value, 0.25),
                (StatusChamado.PENDENTE.value, 0.15),
                (StatusChamado.RESOLVIDO.value, 0.2),
                (StatusChamado.FECHADO.value, 0.1)
            ]
            status = random.choices([s[0] for s in status_opcoes], weights=[s[1] for s in status_opcoes])[0]
            
            # Data de criação nos últimos 30 dias
            data_criacao = datetime.now() - timedelta(days=random.randint(0, 30))
            
            # SLA baseado na criticidade
            sla_horas = {
                "Crítica": 4,
                "Alta": 24,
                "Média": 72,
                "Baixa": 120
            }
            sla_limite = data_criacao + timedelta(hours=sla_horas[criticidade])
            
            # Score de qualidade baseado em critérios
            score_base = 50
            if "timeout" in descricao.lower() or "erro" in descricao.lower():
                score_base += 20  # Problema técnico bem definido
            if "usuários relatam" in descricao.lower():
                score_base += 15  # Informação de impacto
            if len(descricao) > 100:
                score_base += 10  # Descrição detalhada
            if random.random() < 0.3:  # 30% chance de ambiente informado
                score_base += 15
                ambiente_informado = True
            else:
                ambiente_informado = False
            
            # Anexos baseados no tipo de problema
            possui_anexos = random.random() < 0.4  # 40% chance
            if "erro" in descricao.lower():
                possui_anexos = random.random() < 0.7  # 70% chance para erros
            
            # Garantir score entre 0-100
            score_qualidade = min(100, max(0, score_base + random.randint(-15, 15)))
            
            # Criar chamado
            chamado = Chamado(
                numero_wex=f"WEX-2025-{i:03d}",
                cliente_solicitante=random.choice(clientes),
                descricao=descricao,
                status=status,
                criticidade=criticidade,
                data_criacao=data_criacao,
                data_atualizacao=data_criacao + timedelta(hours=random.randint(1, 48)),
                sla_limite=sla_limite,
                tags_automaticas=json.dumps(template["tags"] + [random.choice(["produção", "desenvolvimento", "teste"])]),
                score_qualidade=score_qualidade,
                ambiente_informado=ambiente_informado,
                possui_anexos=possui_anexos
            )
            
            db.add(chamado)
            db.flush()  # Para obter o ID
            chamados_criados.append(chamado)
            
            print(f"Chamado {i}/50 criado: {chamado.numero_wex} - {criticidade}")
        
        # Gerar follow-ups para os chamados
        tipos_followup = [
            (TipoFollowUp.ANALISE.value, "Iniciada análise do problema reportado."),
            (TipoFollowUp.ANALISE.value, "Logs do sistema coletados para investigação."),
            (TipoFollowUp.DESENVOLVIMENTO.value, "Identificada causa raiz do problema."),
            (TipoFollowUp.DESENVOLVIMENTO.value, "Correção implementada no ambiente de desenvolvimento."),
            (TipoFollowUp.PUBLICACAO.value, "Deploy da correção realizado em produção."),
            (TipoFollowUp.PUBLICACAO.value, "Atualização do sistema concluída com sucesso."),
            (TipoFollowUp.OUTROS.value, "Contato realizado com o cliente para mais informações."),
            (TipoFollowUp.OUTROS.value, "Documentação atualizada com nova informação."),
        ]
        
        autores = [
            "João Silva - Suporte Técnico",
            "Maria Santos - Analista de Sistemas", 
            "Pedro Oliveira - Desenvolvedor",
            "Ana Costa - DBA",
            "Carlos Ferreira - DevOps",
            "Lucia Almeida - QA",
            "Roberto Lima - Arquiteto",
            "Fernanda Rocha - Product Owner"
        ]
        
        total_followups = 0
        
        for chamado in chamados_criados:
            # Quantidade de follow-ups baseada no status
            if chamado.status == StatusChamado.FECHADO.value:
                num_followups = random.randint(2, 5)
            elif chamado.status == StatusChamado.RESOLVIDO.value:
                num_followups = random.randint(1, 4)
            elif chamado.status in [StatusChamado.EM_ANALISE.value, StatusChamado.PENDENTE.value]:
                num_followups = random.randint(1, 3)
            else:  # Aberto
                num_followups = random.randint(0, 2)
            
            for j in range(num_followups):
                tipo, descricao_base = random.choice(tipos_followup)
                
                # Personalizar descrição baseada no contexto
                if "erro" in chamado.descricao.lower() and tipo == TipoFollowUp.ANALISE.value:
                    descricao_base = f"Analisando erro reportado: {descricao_base}"
                elif "lentidão" in chamado.descricao.lower() and tipo == TipoFollowUp.DESENVOLVIMENTO.value:
                    descricao_base = "Otimização de performance implementada."
                
                data_followup = chamado.data_criacao + timedelta(hours=random.randint(1, 48*(j+1)))
                
                # Anexos ocasionais
                anexos = []
                if random.random() < 0.3:  # 30% chance
                    anexos_possiveis = [
                        "log_analise.txt",
                        "screenshot_erro.png", 
                        "relatorio_performance.pdf",
                        "documentacao_tecnica.docx",
                        "script_correcao.sql"
                    ]
                    anexos = [random.choice(anexos_possiveis)]
                
                followup = FollowUp(
                    chamado_id=chamado.id,
                    tipo=tipo,
                    descricao=descricao_base,
                    data_criacao=data_followup,
                    autor=random.choice(autores),
                    anexos=json.dumps(anexos)
                )
                
                db.add(followup)
                total_followups += 1
        
        # Commit todas as mudanças
        db.commit()
        
        print(f"\n✅ Dados mockados gerados com sucesso!")
        print(f"📋 {len(chamados_criados)} chamados criados")
        print(f"💬 {total_followups} follow-ups criados")
        
        # Estatísticas
        stats = {}
        for chamado in chamados_criados:
            status = chamado.status
            stats[status] = stats.get(status, 0) + 1
        
        print(f"\n📊 Distribuição por Status:")
        for status, count in stats.items():
            print(f"   {status}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar dados: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Iniciando geração de dados mockados...")
    success = generate_mock_data()
    
    if success:
        print("\n🎉 Processo concluído! O sistema está pronto para demonstração.")
    else:
        print("\n💥 Falha na geração dos dados. Verifique os logs acima.")