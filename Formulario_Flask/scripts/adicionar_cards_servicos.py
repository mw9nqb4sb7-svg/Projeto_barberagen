"""
Script para adicionar campos de personalização dos 4 cards de serviços
"""

import os
import sys

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import inspect, text

def adicionar_colunas():
    """Adiciona as colunas de personalização dos cards de serviços"""
    with app.app_context():
        inspector = inspect(db.engine)
        colunas_existentes = [col['name'] for col in inspector.get_columns('barbearia')]
        
        # Lista de colunas a serem adicionadas (4 cards x 3 campos = 12 colunas)
        novas_colunas = [
            # Card 1
            ('card1_icone', 'TEXT DEFAULT "✂️"'),
            ('card1_titulo', 'TEXT DEFAULT "Corte masculino"'),
            ('card1_descricao', 'TEXT DEFAULT "Cortes modernos e clássicos com acabamento perfeito, realizado por barbeiros experientes"'),
            
            # Card 2
            ('card2_icone', 'TEXT DEFAULT "🧔"'),
            ('card2_titulo', 'TEXT DEFAULT "Barba completa"'),
            ('card2_descricao', 'TEXT DEFAULT "Design, aparação e tratamento completo para sua barba ficar impecável"'),
            
            # Card 3
            ('card3_icone', 'TEXT DEFAULT "💈"'),
            ('card3_titulo', 'TEXT DEFAULT "Combo premium"'),
            ('card3_descricao', 'TEXT DEFAULT "Corte + barba + finalização, o pacote completo para você sair renovado"'),
            
            # Card 4
            ('card4_icone', 'TEXT DEFAULT "📅"'),
            ('card4_titulo', 'TEXT DEFAULT "Agendamento fácil"'),
            ('card4_descricao', 'TEXT DEFAULT "Reserve seu horário online de forma rápida e prática, sem complicação"'),
        ]
        
        # Adiciona cada coluna se não existir
        for nome_coluna, tipo_coluna in novas_colunas:
            if nome_coluna not in colunas_existentes:
                try:
                    sql = f'ALTER TABLE barbearia ADD COLUMN {nome_coluna} {tipo_coluna}'
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"✅ Coluna '{nome_coluna}' adicionada com sucesso!")
                except Exception as e:
                    print(f"❌ Erro ao adicionar coluna '{nome_coluna}': {e}")
                    db.session.rollback()
            else:
                print(f"ℹ️ Coluna '{nome_coluna}' já existe")
        
        print("\n✅ Migração concluída com sucesso!")

if __name__ == '__main__':
    print("🚀 Iniciando migração - Adicionando campos dos cards de serviços...")
    adicionar_colunas()
    print("🎉 Processo finalizado!")
