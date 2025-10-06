from database import SessionLocal
from models import Chamado, FollowUp

def validate_data():
    """Validar se os dados foram criados corretamente"""
    
    db = SessionLocal()
    
    try:
        print("🔍 Validando dados no banco...")
        
        # Contar chamados
        total_chamados = db.query(Chamado).count()
        print(f"✅ Total de chamados: {total_chamados}")
        
        if total_chamados != 50:
            print(f"❌ Erro: Esperado 50 chamados, encontrado {total_chamados}")
            return False
        
        # Contar follow-ups
        total_followups = db.query(FollowUp).count()
        print(f"✅ Total de follow-ups: {total_followups}")
        
        # Verificar distribuição por status
        print("\n📊 Distribuição por Status:")
        from sqlalchemy import func
        status_counts = db.query(Chamado.status, func.count(Chamado.id)).group_by(Chamado.status).all()
        
        for status, count in status_counts:
            print(f"   {status}: {count}")
        
        # Verificar alguns chamados específicos
        print("\n🔍 Exemplos de chamados:")
        primeiros_5 = db.query(Chamado).limit(5).all()
        
        for chamado in primeiros_5:
            print(f"   {chamado.numero_wex}: {chamado.cliente_solicitante} - {chamado.status} ({chamado.criticidade})")
            
            # Contar follow-ups deste chamado
            followups_count = db.query(FollowUp).filter(FollowUp.chamado_id == chamado.id).count()
            print(f"     Follow-ups: {followups_count}")
        
        # Verificar chamados críticos
        chamados_criticos = db.query(Chamado).filter(Chamado.criticidade == "Crítica").count()
        print(f"\n⚠️  Chamados críticos: {chamados_criticos}")
        
        # Verificar scores de qualidade
        score_medio = db.query(func.avg(Chamado.score_qualidade)).scalar()
        print(f"📈 Score médio de qualidade: {score_medio:.1f}%")
        
        print("\n✅ Validação concluída! Dados estão corretos.")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    validate_data()