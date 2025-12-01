"""
Script para adicionar a coluna 'logo' na tabela Barbearia
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'meubanco.db')

print(f"Conectando ao banco de dados: {db_path}")

# Conectar ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(barbearia)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'logo' in columns:
        print("✓ A coluna 'logo' já existe na tabela barbearia")
    else:
        # Adicionar a coluna logo
        cursor.execute("ALTER TABLE barbearia ADD COLUMN logo VARCHAR(200)")
        conn.commit()
        print("✓ Coluna 'logo' adicionada com sucesso à tabela barbearia")
    
    # Mostrar estrutura atual da tabela
    cursor.execute("PRAGMA table_info(barbearia)")
    print("\n📋 Estrutura atual da tabela barbearia:")
    for row in cursor.fetchall():
        print(f"   {row[1]} ({row[2]})")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\n✓ Concluído!")
