"""
Script para criar/atualizar super admin com username
Username: lualmeida
Senha: 562402
"""
import sqlite3
import os
import uuid as uuid_lib
from werkzeug.security import generate_password_hash
import logging, sys

# Logger para scripts
logger = logging.getLogger('projeto_barber.scripts.configurar_super_admin')
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(_handler)

# Caminho do banco de dados (subir um nível da pasta scripts)
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'meubanco.db')

logger.info(f"Conectando ao banco de dados: {db_path}")

# Conectar ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    username = 'lualmeida'
    senha = '562402'
    senha_hash = generate_password_hash(senha)
    
    # Verificar se já existe um super admin
    cursor.execute("SELECT id, nome, email, username FROM usuario WHERE tipo_conta = 'super_admin'")
    super_admin = cursor.fetchone()
    
    if super_admin:
        admin_id, nome, email, username_atual = super_admin
        logger.info("Super Admin existente encontrado:")
        logger.info(f"  ID: {admin_id}")
        logger.info(f"  Nome: {nome}")
        logger.info(f"  Email: {email}")
        logger.info(f"  Username atual: {username_atual or 'Nenhum'}")
        
        # Atualizar username e senha
        cursor.execute("""
            UPDATE usuario 
            SET username = ?, senha = ? 
            WHERE id = ?
        """, (username, senha_hash, admin_id))
        conn.commit()
        
        logger.info("Super Admin atualizado com sucesso")
        logger.info(f"   Username: {username}")
        logger.info(f"   Senha: {senha}")
        
    else:
        logger.info('Nenhum super admin encontrado no sistema')
        logger.info('Criando novo super admin...')
        
        # Gerar UUID
        user_uuid = str(uuid_lib.uuid4())
        
        # Criar novo super admin
        cursor.execute("""
            INSERT INTO usuario (uuid, nome, email, username, senha, tipo_conta, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_uuid, 'Super Admin', 'superadmin@sistema.com', username, senha_hash, 'super_admin', 1))
        conn.commit()
        
        logger.info('Super Admin criado com sucesso')
        logger.info(f"   Nome: Super Admin")
        logger.info(f"   Username: {username}")
        logger.info(f"   Email: superadmin@sistema.com")
        logger.info(f"   Senha: {senha}")
    
    logger.info('Credenciais de acesso:')
    logger.info(f"   URL: http://localhost:5000/super_admin/login")
    logger.info(f"   Usuário: {username}")
    logger.info(f"   Senha: {senha}")
    
except Exception as e:
    logger.exception(f"Erro: {e}")
    conn.rollback()
finally:
    conn.close()
    logger.info("Concluído")
