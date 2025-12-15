"""
Script para criar planos mensais de exemplo
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório pai ao path
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from app import app, db, PlanoMensal, Barbearia
import json

def criar_planos_exemplo():
    """Cria planos mensais de exemplo para todas as barbearias"""
    with app.app_context():
        print("💎 Criando planos mensais de exemplo...\n")
        
        try:
            # Buscar todas as barbearias
            barbearias = Barbearia.query.filter_by(ativa=True).all()
            
            if not barbearias:
                print("❌ Nenhuma barbearia encontrada no banco de dados")
                return
            
            planos_template = [
                {
                    'nome': 'Plano Básico',
                    'descricao': 'Ideal para quem quer manter o visual sempre em dia com economia',
                    'preco': 79.90,
                    'atendimentos_mes': 2,
                    'beneficios': [
                        'Corte de cabelo incluso',
                        'Desconto de 10% em produtos',
                        'Agendamento prioritário',
                        'Atendimento sem fila'
                    ]
                },
                {
                    'nome': 'Plano Premium',
                    'descricao': 'Para quem busca o cuidado completo e não abre mão da qualidade',
                    'preco': 149.90,
                    'atendimentos_mes': 4,
                    'beneficios': [
                        'Corte + Barba inclusos',
                        'Desconto de 20% em produtos',
                        'Agendamento prioritário VIP',
                        'Atendimento sem fila',
                        'Toalha quente de cortesia',
                        'Bebida premium incluída'
                    ]
                },
                {
                    'nome': 'Plano Black',
                    'descricao': 'A experiência mais completa da barbearia com benefícios exclusivos',
                    'preco': 249.90,
                    'atendimentos_mes': 8,
                    'beneficios': [
                        'Serviços ilimitados no mês',
                        'Desconto de 30% em produtos',
                        'Agendamento prioritário Black',
                        'Sem necessidade de fila',
                        'Toalha quente de cortesia',
                        'Bebida premium incluída',
                        'Tratamento capilar mensal',
                        'Acesso a eventos exclusivos'
                    ]
                }
            ]
            
            total_criados = 0
            
            for barbearia in barbearias:
                print(f"📍 Barbearia: {barbearia.nome}")
                
                for plano_data in planos_template:
                    # Verificar se já existe
                    plano_existente = PlanoMensal.query.filter_by(
                        barbearia_id=barbearia.id,
                        nome=plano_data['nome']
                    ).first()
                    
                    if plano_existente:
                        print(f"   ⚠️  {plano_data['nome']} já existe")
                        continue
                    
                    # Criar novo plano
                    plano = PlanoMensal(
                        barbearia_id=barbearia.id,
                        nome=plano_data['nome'],
                        descricao=plano_data['descricao'],
                        preco=plano_data['preco'],
                        atendimentos_mes=plano_data['atendimentos_mes'],
                        ativo=True
                    )
                    plano.set_beneficios(plano_data['beneficios'])
                    
                    db.session.add(plano)
                    print(f"   ✅ {plano_data['nome']} criado - R$ {plano_data['preco']:.2f}")
                    total_criados += 1
                
                print()
            
            db.session.commit()
            
            print(f"\n✨ Total de planos criados: {total_criados}")
            print("🎉 Processo concluído com sucesso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar planos: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    criar_planos_exemplo()
