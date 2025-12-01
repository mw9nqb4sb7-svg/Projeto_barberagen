"""
Script para criar/atualizar super admin com username
Username: lualmeida
Senha: 562402
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'meubanco.db')

print(f"Conectando ao banco de dados: {db_path}")

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
        print(f"\n✓ Super Admin existente encontrado:")
        print(f"  ID: {admin_id}")
        print(f"  Nome: {nome}")
        print(f"  Email: {email}")
        print(f"  Username atual: {username_atual or 'Nenhum'}")
        
        # Atualizar username e senha
        cursor.execute("""
            UPDATE usuario 
            SET username = ?, senha = ? 
            WHERE id = ?
        """, (username, senha_hash, admin_id))
        conn.commit()
        
        print(f"\n✅ Super Admin atualizado com sucesso!")
        print(f"   Username: {username}")
        print(f"   Senha: {senha}")
        
    else:
        print("\n❌ Nenhum super admin encontrado no sistema")
        print("Criando novo super admin...")
        
        # Criar novo super admin
        cursor.execute("""
            INSERT INTO usuario (nome, email, username, senha, tipo_conta, ativo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('Super Admin', 'superadmin@sistema.com', username, senha_hash, 'super_admin', 1))
        conn.commit()
        
        print(f"\n✅ Super Admin criado com sucesso!")
        print(f"   Nome: Super Admin")
        print(f"   Username: {username}")
        print(f"   Email: superadmin@sistema.com")
        print(f"   Senha: {senha}")
    
    print("\n📋 Credenciais de acesso:")
    print(f"   URL: http://localhost:5000/super_admin/login")
    print(f"   Usuário: {username}")
    print(f"   Senha: {senha}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\n✓ Concluído!")
