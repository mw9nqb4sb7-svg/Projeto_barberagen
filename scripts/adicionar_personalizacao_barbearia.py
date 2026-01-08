#!/usr/bin/env python3
"""
Script para adicionar campos de personalização nas barbearias
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sqlalchemy import text

def adicionar_colunas_personalizacao():
    """Adiciona colunas para personalização visual da barbearia"""
    
    print("🎨 Adicionando campos de personalização às barbearias...\n")
    
    with app.app_context():
        try:
            # Verificar se as colunas já existem
            inspector = db.inspect(db.engine)
            colunas_existentes = [col['name'] for col in inspector.get_columns('barbearia')]
            
            colunas_para_adicionar = {
                'hero_titulo': "ALTER TABLE barbearia ADD COLUMN hero_titulo TEXT DEFAULT 'Seu visual no máximo. Profissionalismo em cada detalhe.'",
                'hero_subtitulo': "ALTER TABLE barbearia ADD COLUMN hero_subtitulo TEXT DEFAULT 'Agende seu horário com praticidade e estilo. Cortes modernos e atendimento de excelência.'",
                'cor_primaria': "ALTER TABLE barbearia ADD COLUMN cor_primaria VARCHAR(7) DEFAULT '#8b5cf6'",
                'cor_secundaria': "ALTER TABLE barbearia ADD COLUMN cor_secundaria VARCHAR(7) DEFAULT '#7c3aed'",
                'cor_texto': "ALTER TABLE barbearia ADD COLUMN cor_texto VARCHAR(7) DEFAULT '#1f2937'",
                'slogan': "ALTER TABLE barbearia ADD COLUMN slogan TEXT DEFAULT 'Estilo e Tradição'"
            }
            
            for coluna, sql in colunas_para_adicionar.items():
                if coluna not in colunas_existentes:
                    print(f"  ➕ Adicionando coluna '{coluna}'...")
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"     ✅ Coluna '{coluna}' adicionada com sucesso!")
                else:
                    print(f"  ⚠️  Coluna '{coluna}' já existe, pulando...")
            
            print("\n✅ Migração concluída com sucesso!")
            print("\n📝 Campos adicionados:")
            print("   • hero_titulo - Título principal da home page")
            print("   • hero_subtitulo - Subtítulo da home page")
            print("   • cor_primaria - Cor primária do tema (#8b5cf6)")
            print("   • cor_secundaria - Cor secundária do tema (#7c3aed)")
            print("   • cor_texto - Cor do texto principal (#1f2937)")
            print("   • slogan - Slogan da barbearia")
            
        except Exception as e:
            print(f"\n❌ Erro ao adicionar colunas: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    try:
        adicionar_colunas_personalizacao()
        print("\n🎉 Script executado com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {str(e)}")
        sys.exit(1)
