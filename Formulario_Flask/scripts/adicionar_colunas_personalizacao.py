"""
Script para adicionar colunas de personalização na tabela barbearia
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sqlalchemy import text

def adicionar_colunas_personalizacao():
    """Adiciona colunas de personalização visual à tabela barbearia"""
    with app.app_context():
        try:
            # Lista de colunas para adicionar
            colunas = [
                ("hero_titulo", "TEXT", "Seu visual|no nível máximo"),
                ("hero_subtitulo", "TEXT", "Mais que um corte de cabelo, uma experiência completa. Profissionais qualificados, ambiente moderno e atendimento premium."),
                ("slogan", "VARCHAR(200)", "Estilo e Tradição"),
                ("cor_primaria", "VARCHAR(10)", "#8b5cf6"),
                ("cor_secundaria", "VARCHAR(10)", "#A78BFA"),
                ("cor_texto", "VARCHAR(10)", "#1f2937"),
                ("card1_icone", "VARCHAR(10)", "✂️"),
                ("card1_titulo", "VARCHAR(100)", "Corte masculino"),
                ("card1_descricao", "TEXT", "Cortes modernos e clássicos com acabamento perfeito, realizado por barbeiros experientes"),
                ("card2_icone", "VARCHAR(10)", "🧔"),
                ("card2_titulo", "VARCHAR(100)", "Barba completa"),
                ("card2_descricao", "TEXT", "Design, aparação e tratamento completo para sua barba ficar impecável"),
                ("card3_icone", "VARCHAR(10)", "💈"),
                ("card3_titulo", "VARCHAR(100)", "Combo premium"),
                ("card3_descricao", "TEXT", "Corte + barba + finalização, o pacote completo para você sair renovado"),
                ("card4_icone", "VARCHAR(10)", "📅"),
                ("card4_titulo", "VARCHAR(100)", "Agendamento fácil"),
                ("card4_descricao", "TEXT", "Reserve seu horário online de forma rápida e prática, sem complicação"),
            ]
            
            print("🔍 Verificando colunas existentes...")
            
            # Verificar quais colunas já existem
            result = db.session.execute(text("PRAGMA table_info(barbearia)"))
            colunas_existentes = [row[1] for row in result.fetchall()]
            
            print(f"✅ Colunas atuais: {', '.join(colunas_existentes)}")
            print()
            
            colunas_adicionadas = []
            colunas_ja_existentes = []
            
            for coluna_nome, coluna_tipo, valor_default in colunas:
                if coluna_nome in colunas_existentes:
                    colunas_ja_existentes.append(coluna_nome)
                    print(f"⚠️  Coluna '{coluna_nome}' já existe")
                else:
                    try:
                        # Adicionar coluna
                        if 'VARCHAR' in coluna_tipo or 'TEXT' in coluna_tipo:
                            query = text(f"ALTER TABLE barbearia ADD COLUMN {coluna_nome} {coluna_tipo} DEFAULT '{valor_default}'")
                        else:
                            query = text(f"ALTER TABLE barbearia ADD COLUMN {coluna_nome} {coluna_tipo} DEFAULT {valor_default}")
                        
                        db.session.execute(query)
                        db.session.commit()
                        colunas_adicionadas.append(coluna_nome)
                        print(f"✅ Coluna '{coluna_nome}' adicionada com sucesso")
                    except Exception as e:
                        print(f"❌ Erro ao adicionar coluna '{coluna_nome}': {str(e)}")
                        db.session.rollback()
            
            print()
            print("=" * 60)
            print(f"📊 Resumo:")
            print(f"   - Colunas já existentes: {len(colunas_ja_existentes)}")
            print(f"   - Colunas adicionadas: {len(colunas_adicionadas)}")
            print(f"   - Total de colunas: {len(colunas)}")
            
            if colunas_adicionadas:
                print(f"\n✅ Novas colunas: {', '.join(colunas_adicionadas)}")
            
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro geral: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🎨 Iniciando adição de colunas de personalização...")
    print("=" * 60)
    adicionar_colunas_personalizacao()
