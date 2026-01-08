#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Unificado de Inicialização do Sistema

Este script substitui:
- criar_barbearia_man.py
- criar_segunda_barbearia.py
- criar_usuarios.py
- criar_usuarios_lote.py
- setup.py

Uso:
    python inicializar_barbearias.py              # Cria barbearias básicas
    python inicializar_barbearias.py --completo   # Cria barbearias + super admin + usuários exemplo
    python inicializar_barbearias.py --verificar  # Apenas verifica o banco
"""

import sys
from app import app, db, Barbearia, Servico, Usuario, UsuarioBarbearia
from werkzeug.security import generate_password_hash

def verificar_banco():
    """Verifica o estado atual do banco de dados"""
    with app.app_context():
        print("\n" + "="*60)
        print("📊 VERIFICAÇÃO DO BANCO DE DADOS")
        print("="*60)
        
        barbearias = Barbearia.query.all()
        usuarios = Usuario.query.all()
        servicos = Servico.query.all()
        
        print(f"\n✅ Barbearias: {len(barbearias)}")
        for b in barbearias:
            servicos_count = Servico.query.filter_by(barbearia_id=b.id).count()
            usuarios_count = UsuarioBarbearia.query.filter_by(barbearia_id=b.id).count()
            print(f"   - {b.nome} (/{b.slug}): {servicos_count} serviços, {usuarios_count} usuários")
        
        print(f"\n✅ Usuários totais: {len(usuarios)}")
        super_admins = Usuario.query.filter_by(tipo_conta='super_admin').count()
        print(f"   - Super Admins: {super_admins}")
        
        print(f"\n✅ Serviços totais: {len(servicos)}")
        print("="*60 + "\n")

def criar_super_admin():
    """Cria o super administrador do sistema"""
    with app.app_context():
        email = 'superadmin@sistema.com'
        super_admin = Usuario.query.filter_by(email=email).first()
        
        if super_admin:
            print(f"   ⚠️  Super Admin já existe: {email}")
            return
        
        super_admin = Usuario(
            nome='Super Administrador',
            email=email,
            senha=generate_password_hash('admin123'),
            tipo_conta='super_admin',
            ativo=True
        )
        
        db.session.add(super_admin)
        db.session.commit()
        
        print(f"   ✅ Super Admin criado: {email} / admin123")

def criar_usuarios_exemplo(barbearia_id, barbearia_nome):
    """Cria usuários de exemplo para uma barbearia"""
    with app.app_context():
        slug = Barbearia.query.get(barbearia_id).slug
        
        usuarios_exemplo = [
            {
                'nome': f'Admin {barbearia_nome}',
                'email': f'admin@{slug}.com',
                'senha': 'admin123',
                'tipo_conta': 'admin_barbearia',
                'role': 'admin'
            },
            {
                'nome': f'Barbeiro {barbearia_nome}',
                'email': f'barbeiro@{slug}.com',
                'senha': 'barbeiro123',
                'tipo_conta': 'barbeiro',
                'role': 'barbeiro'
            },
            {
                'nome': f'Cliente {barbearia_nome}',
                'email': f'cliente@{slug}.com',
                'senha': 'cliente123',
                'tipo_conta': 'cliente',
                'role': 'cliente'
            }
        ]
        
        for user_data in usuarios_exemplo:
            usuario_existente = Usuario.query.filter_by(email=user_data['email']).first()
            
            if usuario_existente:
                continue
            
            novo_usuario = Usuario(
                nome=user_data['nome'],
                email=user_data['email'],
                senha=generate_password_hash(user_data['senha']),
                tipo_conta=user_data['tipo_conta'],
                ativo=True
            )
            
            db.session.add(novo_usuario)
            db.session.flush()
            
            vinculo = UsuarioBarbearia(
                usuario_id=novo_usuario.id,
                barbearia_id=barbearia_id,
                role=user_data['role'],
                ativo=True
            )
            
            db.session.add(vinculo)
            print(f"      - {user_data['nome']}: {user_data['email']} / {user_data['senha']}")
        
        db.session.commit()

def criar_barbearias_iniciais():
    """Cria as 3 barbearias básicas do sistema"""
    
    with app.app_context():
        # Verificar se já existem barbearias
        barbearias_existentes = Barbearia.query.all()
        
        if barbearias_existentes:
            print(f"✅ Já existem {len(barbearias_existentes)} barbearia(s) cadastrada(s).")
            print("\nBarbearias existentes:")
            for b in barbearias_existentes:
                print(f"  - {b.nome} (slug: {b.slug})")
            return
        
        print("🔄 Criando barbearias iniciais...\n")
        
        # Criar Barbearia Principal
        barbearia_principal = Barbearia(
            nome='Barbearia Principal',
            slug='principal',
            cnpj='11.111.111/0001-11',
            telefone='(11) 1111-1111',
            endereco='Rua Principal, 123',
            ativa=True
        )
        
        # Criar Barbearia Elite
        barbearia_elite = Barbearia(
            nome='Barbearia Elite',
            slug='elite',
            cnpj='22.222.222/0001-22',
            telefone='(22) 2222-2222',
            endereco='Avenida Elite, 456',
            ativa=True
        )
        
        # Criar Barbearia Man
        barbearia_man = Barbearia(
            nome='Barbearia Man',
            slug='man',
            cnpj='33.333.333/0001-33',
            telefone='(33) 3333-3333',
            endereco='Rua dos Homens, 789',
            ativa=True
        )
        
        db.session.add(barbearia_principal)
        db.session.add(barbearia_elite)
        db.session.add(barbearia_man)
        db.session.commit()
        
        print("✅ Barbearias criadas com sucesso!")
        print(f"   - {barbearia_principal.nome} (slug: {barbearia_principal.slug})")
        print(f"   - {barbearia_elite.nome} (slug: {barbearia_elite.slug})")
        print(f"   - {barbearia_man.nome} (slug: {barbearia_man.slug})")
        
        # Criar serviços básicos para cada barbearia
        print("\n🔄 Criando serviços básicos...\n")
        
        barbearias = [barbearia_principal, barbearia_elite, barbearia_man]
        
        for barbearia in barbearias:
            print(f"   Criando serviços para {barbearia.nome}...")
            
            servicos = [
                Servico(
                    barbearia_id=barbearia.id,
                    nome='Corte Simples',
                    preco=30.0,
                    duracao=30,
                    ativo=True,
                    ordem_exibicao=1
                ),
                Servico(
                    barbearia_id=barbearia.id,
                    nome='Corte + Barba',
                    preco=50.0,
                    duracao=45,
                    ativo=True,
                    ordem_exibicao=2
                ),
                Servico(
                    barbearia_id=barbearia.id,
                    nome='Barba',
                    preco=25.0,
                    duracao=20,
                    ativo=True,
                    ordem_exibicao=3
                ),
                Servico(
                    barbearia_id=barbearia.id,
                    nome='Corte + Barba + Sobrancelha',
                    preco=65.0,
                    duracao=60,
                    ativo=True,
                    ordem_exibicao=4
                )
            ]
            
            for servico in servicos:
                db.session.add(servico)
        
        db.session.commit()
        
        print("\n✅ Serviços básicos criados para todas as barbearias!")
        
        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO DA INICIALIZAÇÃO")
        print("="*60)
        
        barbearias_final = Barbearia.query.all()
        for b in barbearias_final:
            servicos_count = Servico.query.filter_by(barbearia_id=b.id, ativo=True).count()
            print(f"\n🏪 {b.nome}")
            print(f"   Slug: {b.slug}")
            print(f"   Serviços: {servicos_count}")
            print(f"   URL: http://localhost:5000/{b.slug}")
        
        print("\n✅ Sistema pronto para uso!")
        print("\n💡 Próximos passos:")
        print("   1. Execute: python app.py")
        print("   2. Acesse: http://localhost:5000/")
        print("   3. Clique em uma barbearia para acessar\n")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 INICIALIZADOR DO SISTEMA DE BARBEARIAS")
    print("="*60 + "\n")
    
    # Verificar argumentos
    if '--verificar' in sys.argv:
        verificar_banco()
        exit(0)
    
    modo_completo = '--completo' in sys.argv
    
    try:
        # Criar barbearias
        criar_barbearias_iniciais()
        
        # Modo completo: criar super admin e usuários exemplo
        if modo_completo:
            print("\n🔧 Criando usuários do sistema...\n")
            criar_super_admin()
            
            print("\n👥 Criando usuários exemplo para cada barbearia...\n")
            barbearias = Barbearia.query.all()
            for b in barbearias:
                print(f"   {b.nome}:")
                criar_usuarios_exemplo(b.id, b.nome)
        
        # Verificação final
        print("\n" + "="*60)
        print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        
        if modo_completo:
            print("\n🔑 CREDENCIAIS DE ACESSO:")
            print("   Super Admin: superadmin@sistema.com / admin123")
            print("   Admin Principal: admin@principal.com / admin123")
            print("   Admin Elite: admin@elite.com / admin123")
            print("   Admin Man: admin@man.com / admin123")
        
        print("\n🌐 URLS DE ACESSO:")
        print("   Página Inicial: http://localhost:5000/")
        print("   Super Admin: http://localhost:5000/super_admin/login")
        barbearias = Barbearia.query.all()
        for b in barbearias:
            print(f"   {b.nome}: http://localhost:5000/{b.slug}")
        
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Execute: python app.py")
        print("   2. Acesse: http://localhost:5000/")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao inicializar: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
