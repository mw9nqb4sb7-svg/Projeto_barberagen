"""
Script para adicionar a coluna 'username' na tabela Usuario
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
    cursor.execute("PRAGMA table_info(usuario)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'username' in columns:
        print("✓ A coluna 'username' já existe na tabela usuario")
    else:
        # Adicionar a coluna username (sem UNIQUE primeiro)
        cursor.execute("ALTER TABLE usuario ADD COLUMN username VARCHAR(50)")
        conn.commit()
        print("✓ Coluna 'username' adicionada com sucesso à tabela usuario")
        print("  (Nota: UNIQUE será validado no código da aplicação)")
    
    # Mostrar estrutura atual da tabela
    cursor.execute("PRAGMA table_info(usuario)")
    print("\n📋 Estrutura atual da tabela usuario:")
    for row in cursor.fetchall():
        print(f"   {row[1]} ({row[2]})")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\n✓ Concluído!")
