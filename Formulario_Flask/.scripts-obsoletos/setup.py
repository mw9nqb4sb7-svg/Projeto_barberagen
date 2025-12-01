#!/usr/bin/env python3
"""
Script de inicialização para desenvolvimento
Configura o banco de dados e cria usuários de exemplo
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

def init_database():
    """Inicializa o banco de dados"""
    print("🗄️  Inicializando banco de dados...")
    
    from app import app, db
    
    with app.app_context():
        # Criar tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")

def create_super_admin():
    """Cria o super administrador"""
    print("👨‍💼 Criando super administrador...")
    
    try:
        # Executar script de criação do super admin
        exec(open('criar_super_admin.py').read())
        print("✅ Super admin criado com sucesso!")
    except Exception as e:
        print(f"⚠️  Super admin já existe ou erro: {e}")

def create_example_barbearia():
    """Cria barbearia de exemplo"""
    print("🏪 Criando barbearia de exemplo...")
    
    try:
        # Executar script de criação da barbearia
        exec(open('criar_barbearia_man.py').read())
        print("✅ Barbearia exemplo criada com sucesso!")
    except Exception as e:
        print(f"⚠️  Barbearia já existe ou erro: {e}")

def main():
    """Função principal de inicialização"""
    print("=" * 50)
    print("🚀 INICIALIZAÇÃO DO SISTEMA DE BARBEARIAS")
    print("=" * 50)
    
    # Verificar se já existe banco
    db_exists = os.path.exists('meubanco.db')
    
    if not db_exists:
        print("📦 Configuração inicial do projeto...")
        init_database()
        create_super_admin()
        create_example_barbearia()
    else:
        print("📊 Banco de dados já existe.")
        
        choice = input("Deseja recriar os dados de exemplo? (s/N): ").strip().lower()
        if choice == 's':
            create_super_admin()
            create_example_barbearia()
    
    print("\n" + "=" * 50)
    print("✅ SISTEMA PRONTO PARA USO!")
    print("=" * 50)
    print("🌐 URLs de Acesso:")
    print("   Super Admin: http://localhost:5000/super_admin/login")
    print("   Barbearia Man: http://localhost:5000/man/")
    print("\n🔑 Credenciais Padrão:")
    print("   Super Admin: superadmin@sistema.com / admin123")
    print("   Admin Man: admin@man.com / admin123")
    print("   Barbeiro Man: barbeiro@man.com / barbeiro123")
    print("\n🚀 Para iniciar o servidor:")
    print("   python app.py")
    print("=" * 50)

if __name__ == "__main__":
    main()