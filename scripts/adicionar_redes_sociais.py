"""
Script para adicionar colunas de redes sociais na tabela barbearia
"""
import sys
import os

# Adiciona o diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sqlalchemy import text

def adicionar_colunas_redes_sociais():
    """Adiciona colunas instagram e whatsapp na tabela barbearia"""
    with app.app_context():
        try:
            # Verificar se as colunas já existem
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(barbearia)"))
                colunas_existentes = [row[1] for row in result]
                
                print(f"Colunas existentes: {colunas_existentes}")
                
                # Adicionar coluna instagram se não existir
                if 'instagram' not in colunas_existentes:
                    print("Adicionando coluna 'instagram'...")
                    conn.execute(text("ALTER TABLE barbearia ADD COLUMN instagram VARCHAR(200)"))
                    conn.commit()
                    print("✅ Coluna 'instagram' adicionada com sucesso!")
                else:
                    print("ℹ️  Coluna 'instagram' já existe")
                
                # Adicionar coluna whatsapp se não existir
                if 'whatsapp' not in colunas_existentes:
                    print("Adicionando coluna 'whatsapp'...")
                    conn.execute(text("ALTER TABLE barbearia ADD COLUMN whatsapp VARCHAR(20)"))
                    conn.commit()
                    print("✅ Coluna 'whatsapp' adicionada com sucesso!")
                else:
                    print("ℹ️  Coluna 'whatsapp' já existe")
                
                print("\n✅ Migração concluída com sucesso!")
                print("As barbearias agora podem ter Instagram e WhatsApp personalizados.")
                
        except Exception as e:
            print(f"\n❌ Erro ao adicionar colunas: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("ADICIONANDO COLUNAS DE REDES SOCIAIS")
    print("=" * 60)
    print()
    
    sucesso = adicionar_colunas_redes_sociais()
    
    if sucesso:
        print("\n" + "=" * 60)
        print("✅ SCRIPT EXECUTADO COM SUCESSO!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ SCRIPT FALHOU!")
        print("=" * 60)
        sys.exit(1)
