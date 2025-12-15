"""
Script para adicionar tabelas de Planos Mensais ao banco de dados
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório pai ao path
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from app import app, db, PlanoMensal, AssinaturaPlano

def adicionar_tabelas_planos():
    """Adiciona as tabelas de planos mensais ao banco de dados"""
    with app.app_context():
        print("🔧 Criando tabelas de planos mensais...")
        
        try:
            # Criar as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se as tabelas foram criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'plano_mensal' in tables:
                print("✅ Tabela 'plano_mensal' criada")
            else:
                print("❌ Tabela 'plano_mensal' não foi criada")
                
            if 'assinatura_plano' in tables:
                print("✅ Tabela 'assinatura_plano' criada")
            else:
                print("❌ Tabela 'assinatura_plano' não foi criada")
            
            print("\n✨ Processo concluído!")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    adicionar_tabelas_planos()
