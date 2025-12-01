"""
Script para resetar senhas de admin e superadmin
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório ao path
BASE_DIR = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE_DIR)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Configurar Flask
DB_PATH = os.path.join(BASE_DIR, 'meubanco.db')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos
class Barbearia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    ativo = db.Column(db.Boolean, default=True)
    tipo_conta = db.Column(db.String(20), default='cliente')
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())

class UsuarioBarbearia(db.Model):
    __tablename__ = 'usuario_barbearia'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'))
    role = db.Column(db.String(20), default='cliente')
    ativo = db.Column(db.Boolean, default=True)

with app.app_context():
    print("🔍 Verificando usuários...\n")
    
    # Verificar super admin
    super_admin = Usuario.query.filter_by(tipo_conta='super_admin').first()
    if super_admin:
        print(f"✅ Super Admin encontrado: {super_admin.email}")
        super_admin.senha = generate_password_hash("super123")
        super_admin.ativo = True
        print("   🔄 Senha resetada para: super123")
    else:
        print("❌ Super Admin não encontrado, criando...")
        super_admin = Usuario(
            nome="Super Administrador",
            email="superadmin@sistema.com",
            senha=generate_password_hash("super123"),
            telefone="(11) 00000-0000",
            tipo_conta="super_admin",
            ativo=True
        )
        db.session.add(super_admin)
        print("   ✅ Super Admin criado")
    
    print()
    
    # Verificar admin Principal
    admin_principal = Usuario.query.filter_by(email='admin@principal.com').first()
    if admin_principal:
        print(f"✅ Admin Principal encontrado: {admin_principal.email}")
        admin_principal.senha = generate_password_hash("admin123")
        admin_principal.ativo = True
        print("   🔄 Senha resetada para: admin123")
    else:
        print("❌ Admin Principal não encontrado, criando...")
        admin_principal = Usuario(
            nome="Admin Principal",
            email="admin@principal.com",
            senha=generate_password_hash("admin123"),
            telefone="(11) 99999-0001",
            tipo_conta="admin",
            ativo=True
        )
        db.session.add(admin_principal)
        db.session.flush()  # Para obter o ID
        
        # Criar relacionamento com barbearia
        relacao = UsuarioBarbearia(
            usuario_id=admin_principal.id,
            barbearia_id=1,
            role='admin',
            ativo=True
        )
        db.session.add(relacao)
        print("   ✅ Admin Principal criado e vinculado à barbearia")
    
    db.session.commit()
    
    print("\n" + "="*60)
    print("✅ SENHAS RESETADAS COM SUCESSO!\n")
    print("📋 CREDENCIAIS ATUALIZADAS:")
    print("\n🔷 Super Admin (acesso global):")
    print("   📧 Email: superadmin@sistema.com")
    print("   🔑 Senha: super123")
    print("   🔗 URL: http://192.168.0.31:5000/super_admin/login")
    print("\n🔷 Admin Barbearia Principal:")
    print("   📧 Email: admin@principal.com")
    print("   🔑 Senha: admin123")
    print("   🔗 URL: http://192.168.0.31:5000/principal/login")
    print("="*60)
