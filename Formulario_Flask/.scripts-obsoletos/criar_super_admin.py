"""
Script para criar super admin do sistema
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Configurar Flask e SQLAlchemy independente
BASE_DIR = str(Path(__file__).resolve().parent)
DB_PATH = os.path.join(BASE_DIR, 'meubanco.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Redefinir modelo Usuario para o script
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    tipo_conta = db.Column(db.String(20), nullable=False, default='cliente')

def criar_super_admin():
    """Cria o super admin do sistema"""
    print("🔄 Criando super admin do sistema...")
    
    with app.app_context():
        # Verificar se já existe super admin
        super_admin_existente = Usuario.query.filter_by(tipo_conta='super_admin').first()
        if super_admin_existente:
            print(f"✅ Super admin já existe: {super_admin_existente.email}")
            return True
        
        # Criar super admin
        super_admin = Usuario(
            nome="Super Administrador",
            email="superadmin@sistema.com",
            senha=generate_password_hash("super123"),
            telefone="(11) 00000-0000",
            tipo_conta="super_admin",
            ativo=True
        )
        
        db.session.add(super_admin)
        db.session.commit()
        
        print("✅ Super admin criado com sucesso!")
        print("\n📋 Dados do Super Admin:")
        print("  👤 Nome: Super Administrador")
        print("  📧 Email: superadmin@sistema.com")
        print("  🔑 Senha: super123")
        print("  🎯 Tipo: super_admin")
        
        print("\n🚀 Acesso:")
        print("  • Login: http://localhost:5000/super-admin")
        print("  • Dashboard: http://localhost:5000/super-admin/dashboard")
        
        return True

if __name__ == "__main__":
    criar_super_admin()