#!/usr/bin/env python3
"""
Script para criar usuários Admin e Barbeiro para barbearias
Uso: python criar_usuarios.py
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
    print("Certifique-se de estar no diretório correto e que o app.py existe")
    sys.exit(1)

def listar_barbearias():
    """Lista todas as barbearias disponíveis"""
    print("\n🏪 Barbearias disponíveis:")
    print("-" * 50)
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    
    if not barbearias:
        print("❌ Nenhuma barbearia encontrada")
        return []
    
    for i, barbearia in enumerate(barbearias, 1):
        print(f"{i}. {barbearia.nome} (slug: {barbearia.slug})")
    
    return barbearias

def criar_usuario(nome, email, senha, tipo_conta, barbearia_id, role):
    """Cria um usuário e seu vínculo com a barbearia"""
    
    # Verificar se email já existe
    if Usuario.query.filter_by(email=email).first():
        print(f"❌ Email {email} já está em uso!")
        return False
    
    try:
        # Criar usuário
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            tipo_conta=tipo_conta,
            ativo=True
        )
        db.session.add(usuario)
        db.session.commit()
        
        # Criar vínculo com barbearia
        vinculo = UsuarioBarbearia(
            usuario_id=usuario.id,
            barbearia_id=barbearia_id,
            role=role,
            ativo=True
        )
        db.session.add(vinculo)
        db.session.commit()
        
        print(f"✅ Usuário {nome} criado com sucesso!")
        print(f"   Email: {email}")
        print(f"   Tipo: {tipo_conta}")
        print(f"   Role: {role}")
        print(f"   Barbearia ID: {barbearia_id}")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar usuário: {e}")
        return False

def menu_principal():
    """Menu principal do script"""
    print("\n" + "="*60)
    print("🔧 CRIADOR DE USUÁRIOS PARA BARBEARIAS")
    print("="*60)
    
    while True:
        print("\nOpções:")
        print("1. 👨‍💼 Criar Admin para barbearia")
        print("2. ✂️  Criar Barbeiro para barbearia")
        print("3. 📋 Listar usuários existentes")
        print("4. 🏪 Listar barbearias")
        print("5. ❌ Sair")
        
        opcao = input("\nEscolha uma opção (1-5): ").strip()
        
        if opcao == "1":
            criar_admin()
        elif opcao == "2":
            criar_barbeiro()
        elif opcao == "3":
            listar_usuarios()
        elif opcao == "4":
            listar_barbearias()
        elif opcao == "5":
            print("👋 Saindo...")
            break
        else:
            print("❌ Opção inválida!")

def criar_admin():
    """Cria um usuário admin para uma barbearia"""
    print("\n🔧 CRIAR ADMIN")
    print("-" * 30)
    
    barbearias = listar_barbearias()
    if not barbearias:
        return
    
    try:
        escolha = int(input("\nEscolha o número da barbearia: ")) - 1
        if escolha < 0 or escolha >= len(barbearias):
            print("❌ Escolha inválida!")
            return
        
        barbearia = barbearias[escolha]
        print(f"\n📍 Selecionada: {barbearia.nome}")
        
        nome = input("Nome do admin: ").strip()
        if not nome:
            print("❌ Nome é obrigatório!")
            return
        
        email = input("Email do admin: ").strip()
        if not email or "@" not in email:
            print("❌ Email inválido!")
            return
        
        senha = input("Senha do admin: ").strip()
        if len(senha) < 6:
            print("❌ Senha deve ter pelo menos 6 caracteres!")
            return
        
        criar_usuario(nome, email, senha, "admin_barbearia", barbearia.id, "admin")
        
    except (ValueError, IndexError):
        print("❌ Entrada inválida!")

def criar_barbeiro():
    """Cria um usuário barbeiro para uma barbearia"""
    print("\n✂️  CRIAR BARBEIRO")
    print("-" * 30)
    
    barbearias = listar_barbearias()
    if not barbearias:
        return
    
    try:
        escolha = int(input("\nEscolha o número da barbearia: ")) - 1
        if escolha < 0 or escolha >= len(barbearias):
            print("❌ Escolha inválida!")
            return
        
        barbearia = barbearias[escolha]
        print(f"\n📍 Selecionada: {barbearia.nome}")
        
        nome = input("Nome do barbeiro: ").strip()
        if not nome:
            print("❌ Nome é obrigatório!")
            return
        
        email = input("Email do barbeiro: ").strip()
        if not email or "@" not in email:
            print("❌ Email inválido!")
            return
        
        senha = input("Senha do barbeiro: ").strip()
        if len(senha) < 6:
            print("❌ Senha deve ter pelo menos 6 caracteres!")
            return
        
        criar_usuario(nome, email, senha, "barbeiro", barbearia.id, "barbeiro")
        
    except (ValueError, IndexError):
        print("❌ Entrada inválida!")

def listar_usuarios():
    """Lista todos os usuários e seus vínculos"""
    print("\n👥 USUÁRIOS CADASTRADOS")
    print("-" * 50)
    
    usuarios = Usuario.query.all()
    
    if not usuarios:
        print("❌ Nenhum usuário encontrado")
        return
    
    for usuario in usuarios:
        print(f"\n👤 {usuario.nome}")
        print(f"   📧 Email: {usuario.email}")
        print(f"   🔧 Tipo: {usuario.tipo_conta}")
        print(f"   ✅ Ativo: {'Sim' if usuario.ativo else 'Não'}")
        
        # Listar vínculos com barbearias
        vinculos = UsuarioBarbearia.query.filter_by(usuario_id=usuario.id, ativo=True).all()
        if vinculos:
            print(f"   🏪 Barbearias:")
            for vinculo in vinculos:
                barbearia = Barbearia.query.get(vinculo.barbearia_id)
                if barbearia:
                    print(f"      - {barbearia.nome} ({vinculo.role})")

def main():
    """Função principal"""
    try:
        with app.app_context():
            menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido pelo usuário. Saindo...")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()