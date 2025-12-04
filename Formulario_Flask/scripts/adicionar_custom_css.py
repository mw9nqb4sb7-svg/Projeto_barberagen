"""
Script para adicionar a coluna custom_css na tabela Barbearia
Permite que cada barbearia tenha seu próprio CSS personalizado
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório pai ao path
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, BASE_DIR)

from app import app, db, Barbearia

def adicionar_coluna_custom_css():
    """Adiciona a coluna custom_css à tabela Barbearia se ela não existir"""
    
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('barbearia')]
            
            if 'custom_css' in columns:
                print("✅ A coluna 'custom_css' já existe na tabela Barbearia!")
                return
            
            # Adicionar a coluna usando SQL direto
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE barbearia ADD COLUMN custom_css TEXT"))
                conn.commit()
            
            print("✅ Coluna 'custom_css' adicionada com sucesso à tabela Barbearia!")
            print("📝 Agora cada barbearia pode ter seu próprio CSS personalizado.")
            
            # Mostrar estatísticas
            total_barbearias = Barbearia.query.count()
            print(f"\n📊 Total de barbearias no sistema: {total_barbearias}")
            
            if total_barbearias > 0:
                print("\n💡 Dica: Use a interface de administração para adicionar CSS personalizado a cada barbearia.")
            
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🎨 Adicionando suporte para CSS personalizado por barbearia...")
    print("-" * 60)
    adicionar_coluna_custom_css()
    print("-" * 60)
    print("✨ Processo concluído!")
