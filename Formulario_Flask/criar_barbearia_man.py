from app import app, db, Barbearia, Usuario, UsuarioBarbearia, Servico
from werkzeug.security import generate_password_hash
from datetime import datetime

def criar_barbearia_man():
    """Cria a Barbearia Man com dados completos"""
    
    with app.app_context():
        print("🚀 Criando Barbearia Man...")
        
        # 1. Verificar se já existe
        barbearia_existente = Barbearia.query.filter_by(slug='man').first()
        if barbearia_existente:
            print("⚠️ Barbearia Man já existe!")
            return
        
        # 2. Criar a barbearia
        barbearia_man = Barbearia(
            nome='Barbearia Man',
            slug='man',
            cnpj='12.345.678/0001-99',
            telefone='(11) 98765-4321',
            endereco='Rua dos Homens, 123 - Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01234-567',
            ativa=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(barbearia_man)
        db.session.commit()
        print(f"✅ Barbearia criada com ID: {barbearia_man.id}")
        
        # 3. Criar admin da barbearia
        admin_man = Usuario(
            nome='Administrador Man',
            email='admin@barbeariaman.com',
            senha=generate_password_hash('admin123'),
            telefone='(11) 98765-4321',
            tipo_conta='usuario',
            ativo=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(admin_man)
        db.session.commit()
        print(f"✅ Admin criado com ID: {admin_man.id}")
        
        # 4. Associar admin à barbearia
        vinculo_admin = UsuarioBarbearia(
            usuario_id=admin_man.id,
            barbearia_id=barbearia_man.id,
            role='admin',
            ativo=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(vinculo_admin)
        db.session.commit()
        print("✅ Admin vinculado à barbearia")
        
        # 5. Criar barbeiro
        barbeiro_man = Usuario(
            nome='João Barbeiro',
            email='joao@barbeariaman.com',
            senha=generate_password_hash('barbeiro123'),
            telefone='(11) 91234-5678',
            tipo_conta='usuario',
            ativo=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(barbeiro_man)
        db.session.commit()
        print(f"✅ Barbeiro criado com ID: {barbeiro_man.id}")
        
        # 6. Associar barbeiro à barbearia
        vinculo_barbeiro = UsuarioBarbearia(
            usuario_id=barbeiro_man.id,
            barbearia_id=barbearia_man.id,
            role='barbeiro',
            ativo=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(vinculo_barbeiro)
        db.session.commit()
        print("✅ Barbeiro vinculado à barbearia")
        
        # 7. Criar cliente de exemplo
        cliente_man = Usuario(
            nome='Carlos Cliente',
            email='carlos@email.com',
            senha=generate_password_hash('cliente123'),
            telefone='(11) 95555-1234',
            tipo_conta='usuario',
            ativo=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(cliente_man)
        db.session.commit()
        print(f"✅ Cliente criado com ID: {cliente_man.id}")
        
        # 8. Associar cliente à barbearia
        vinculo_cliente = UsuarioBarbearia(
            usuario_id=cliente_man.id,
            barbearia_id=barbearia_man.id,
            role='cliente',
            ativo=True,
            data_criacao=datetime.now()
        )
        
        db.session.add(vinculo_cliente)
        db.session.commit()
        print("✅ Cliente vinculado à barbearia")
        
        # 9. Criar serviços da Barbearia Man
        servicos_man = [
            {
                'nome': 'Corte Masculino Clássico',
                'descricao': 'Corte tradicional masculino com acabamento impecável',
                'preco': 25.00,
                'duracao': 30
            },
            {
                'nome': 'Barba + Bigode',
                'descricao': 'Aparar barba e bigode com navalha e acabamento',
                'preco': 20.00,
                'duracao': 25
            },
            {
                'nome': 'Corte + Barba Completo',
                'descricao': 'Pacote completo: corte de cabelo + barba + bigode',
                'preco': 40.00,
                'duracao': 50
            },
            {
                'nome': 'Corte Degradê',
                'descricao': 'Corte moderno com degradê nas laterais',
                'preco': 30.00,
                'duracao': 35
            },
            {
                'nome': 'Sobrancelha Masculina',
                'descricao': 'Design e limpeza de sobrancelhas masculinas',
                'preco': 15.00,
                'duracao': 15
            },
            {
                'nome': 'Tratamento Capilar',
                'descricao': 'Hidratação e tratamento para cabelo masculino',
                'preco': 35.00,
                'duracao': 40
            }
        ]
        
        for servico_data in servicos_man:
            servico = Servico(
                nome=servico_data['nome'],
                descricao=servico_data['descricao'],
                preco=servico_data['preco'],
                duracao=servico_data['duracao'],
                barbearia_id=barbearia_man.id,
                ativo=True,
                data_criacao=datetime.now()
            )
            db.session.add(servico)
        
        db.session.commit()
        print(f"✅ {len(servicos_man)} serviços criados")
        
        print("\n🎉 BARBEARIA MAN CRIADA COM SUCESSO!")
        print("\n📋 RESUMO:")
        print(f"🏪 Barbearia: {barbearia_man.nome} (slug: {barbearia_man.slug})")
        print(f"👨‍💼 Admin: {admin_man.email} / admin123")
        print(f"✂️ Barbeiro: {barbeiro_man.email} / barbeiro123") 
        print(f"👤 Cliente: {cliente_man.email} / cliente123")
        print(f"🔧 Serviços: {len(servicos_man)} disponíveis")
        print(f"\n🌐 Acesso: http://127.0.0.1:5000/?b=man")

if __name__ == '__main__':
    criar_barbearia_man()