#!/usr/bin/env python3
"""
Script avançado para criação em lote de usuários
Uso: python criar_usuarios_lote.py
"""

import sys
import os
from werkzeug.security import generate_password_hash

# Adicionar o diretório atual ao path para importar app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db, Usuario, Barbearia, UsuarioBarbearia
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    sys.exit(1)

def criar_usuarios_padrao():
    """Cria usuários admin e barbeiro para todas as barbearias"""
    print("\n🚀 CRIANDO USUÁRIOS PADRÃO PARA TODAS AS BARBEARIAS")
    print("="*60)
    
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    
    if not barbearias:
        print("❌ Nenhuma barbearia encontrada!")
        return
    
    for barbearia in barbearias:
        print(f"\n🏪 Processando: {barbearia.nome}")
        print("-" * 40)
        
        # Criar admin
        admin_email = f"admin@{barbearia.slug}.com"
        admin_nome = f"Admin {barbearia.nome}"
        
        if not Usuario.query.filter_by(email=admin_email).first():
            try:
                # Criar usuário admin
                admin = Usuario(
                    nome=admin_nome,
                    email=admin_email,
                    senha=generate_password_hash("admin123"),
                    tipo_conta="admin_barbearia",
                    ativo=True
                )
                db.session.add(admin)
                db.session.commit()
                
                # Criar vínculo
                vinculo_admin = UsuarioBarbearia(
                    usuario_id=admin.id,
                    barbearia_id=barbearia.id,
                    role="admin",
                    ativo=True
                )
                db.session.add(vinculo_admin)
                db.session.commit()
                
                print(f"✅ Admin criado: {admin_email} / admin123")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao criar admin: {e}")
        else:
            print(f"⚠️  Admin já existe: {admin_email}")
        
        # Criar barbeiro
        barbeiro_email = f"barbeiro@{barbearia.slug}.com"
        barbeiro_nome = f"Barbeiro {barbearia.nome}"
        
        if not Usuario.query.filter_by(email=barbeiro_email).first():
            try:
                # Criar usuário barbeiro
                barbeiro = Usuario(
                    nome=barbeiro_nome,
                    email=barbeiro_email,
                    senha=generate_password_hash("barbeiro123"),
                    tipo_conta="barbeiro",
                    ativo=True
                )
                db.session.add(barbeiro)
                db.session.commit()
                
                # Criar vínculo
                vinculo_barbeiro = UsuarioBarbearia(
                    usuario_id=barbeiro.id,
                    barbearia_id=barbearia.id,
                    role="barbeiro",
                    ativo=True
                )
                db.session.add(vinculo_barbeiro)
                db.session.commit()
                
                print(f"✅ Barbeiro criado: {barbeiro_email} / barbeiro123")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao criar barbeiro: {e}")
        else:
            print(f"⚠️  Barbeiro já existe: {barbeiro_email}")

def listar_credenciais():
    """Lista todas as credenciais criadas"""
    print("\n📋 CREDENCIAIS DE ACESSO")
    print("="*60)
    
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    
    for barbearia in barbearias:
        print(f"\n🏪 {barbearia.nome.upper()}")
        print(f"🌐 URL: http://localhost:5000/{barbearia.slug}")
        print("-" * 40)
        
        # Buscar admin
        admin_email = f"admin@{barbearia.slug}.com"
        admin = Usuario.query.filter_by(email=admin_email).first()
        if admin:
            print(f"👨‍💼 ADMIN:")
            print(f"   📧 Email: {admin_email}")
            print(f"   🔑 Senha: admin123")
            print(f"   🔗 Login: http://localhost:5000/{barbearia.slug}/login")
        
        # Buscar barbeiro
        barbeiro_email = f"barbeiro@{barbearia.slug}.com"
        barbeiro = Usuario.query.filter_by(email=barbeiro_email).first()
        if barbeiro:
            print(f"✂️  BARBEIRO:")
            print(f"   📧 Email: {barbeiro_email}")
            print(f"   🔑 Senha: barbeiro123")
            print(f"   🔗 Login: http://localhost:5000/{barbearia.slug}/login")

def resetar_senhas():
    """Reseta senhas para padrões conhecidos"""
    print("\n🔄 RESETAR SENHAS PADRÃO")
    print("="*40)
    
    confirm = input("⚠️  Tem certeza? Isso resetará todas as senhas padrão (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Operação cancelada")
        return
    
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    
    for barbearia in barbearias:
        # Reset admin
        admin_email = f"admin@{barbearia.slug}.com"
        admin = Usuario.query.filter_by(email=admin_email).first()
        if admin:
            admin.senha = generate_password_hash("admin123")
            db.session.commit()
            print(f"✅ Senha do admin resetada: {admin_email}")
        
        # Reset barbeiro
        barbeiro_email = f"barbeiro@{barbearia.slug}.com"
        barbeiro = Usuario.query.filter_by(email=barbeiro_email).first()
        if barbeiro:
            barbeiro.senha = generate_password_hash("barbeiro123")
            db.session.commit()
            print(f"✅ Senha do barbeiro resetada: {barbeiro_email}")

def menu():
    """Menu principal"""
    print("\n" + "="*60)
    print("🔧 GERENCIADOR DE USUÁRIOS EM LOTE")
    print("="*60)
    
    while True:
        print("\nOpções:")
        print("1. 🚀 Criar usuários padrão para todas as barbearias")
        print("2. 📋 Listar todas as credenciais")
        print("3. 🔄 Resetar senhas padrão")
        print("4. ❌ Sair")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == "1":
            criar_usuarios_padrao()
        elif opcao == "2":
            listar_credenciais()
        elif opcao == "3":
            resetar_senhas()
        elif opcao == "4":
            print("👋 Saindo...")
            break
        else:
            print("❌ Opção inválida!")

def main():
    """Função principal"""
    try:
        with app.app_context():
            menu()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido pelo usuário. Saindo...")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()