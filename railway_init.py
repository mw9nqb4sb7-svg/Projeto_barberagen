#!/usr/bin/env python3
"""
Script de inicialização para Railway
Executa migrações e configurações iniciais do banco de dados
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def init_database():
    """Inicializa o banco de dados e cria tabelas se necessário"""
    try:
        from app import db, app

        with app.app_context():
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas/verficadas com sucesso")

            # Verificar se já existe super admin
            from app import Usuario
            super_admin = Usuario.query.filter_by(tipo_conta='super_admin').first()
            if not super_admin:
                print("⚠️ Criando super admin padrão...")
                novo_admin = Usuario(
                    nome="Super Admin",
                    username="lualmeida",
                    email="admin@barberconnect.com",
                    tipo_conta="super_admin",
                    ativo=True
                )
                novo_admin.set_senha("562402")
                db.session.add(novo_admin)
                db.session.commit()
                print("✅ Super admin 'lualmeida' criado com sucesso!")
            else:
                print(f"✅ Super admin já configurado: {super_admin.username}")

    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        return False

    return True

def check_environment():
    """Verifica se todas as variáveis de ambiente necessárias estão configuradas"""
    # DATABASE_URL é opcional, se faltar usa SQLite
    required_vars = ['FLASK_SECRET']
    missing_vars = []

    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"⚠️  Variáveis de ambiente críticas faltando: {', '.join(missing_vars)}")
        return False

    if not os.environ.get('DATABASE_URL'):
        print("ℹ️  DATABASE_URL não configurada. Usando SQLite local (não recomendado para produção persistente).")

    print("✅ Variáveis de ambiente verificadas")
    return True

if __name__ == '__main__':
    print("🚀 Inicializando aplicação BarberConnect no Railway...")

    # Verificar ambiente
    if not check_environment():
        sys.exit(1)

    # Inicializar banco de dados
    if not init_database():
        sys.exit(1)

    print("🎉 Inicialização concluída com sucesso!")