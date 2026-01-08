"""
Script para adicionar a coluna 'username' na tabela Usuario
"""
import sqlite3
import os
import logging, sys

# Logger para scripts
logger = logging.getLogger('projeto_barber.scripts.adicionar_username')
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(_handler)

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'meubanco.db')

logger.info(f"Conectando ao banco de dados: {db_path}")

# Conectar ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(usuario)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'username' in columns:
        logger.info("A coluna 'username' já existe na tabela usuario")
    else:
        # Adicionar a coluna username (sem UNIQUE primeiro)
        cursor.execute("ALTER TABLE usuario ADD COLUMN username VARCHAR(50)")
        conn.commit()
        logger.info("Coluna 'username' adicionada com sucesso à tabela usuario")
        logger.info("(Nota: UNIQUE será validado no código da aplicação)")
    
    # Mostrar estrutura atual da tabela
    cursor.execute("PRAGMA table_info(usuario)")
    logger.info("Estrutura atual da tabela usuario:")
    for row in cursor.fetchall():
        logger.info(f"   {row[1]} ({row[2]})")
    
except Exception as e:
    logger.exception(f"Erro: {e}")
    conn.rollback()
finally:
    conn.close()
    logger.info("Concluído")
