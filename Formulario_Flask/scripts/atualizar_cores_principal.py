"""
Script para atualizar as cores da Barbearia Principal para o tema roxo e branco
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sqlalchemy import text

def atualizar_cores_barbearia_principal():
    """Atualiza as cores da barbearia principal para roxo e branco"""
    with app.app_context():
        try:
            # Cores do tema roxo
            cor_primaria = '#8B5CF6'  # Roxo vibrante
            cor_secundaria = '#A78BFA'  # Roxo claro
            cor_texto = '#1f2937'  # Texto escuro para fundo branco
            
            # Listar barbearias disponíveis
            print("📋 Barbearias disponíveis:")
            barbearias = db.session.execute(text("SELECT id, nome, slug FROM barbearia")).fetchall()
            for idx, barb in enumerate(barbearias, 1):
                print(f"   {idx}. ID: {barb[0]}, Nome: {barb[1]}, Slug: {barb[2]}")
            
            print("\n🎯 Atualizando TODAS as barbearias para o tema roxo...")
            
            # Atualizar TODAS as barbearias
            query = text("""
                UPDATE barbearia 
                SET cor_primaria = :cor_primaria,
                    cor_secundaria = :cor_secundaria,
                    cor_texto = :cor_texto
            """)
            
            result = db.session.execute(query, {
                'cor_primaria': cor_primaria,
                'cor_secundaria': cor_secundaria,
                'cor_texto': cor_texto
            })
            
            db.session.commit()
            
            print(f"\n✅ Cores atualizadas com sucesso!")
            print(f"   - Cor primária: {cor_primaria}")
            print(f"   - Cor secundária: {cor_secundaria}")
            print(f"   - Cor texto: {cor_texto}")
            print(f"   - Barbearias atualizadas: {result.rowcount}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao atualizar cores: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🎨 Iniciando atualização das cores da barbearia principal...")
    print("=" * 60)
    atualizar_cores_barbearia_principal()
    print("=" * 60)
