"""
Script para criar uma segunda barbearia e testar o isolamento multi-tenant
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

# Redefinir modelos para o script
class Barbearia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    configuracoes = db.Column(db.Text, default='{}')
    
    def set_configuracoes(self, config_dict):
        self.configuracoes = json.dumps(config_dict)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    tipo_conta = db.Column(db.String(20), nullable=False, default='cliente')

class UsuarioBarbearia(db.Model):
    __tablename__ = 'usuario_barbearia'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cliente')
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_vinculo = db.Column(db.DateTime, default=db.func.current_timestamp())

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    duracao = db.Column(db.Integer, default=30)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    ordem_exibicao = db.Column(db.Integer, default=0)

def criar_segunda_barbearia():
    """Cria uma segunda barbearia para testar isolamento"""
    print("🔄 Criando segunda barbearia para teste de isolamento...")
    
    with app.app_context():
        # Criar segunda barbearia
        barbearia_teste = Barbearia(
            nome="Barber Shop Elite",
            slug="elite",
            cnpj="98.765.432/0001-10",
            telefone="(11) 88888-8888",
            endereco="Av. Elite, 456 - Bairro Nobre",
            ativa=True
        )
        
        # Configurações específicas da barbearia elite
        config_elite = {
            "horario_funcionamento": {
                "segunda": {"inicio": "10:00", "fim": "20:00"},
                "terca": {"inicio": "10:00", "fim": "20:00"},
                "quarta": {"inicio": "10:00", "fim": "20:00"},
                "quinta": {"inicio": "10:00", "fim": "20:00"},
                "sexta": {"inicio": "10:00", "fim": "22:00"},
                "sabado": {"inicio": "08:00", "fim": "18:00"},
                "domingo": {"inicio": "10:00", "fim": "16:00"}
            },
            "politica_cancelamento": 12,  # horas
            "intervalo_agendamento": 45,  # minutos
            "antecedencia_minima": 1      # horas
        }
        barbearia_teste.set_configuracoes(config_elite)
        
        db.session.add(barbearia_teste)
        db.session.commit()
        print("✅ Barber Shop Elite criada!")
        
        # Criar admin da barbearia elite
        admin_elite = Usuario(
            nome="Carlos Elite",
            email="admin@elite.com",
            senha=generate_password_hash("elite123"),
            telefone="(11) 88888-8888",
            tipo_conta="admin_barbearia",
            ativo=True
        )
        db.session.add(admin_elite)
        db.session.commit()
        
        # Vincular admin à barbearia elite
        vinculo_admin = UsuarioBarbearia(
            usuario_id=admin_elite.id,
            barbearia_id=barbearia_teste.id,
            role="admin",
            ativo=True
        )
        db.session.add(vinculo_admin)
        
        # Criar barbeiro da elite
        barbeiro_elite = Usuario(
            nome="Rafael Premium",
            email="rafael@elite.com",
            senha=generate_password_hash("barbeiro123"),
            telefone="(11) 88888-7777",
            tipo_conta="barbeiro",
            ativo=True
        )
        db.session.add(barbeiro_elite)
        db.session.commit()
        
        # Vincular barbeiro à barbearia elite
        vinculo_barbeiro = UsuarioBarbearia(
            usuario_id=barbeiro_elite.id,
            barbearia_id=barbearia_teste.id,
            role="barbeiro",
            ativo=True
        )
        db.session.add(vinculo_barbeiro)
        
        # Criar cliente da elite
        cliente_elite = Usuario(
            nome="Ana Premium",
            email="ana@elite.com",
            senha=generate_password_hash("cliente123"),
            telefone="(11) 88888-6666",
            tipo_conta="cliente",
            ativo=True
        )
        db.session.add(cliente_elite)
        db.session.commit()
        
        # Vincular cliente à barbearia elite
        vinculo_cliente = UsuarioBarbearia(
            usuario_id=cliente_elite.id,
            barbearia_id=barbearia_teste.id,
            role="cliente",
            ativo=True
        )
        db.session.add(vinculo_cliente)
        
        # Criar serviços premium da elite
        servicos_elite = [
            {
                "nome": "Corte Premium VIP",
                "preco": 80.00,
                "duracao": 45,
                "ordem": 1
            },
            {
                "nome": "Barba Premium",
                "preco": 40.00,
                "duracao": 30,
                "ordem": 2
            },
            {
                "nome": "Corte + Barba Elite",
                "preco": 110.00,
                "duracao": 60,
                "ordem": 3
            },
            {
                "nome": "Tratamento Capilar",
                "preco": 150.00,
                "duracao": 90,
                "ordem": 4
            },
            {
                "nome": "Design de Sobrancelhas",
                "preco": 30.00,
                "duracao": 20,
                "ordem": 5
            }
        ]
        
        for servico_data in servicos_elite:
            servico = Servico(
                barbearia_id=barbearia_teste.id,
                nome=servico_data["nome"],
                preco=servico_data["preco"],
                duracao=servico_data["duracao"],
                ordem_exibicao=servico_data["ordem"],
                ativo=True
            )
            db.session.add(servico)
        
        db.session.commit()
        print("✅ Usuários e serviços premium criados!")
        
        print("\n🎉 Segunda barbearia criada com sucesso!")
        print("\n📋 Dados da Barber Shop Elite:")
        print("  🏢 Barbearia: Barber Shop Elite (slug: elite)")
        print("  👤 Admin: admin@elite.com / elite123")
        print("  ✂️  Barbeiro: rafael@elite.com / barbeiro123")
        print("  👥 Cliente: ana@elite.com / cliente123")
        print("  💼 5 serviços premium")
        
        print("\n🧪 Para testar o isolamento:")
        print("  • Barbearia Principal: http://localhost:5000")
        print("  • Barber Shop Elite: http://localhost:5000?b=elite")
        
        return True

if __name__ == "__main__":
    criar_segunda_barbearia()