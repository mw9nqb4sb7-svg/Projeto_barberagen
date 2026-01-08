from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sys
import json
import uuid
from pathlib import Path
from jinja2 import ChoiceLoader, FileSystemLoader
import smtplib
from email.message import EmailMessage
from datetime import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from whitenoise import WhiteNoise

# Importar módulo de segurança
from security import (
    sanitize_input, validate_email, validate_phone, validate_password_strength,
    check_rate_limit, record_login_attempt, require_login, get_client_ip, audit_log
)
# Legacy session-based login will be used

# Caminhos absolutos
BASE_DIR = str(Path(__file__).resolve().parent)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')        # templates padrão
CLIENTE_TEMPLATES_DIR = os.path.join(BASE_DIR, 'cliente')  # templates que você deixou fora da pasta templates
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_PATH = os.path.join(BASE_DIR, 'meubanco.db')

# Cria app com template_folder apontando para templates principal
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

# Configuração WhiteNoise para arquivos estáticos em produção
app.wsgi_app = WhiteNoise(app.wsgi_app, root=STATIC_DIR, prefix='static/')

# Segurança: SECRET_KEY forte
import secrets
app.secret_key = os.environ.get('FLASK_SECRET', secrets.token_hex(32))

# Proteção CSRF
csrf = CSRFProtect(app)

# Configurações de segurança da sessão
# Em desenvolvimento (sem HTTPS), desabilitar Secure
app.config['SESSION_COOKIE_SECURE'] = False  # Mudar para True apenas em produção com HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Previne acesso via JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Proteção CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

# Adiciona vários caminhos de busca de templates (templates/ e cliente/)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(TEMPLATES_DIR),
    FileSystemLoader(CLIENTE_TEMPLATES_DIR),
    app.jinja_loader
])

# Configuração do Banco de Dados com suporte a PostgreSQL (Railway)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração de upload de imagens - ajustada para Railway
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'logos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_FILE_SIZE', 5)) * 1024 * 1024  # MB max

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Criar pasta de logs se não existir
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

# Isentar rotas de API da proteção CSRF (somente JSON)
csrf.exempt('api_agendamentos_hoje')
csrf.exempt('api_agendamentos_todos')
csrf.exempt('api_reservas_cliente')
csrf.exempt('sincronizar_chamados_manual')  # Sincronização manual de chamados
# Removido CSRF exempt para admin_cancelar_agendamento - deve usar CSRF token

# Tratamento de erros CSRF
@app.errorhandler(400)
def handle_csrf_error(e):
    if 'CSRF' in str(e):
        flash('⚠️ Token de segurança inválido ou expirado. Por favor, tente novamente.', 'error')
        return redirect(request.referrer or url_for('index_login'))
    return e

# Headers de Segurança
@app.after_request
def set_security_headers(response):
    # Proteção contra clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Proteção XSS
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Content Security Policy
    # Content Security Policy: keep conservative defaults for production
    # Allow fonts and inline styles where necessary; restrict network connections to same origin
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "connect-src 'self'; "
        "img-src 'self' data:;"
    )
    # Desabilitar cache para páginas HTML (facilitar desenvolvimento)
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    # HSTS (apenas em produção com HTTPS)
    if not app.debug:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Adicionar pasta scripts ao sys.path para importar módulos de lá
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

# Importar sistema multi-tenant após db ser criado
from tenant import setup_tenant_context, require_tenant, require_admin, require_barbeiro, require_role, get_current_barbearia_id, get_current_barbearia, is_super_admin

def require_super_admin(f):
    """Decorator que exige permissão de super admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Debug
        print(f"[DEBUG] require_super_admin: Verificando acesso...")
        print(f"[DEBUG] Session: {dict(session)}")
        
        # Verificar se está logado
        if 'usuario_id' not in session:
            print(f"[DEBUG] Usuário não logado - redirecionando para login")
            flash('Você precisa fazer login como Super Admin.', 'error')
            return redirect(url_for('super_admin_login'))
        
        # Buscar usuário e verificar tipo
        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            print(f"[DEBUG] Usuário não encontrado no banco - ID: {session.get('usuario_id')}")
            session.clear()
            flash('Sessão inválida. Faça login novamente.', 'error')
            return redirect(url_for('super_admin_login'))
        
        print(f"[DEBUG] Usuário encontrado: {usuario.nome} - Tipo: {usuario.tipo_conta}")
        
        if usuario.tipo_conta != 'super_admin':
            print(f"[DEBUG] Acesso negado - tipo de conta: {usuario.tipo_conta}")
            flash('Acesso negado - apenas super administradores.', 'error')
            return redirect(url_for('admin_index'))
        
        print(f"[DEBUG] Acesso autorizado para super admin: {usuario.nome}")
        return f(*args, **kwargs)
    return decorated_function
    return decorated_function

# ---------- MODELOS ----------
class Barbearia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # para URLs amigáveis
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    logo = db.Column(db.String(200), nullable=True)  # caminho da logo
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # CSS personalizado único para cada barbearia
    custom_css = db.Column(db.Text, nullable=True)
    
    # Configurações específicas da barbearia (JSON)
    configuracoes = db.Column(db.Text, default='{}')
    
    # Personalização visual da home page
    hero_titulo = db.Column(db.Text, nullable=True)
    hero_subtitulo = db.Column(db.Text, nullable=True)
    slogan = db.Column(db.String(200), nullable=True)
    cor_primaria = db.Column(db.String(10), nullable=True)
    cor_secundaria = db.Column(db.String(10), nullable=True)
    cor_texto = db.Column(db.String(10), nullable=True)
    
    # Segurança de Faturamento
    senha_financeira = db.Column(db.String(200), nullable=True)  # Senha hashed para faturamento
    
    # Cards de serviços personalizáveis
    card1_icone = db.Column(db.String(10), nullable=True)
    card1_titulo = db.Column(db.String(100), nullable=True)
    card1_descricao = db.Column(db.Text, nullable=True)
    
    card2_icone = db.Column(db.String(10), nullable=True)
    card2_titulo = db.Column(db.String(100), nullable=True)
    card2_descricao = db.Column(db.Text, nullable=True)
    
    card3_icone = db.Column(db.String(10), nullable=True)
    card3_titulo = db.Column(db.String(100), nullable=True)
    card3_descricao = db.Column(db.Text, nullable=True)
    
    card4_icone = db.Column(db.String(10), nullable=True)
    card4_titulo = db.Column(db.String(100), nullable=True)
    card4_descricao = db.Column(db.Text, nullable=True)
    
    # Seção de estatísticas personalizáveis
    stat1_valor = db.Column(db.String(20), nullable=True)
    stat1_label = db.Column(db.String(100), nullable=True)
    
    stat2_valor = db.Column(db.String(20), nullable=True)
    stat2_label = db.Column(db.String(100), nullable=True)
    
    stat3_valor = db.Column(db.String(20), nullable=True)
    stat3_label = db.Column(db.String(100), nullable=True)
    
    stat4_valor = db.Column(db.String(20), nullable=True)
    stat4_label = db.Column(db.String(100), nullable=True)
    
    # Relacionamentos
    usuarios = db.relationship('UsuarioBarbearia', back_populates='barbearia', cascade="all, delete-orphan")
    servicos = db.relationship('Servico', backref='barbearia', lazy=True, cascade="all, delete-orphan")
    reservas = db.relationship('Reserva', backref='barbearia', lazy=True, cascade="all, delete-orphan")
    disponibilidades = db.relationship('DisponibilidadeSemanal', backref='barbearia', lazy=True, cascade="all, delete-orphan")
    
    def get_configuracoes(self):
        try:
            return json.loads(self.configuracoes)
        except:
            return {}
    
    def set_configuracoes(self, config_dict):
        self.configuracoes = json.dumps(config_dict)
    
    def __repr__(self):
        return f'<Barbearia {self.nome}>'

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    apelido = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=True)  # Para admins
    senha = db.Column(db.String(200), nullable=False)
    # Campo telefone do usuário
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Tipo geral do usuário no sistema
    tipo_conta = db.Column(db.String(20), nullable=False, default='cliente')  # admin_sistema, admin_barbearia, barbeiro, cliente
    
    # Relacionamentos
    barbearias = db.relationship('UsuarioBarbearia', back_populates='usuario', cascade="all, delete-orphan")
    
    def set_senha(self, senha_plana):
        self.senha = generate_password_hash(senha_plana)
        
    def __repr__(self):
        return f'<Usuario {self.nome}>'

class UsuarioBarbearia(db.Model):
    """Tabela de relacionamento Many-to-Many entre Usuario e Barbearia"""
    __tablename__ = 'usuario_barbearia'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    
    # Role específica do usuário nesta barbearia
    role = db.Column(db.String(20), nullable=False, default='cliente')  # admin, barbeiro, cliente
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_vinculo = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relacionamentos
    usuario = db.relationship('Usuario', back_populates='barbearias')
    barbearia = db.relationship('Barbearia', back_populates='usuarios')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'barbearia_id', name='unique_usuario_barbearia'),
    )
    
    def __repr__(self):
        return f'<UsuarioBarbearia {self.usuario.nome} - {self.barbearia.nome} ({self.role})>'


class RecuperacaoSenha(db.Model):
    __tablename__ = 'recuperacao_senha'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    expira_em = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)

    def gerar_token(self, horas_validade=1):
        import secrets
        from datetime import datetime, timedelta
        self.token = secrets.token_urlsafe(32)
        self.expira_em = datetime.utcnow() + timedelta(hours=horas_validade)

    def __repr__(self):
        return f'<RecuperacaoSenha usuario_id={self.usuario_id} token={self.token[:8]}...>'

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    duracao = db.Column(db.Integer, default=30)  # duração em minutos
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    ordem_exibicao = db.Column(db.Integer, default=0)
    reservas = db.relationship('Reserva', backref='servico', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Servico {self.nome} - {self.barbearia.nome}>'

class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)  # cliente que fez a reserva
    barbeiro_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)  # barbeiro responsável
    servico_id = db.Column(db.Integer, db.ForeignKey('servico.id'), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    hora_inicio = db.Column(db.String(5), nullable=False)
    hora_fim = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default='agendada')  # agendada, confirmada, cancelada, concluida
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relacionamentos
    cliente = db.relationship('Usuario', foreign_keys=[cliente_id], backref='reservas_cliente')
    barbeiro = db.relationship('Usuario', foreign_keys=[barbeiro_id], backref='reservas_barbeiro')
    
    def __repr__(self):
        return f'<Reserva {self.cliente.nome} - {self.servico.nome} - {self.data} {self.hora_inicio}>'

class Despesa(db.Model):
    """Controle de despesas da barbearia"""
    __tablename__ = 'despesa'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # aluguel, produtos, energia, agua, internet, salarios, outros
    valor = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='pendente')  # pendente, paga, atrasada
    recorrente = db.Column(db.Boolean, default=False)  # Se é uma despesa mensal fixa
    observacoes = db.Column(db.Text, nullable=True)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relacionamentos
    barbearia = db.relationship('Barbearia', backref='despesas')
    criador = db.relationship('Usuario', backref='despesas_criadas')
    
    def __repr__(self):
        return f'<Despesa {self.descricao} - R$ {self.valor}>'
    
    @property
    def esta_atrasada(self):
        """Verifica se a despesa está atrasada"""
        from datetime import date
        if self.status == 'pendente' and self.data_vencimento < date.today():
            return True
        return False

class PlanoMensal(db.Model):
    """Planos mensais oferecidos pelas barbearias"""
    __tablename__ = 'plano_mensal'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)  # Ex: "Plano Básico", "Plano Premium"
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    atendimentos_mes = db.Column(db.Integer, nullable=False)  # Quantidade de atendimentos inclusos
    beneficios = db.Column(db.Text, nullable=True)  # JSON com lista de benefícios
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relacionamento
    barbearia = db.relationship('Barbearia', backref='planos')
    assinaturas = db.relationship('AssinaturaPlano', back_populates='plano', cascade="all, delete-orphan")
    
    def get_beneficios(self):
        """Retorna lista de benefícios"""
        try:
            return json.loads(self.beneficios) if self.beneficios else []
        except:
            return []
    
    def set_beneficios(self, beneficios_list):
        """Define lista de benefícios"""
        self.beneficios = json.dumps(beneficios_list)
    
    def __repr__(self):
        return f'<PlanoMensal {self.nome} - R$ {self.preco}>'

class AssinaturaPlano(db.Model):
    """Assinaturas de clientes aos planos mensais"""
    __tablename__ = 'assinatura_plano'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    plano_id = db.Column(db.Integer, db.ForeignKey('plano_mensal.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    data_fim = db.Column(db.DateTime, nullable=True)  # Null = ativa
    status = db.Column(db.String(20), default='ativa')  # ativa, cancelada, expirada
    atendimentos_restantes = db.Column(db.Integer, nullable=False)
    data_renovacao = db.Column(db.DateTime, nullable=True)  # Data da próxima renovação
    
    # Relacionamentos
    plano = db.relationship('PlanoMensal', back_populates='assinaturas')
    cliente = db.relationship('Usuario', backref='assinaturas_planos')
    
    def __repr__(self):
        return f'<AssinaturaPlano {self.cliente.nome} - {self.plano.nome}>'

class DisponibilidadeSemanal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    barbeiro_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)  # null = disponibilidade geral
    data_inicio = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD (segunda-feira da semana)
    data_fim = db.Column(db.String(10), nullable=False)     # YYYY-MM-DD (domingo da semana)
    config_json = db.Column(db.Text, nullable=False, default='{}')
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento
    barbeiro = db.relationship('Usuario', foreign_keys=[barbeiro_id], backref='disponibilidades')
    
    def get_config(self):
        try:
            return json.loads(self.config_json)
        except:
            return {}
    
    def set_config(self, config_dict):
        self.config_json = json.dumps(config_dict)
    
    @staticmethod
    def get_ou_criar_semana(data_str, barbearia_id, barbeiro_id=None):
        """Obtém ou cria a configuração para a semana da data fornecida"""
        from datetime import datetime, timedelta
        
        data = datetime.strptime(data_str, '%Y-%m-%d')
        # Calcular início da semana (segunda-feira)
        dias_para_segunda = data.weekday()
        inicio_semana = data - timedelta(days=dias_para_segunda)
        fim_semana = inicio_semana + timedelta(days=6)
        
        data_inicio_str = inicio_semana.strftime('%Y-%m-%d')
        data_fim_str = fim_semana.strftime('%Y-%m-%d')
        
        # Buscar configuração existente
        config_semana = DisponibilidadeSemanal.query.filter_by(
            barbearia_id=barbearia_id,
            barbeiro_id=barbeiro_id,
            data_inicio=data_inicio_str,
            data_fim=data_fim_str
        ).first()
        
        if not config_semana:
            # Criar configuração padrão para a semana
            config_padrao = {
                'monday': {'ativo': True, 'horarios': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']},
                'tuesday': {'ativo': True, 'horarios': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']},
                'wednesday': {'ativo': True, 'horarios': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']},
                'thursday': {'ativo': True, 'horarios': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']},
                'friday': {'ativo': True, 'horarios': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']},
                'saturday': {'ativo': False, 'horarios': []},
                'sunday': {'ativo': False, 'horarios': []}
            }
            
            config_semana = DisponibilidadeSemanal(
                barbearia_id=barbearia_id,
                barbeiro_id=barbeiro_id,
                data_inicio=data_inicio_str,
                data_fim=data_fim_str,
                config_json=json.dumps(config_padrao)
            )
            db.session.add(config_semana)
            db.session.commit()
        
        return config_semana

# Manter classe antiga para compatibilidade
class Disponibilidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    config_json = db.Column(db.Text, nullable=False, default='{}')

class Chamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    numero_chamado = db.Column(db.String(50), unique=True, nullable=False)
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    aplicacao = db.Column(db.String(100), nullable=False)
    usuario_nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(20))
    assunto = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), nullable=False, default='media')
    
    status = db.Column(db.String(20), nullable=False, default='enviado')  # enviado, em_andamento, resolvido, fechado, cancelado
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    resposta_api = db.Column(db.Text)  # Resposta da API externa
    api_chamado_id = db.Column(db.String(100))  # ID retornado pela API externa
    
    # Relacionamentos
    barbearia = db.relationship('Barbearia', backref=db.backref('chamados', lazy=True))
    usuario = db.relationship('Usuario', backref=db.backref('chamados', lazy=True))

# ---------- UTIL ---------- 
def check_required_templates(required):
    available = set()
    try:
        available = set(app.jinja_env.list_templates())
    except Exception:
        # se loader falhar, tenta listar via os.walk
        for root, _, files in os.walk(TEMPLATES_DIR):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), TEMPLATES_DIR).replace('\\', '/')
                available.add(rel)
    missing = [t for t in required if t not in available]
    if missing:
        print("AVISO: alguns templates não foram encontrados:", file=sys.stderr)
        for m in missing:
            print("  -", m, file=sys.stderr)
        print("\nTemplates disponíveis (amostra):", file=sys.stderr)
        for i, a in enumerate(sorted(list(available))[:200], 1):
            print(f"  {i}. {a}", file=sys.stderr)
    return missing

# Lista mínima de templates usados pelo app (ajuste se adicionar outros)
REQUIRED_TEMPLATES = [
    'barbearias_lista.html',
    'barbearia_home.html',
    'usuario_dashboard.html',
    'cliente/login.html',
    'cliente/cadastro_cliente.html',
    'cliente/nova_reserva.html',
    'cliente/clientes.html',
    'cliente/servicos.html',
    'admin/dashboard.html',
    'admin/admin_agendamentos.html',
    'admin/disponibilidade.html',
    'admin/disponibilidade_semana.html',
    'admin/suporte.html',
    'admin/chamados.html'
]

# ---------- MIDDLEWARE ----------
@app.before_request
def before_request():
    """Middleware executado antes de cada request"""
    # Debug para sincronização
    if 'sincronizar' in request.path:
        print(f"\n🔍 [BEFORE_REQUEST] Path: {request.path}")
        print(f"🔍 [BEFORE_REQUEST] Endpoint: {request.endpoint}")
        print(f"🔍 [BEFORE_REQUEST] Method: {request.method}")
        print(f"🔍 [BEFORE_REQUEST] Session: {dict(session)}\n")
    
    # Excluir rotas que não precisam de tenant context
    excluded_paths = ['/static/', '/super_admin/', '/_']
    excluded_endpoints = ['super_admin_login', 'super_admin_dashboard', 'super_admin_barbearias', 'super_admin_usuarios', 'super_admin_relatorios', 'super_admin_redirect']
    
    # Se é rota excluída ou endpoint excluído, não configura tenant
    if any(request.path.startswith(path) for path in excluded_paths) or request.endpoint in excluded_endpoints:
        return
        
    # Tentar configurar contexto do tenant (excluir apenas rotas específicas)
    if request.endpoint and not request.endpoint.endswith('_internal_debug'):
        try:
            # Passar os modelos para evitar import circular
            setup_tenant_context(Usuario, UsuarioBarbearia, Barbearia, db)
        except Exception as e:
            # Se falhar o setup do tenant, configura um contexto vazio
            g.tenant = None
            g.current_barbearia = None
            if 'sincronizar' in request.path:
                print(f"⚠️ [BEFORE_REQUEST] Erro no setup_tenant_context: {e}")
            pass

# ---------- FUNÇÕES HELPER ----------

def get_current_barbearia_slug():
    """Obtém o slug da barbearia atual do contexto"""
    try:
        if hasattr(g, 'tenant') and g.tenant and hasattr(g.tenant, 'barbearia') and g.tenant.barbearia:
            return g.tenant.barbearia.slug
        
        # Fallback: tentar obter da sessão
        barbearia_id = session.get('barbearia_id')
        if barbearia_id:
            barbearia = Barbearia.query.get(barbearia_id)
            if barbearia:
                return barbearia.slug
        
        # Último fallback
        return 'principal'
    except:
        return 'principal'


def enviar_email_reset(destino, assunto, corpo_html, corpo_texto=None):
    """Modo de teste: imprime o link no console. Se variáveis SMTP estiverem configuradas, tenta enviar."""
    try:
        mail_from = os.environ.get('MAIL_FROM') or f'no-reply@{get_current_barbearia_slug()}.local'

        # Imprime no console (modo teste)
        print(f"[EMAIL-TEST] Para: {destino}")
        print(f"[EMAIL-TEST] Assunto: {assunto}")
        print(f"[EMAIL-TEST] HTML:\n{corpo_html}")

        # Se houver configuração SMTP correta, tenta enviar de verdade
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = os.environ.get('SMTP_PORT')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        smtp_starttls = os.environ.get('SMTP_STARTTLS', 'false').lower() in ('1', 'true', 'yes')

        if smtp_host and smtp_port and smtp_user and smtp_pass:
            msg = EmailMessage()
            msg['Subject'] = assunto
            msg['From'] = mail_from
            msg['To'] = destino
            msg.set_content(corpo_texto or 'Verifique o HTML do e-mail')
            msg.add_alternative(corpo_html, subtype='html')
            try:
                port = int(smtp_port)
                if smtp_starttls:
                    # Porta típica 587 (STARTTLS)
                    with smtplib.SMTP(smtp_host, port) as server:
                        server.ehlo()
                        server.starttls()
                        server.login(smtp_user, smtp_pass)
                        server.send_message(msg)
                else:
                    # Usa SSL direto (porta típica 465)
                    with smtplib.SMTP_SSL(smtp_host, port) as server:
                        server.login(smtp_user, smtp_pass)
                        server.send_message(msg)

                print('[EMAIL-TEST] E-mail enviado via SMTP')
            except Exception as e:
                print('[EMAIL-TEST] Falha ao enviar via SMTP:', e)
        else:
            print('[EMAIL-TEST] SMTP não configurado completamente; envio real não tentado')
    except Exception as e:
        print('[EMAIL-TEST] Erro ao preparar email:', e)

@app.template_filter('format_phone')
def format_phone(value):
    if not value:
        return ""
    # Remove caracteres não numéricos
    digits = "".join(filter(str.isdigit, str(value)))
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    elif len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return value

# ---------- ROTAS ----------

# ============= ÁREA ADMINISTRATIVA (SUPER ADMIN) =============
@app.route('/', methods=['GET', 'POST'])
def index_login():
    """Login exclusivo para super admin"""
    if request.method == 'POST':
        login_input = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        if not login_input or not senha:
            flash('Usuário e senha são obrigatórios!', 'error')
            return render_template('super_admin/login.html')
        
        # Buscar super admin por username ou email
        usuario = Usuario.query.filter(
            ((Usuario.username == login_input) | (Usuario.email == login_input)),
            Usuario.tipo_conta == 'super_admin'
        ).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            return redirect('/selecionar_barbearia')
        else:
            flash('Credenciais inválidas ou acesso negado.', 'error')
    
    return render_template('super_admin/login.html')

@app.route('/selecionar_barbearia')
def selecionar_barbearia():
    """Página para super admin selecionar barbearia"""
    if 'usuario_id' not in session:
        return redirect('/')
    
    usuario = Usuario.query.get(session['usuario_id'])
    if not usuario or usuario.tipo_conta != 'super_admin':
        return redirect('/')
    
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    return render_template('selecionar_barbearia.html', barbearias=barbearias)

@app.route('/barbearias')
def admin_index():
    """Área administrativa - lista de barbearias (só para super admin)"""
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    return render_template('barbearias_lista.html', barbearias=barbearias)

# ============= REDIRECIONAMENTOS LEGADOS =============
@app.context_processor
def inject_planos_navbar():
    """Injeta a variável tem_planos em todos os templates para controle da navbar"""
    def check_planos():
        try:
            from tenant import get_current_barbearia_id
            b_id = get_current_barbearia_id()
            if b_id:
                return PlanoMensal.query.filter_by(barbearia_id=b_id, ativo=True).count() > 0
            return False
        except:
            return False
    return dict(tem_planos_sistema=check_planos())

@app.route('/nova_reserva')
def nova_reserva_redirect():
    """Redireciona /nova_reserva para barbearia principal"""
    return redirect(url_for('nova_reserva', slug='principal'))

@app.route('/login')
def login_redirect():
    """Redireciona /login para barbearia principal"""
    return redirect(url_for('login', slug='principal'))

@app.route('/cadastro')
def cadastro_redirect():
    """Redireciona /cadastro para barbearia principal"""
    return redirect(url_for('cadastro', slug='principal'))

# ============= ÁREA PÚBLICA (CLIENTES) =============
@app.route('/<slug>')
def barbearia_publica(slug):
    """Página pública de uma barbearia específica"""
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        return f"""
        <html>
        <head><title>Barbearia não encontrada</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ Barbearia não encontrada</h1>
            <p>A barbearia "<strong>{slug}</strong>" não foi encontrada ou está inativa.</p>
        </body>
        </html>
        """
    
    # Define contexto da barbearia
    session['barbearia_id'] = barbearia.id
    
    # Mostra página da barbearia com serviços e planos ativos
    servicos = Servico.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    planos = PlanoMensal.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    
    return render_template('barbearia_home.html', 
                         barbearia=barbearia, 
                         servicos=servicos,
                         planos=planos)

@app.route('/recuperar_senha', methods=['GET','POST'])
def recuperar_senha():
    if request.method == 'POST':
        # Rate limiting por IP
        client_ip = get_client_ip()
        allowed, remaining, lockout_seconds = check_rate_limit(client_ip, max_attempts=3, window=300) # 3 tentativas a cada 5 min
        
        if not allowed:
            minutes = lockout_seconds // 60
            flash(f'Muitas solicitações. Tente novamente em {minutes} minutos.', 'error')
            audit_log('recuperar_senha_blocked', details={'ip': client_ip})
            return render_template('recuperar_senha.html')

        email = sanitize_input(request.form.get('email','').strip())
        mensagem_generica = 'Se houver uma conta com este e-mail, você receberá um link para recuperação.'
        if not email:
            flash('Informe um e-mail válido.', 'warning')
            return redirect(url_for('recuperar_senha'))
        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        if not usuario:
            flash(mensagem_generica, 'info')
            return redirect(url_for('recuperar_senha'))

        # Criar token
        rec = RecuperacaoSenha(usuario_id=usuario.id)
        rec.gerar_token(horas_validade=1)
        db.session.add(rec)
        db.session.commit()

        link = url_for('recuperar_senha_token', token=rec.token, _external=True)
        print(f"[INFO] Recuperação de senha solicitada para {usuario.email} - link: {link}")
        html = render_template('emails/reset_senha.html', usuario=usuario, link=link, validade_horas=1)
        enviar_email_reset(usuario.email, 'Recuperação de senha', html)

        flash('Se enviamos um e-mail, verifique sua caixa de entrada (ou console do servidor em modo teste).', 'info')
        return redirect(url_for('recuperar_senha'))
    return render_template('recuperar_senha.html')

@app.route('/recuperar_senha/<token>', methods=['GET','POST'])
def recuperar_senha_token(token):
    # Log de segurança: tentativa de verificação de token
    client_ip = get_client_ip()
    
    # Busca o token no banco
    rec = RecuperacaoSenha.query.filter_by(token=token, usado=False).first()
    
    if not rec:
        audit_log('FAIL_PASSWORD_TOKEN', details=f"Token inexistente: {token[:10]}...")
        flash('Link de recuperação inválido ou já utilizado.', 'error')
        return redirect(url_for('recuperar_senha'))
    
    # Verifica validade
    if datetime.utcnow() > rec.expira_em:
        audit_log('FAIL_PASSWORD_TOKEN', user_id=rec.usuario_id, details="Token expirado")
        flash('Este link de recuperação expirou. Solicite um novo.', 'error')
        return redirect(url_for('recuperar_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('senha')
        confirmacao = request.form.get('senha_confirm')
        
        if not nova_senha or len(nova_senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('nova_senha.html', token=token)
            
        if nova_senha != confirmacao:
            flash('As senhas não coincidem.', 'error')
            return render_template('nova_senha.html', token=token)
            
        # Atualiza a senha do usuário
        usuario = Usuario.query.get(rec.usuario_id)
        if usuario:
            usuario.set_senha(nova_senha)
            rec.usado = True
            rec.data_uso = datetime.utcnow()
            db.session.commit()
            
            audit_log('SUCCESS_PASSWORD_RESET', user_id=usuario.id, details="Senha alterada via token")
            flash('Sua senha foi alterada com sucesso! Agora você pode fazer login.', 'success')
            
            # Tentar encontrar a barbearia do usuário para redirecionar melhor
            barbearia = None
            if usuario.barbearias:
                # Pega a primeira barbearia vinculada
                primeiro_vinculo = usuario.barbearias[0]
                barbearia = Barbearia.query.get(primeiro_vinculo.barbearia_id)
            
            if barbearia:
                return redirect(url_for('login', slug=barbearia.slug))
            return redirect('/')
        else:
            flash('Erro ao encontrar usuário associado.', 'error')
            
    return render_template('nova_senha.html', token=token)

@app.route('/<slug>/login', methods=['GET','POST'])
def login(slug):
    # Verificar se a barbearia existe
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        return redirect('/')
    
    # Define contexto da barbearia
    session['barbearia_id'] = barbearia.id
        
    if 'usuario_id' in session:
        return redirect(url_for('dashboard', slug=slug))
    
    if request.method == 'POST':
        # Rate limiting por IP
        client_ip = get_client_ip()
        print(f"[LOGIN DEBUG] IP do cliente: {client_ip}")
        print(f"[LOGIN DEBUG] Headers: {dict(request.headers)}")
        
        allowed, remaining, lockout_seconds = check_rate_limit(client_ip)
        
        if not allowed:
            minutes = lockout_seconds // 60
            flash(f'Muitas tentativas de login. Tente novamente em {minutes} minutos.', 'error')
            audit_log('login_blocked', details={'ip': client_ip, 'slug': slug})
            return render_template('cliente/login.html', barbearia=barbearia)
        
        login_input = sanitize_input(request.form.get('email', '').strip())
        senha = request.form.get('senha', '')
        
        print(f"[LOGIN DEBUG] Login input: {login_input}")
        print(f"[LOGIN DEBUG] Senha fornecida: {'***' if senha else 'VAZIA'}")
        
        if not login_input or not senha:
            flash('Email/usuário e senha são obrigatórios!', 'error')
            return render_template('cliente/login.html', barbearia=barbearia)
        
        # Para admins, buscar por username ou email
        # Para clientes, buscar apenas por email
        usuario = Usuario.query.filter(
            ((Usuario.username == login_input) | (Usuario.email == login_input)),
            Usuario.ativo == True
        ).first()
        
        print(f"[LOGIN DEBUG] Usuário encontrado: {usuario.nome if usuario else 'NÃO ENCONTRADO'}")
        
        if usuario and check_password_hash(usuario.senha, senha):
            print(f"[LOGIN DEBUG] Senha correta! Tipo de conta: {usuario.tipo_conta}")
            
            # Super admin tem acesso a qualquer barbearia
            if usuario.tipo_conta == 'super_admin':
                session.clear()  # Limpar sessão anterior
                session['usuario_id'] = usuario.id
                session['user_id'] = usuario.id  # compatibilidade
                session['usuario_nome'] = usuario.nome
                session['barbearia_id'] = barbearia.id  # Garantir contexto
                session['tipo_conta'] = 'super_admin'
                session.permanent = True  # Usar PERMANENT_SESSION_LIFETIME
                
                print(f"[LOGIN DEBUG] Sessão criada: {dict(session)}")
                
                # Registrar sucesso
                record_login_attempt(client_ip, success=True)
                audit_log('login_success', user_id=usuario.id, details={'slug': slug, 'tipo': 'super_admin'})
                
                flash('Login realizado com sucesso!', 'success')
                redirect_url = url_for('dashboard', slug=slug)
                print(f"[LOGIN DEBUG] Redirecionando para: {redirect_url}")
                return redirect(redirect_url)
            
            # Para outros tipos de usuário, verificar vínculo com a barbearia
            usuario_barbearia = UsuarioBarbearia.query.filter_by(
                usuario_id=usuario.id,
                barbearia_id=barbearia.id,
                ativo=True
            ).first()
            
            if not usuario_barbearia:
                record_login_attempt(client_ip, success=False)
                audit_log('login_failed', user_id=usuario.id, details={'reason': 'no_access_to_barbearia', 'slug': slug})
                flash('Usuário não tem acesso a esta barbearia!', 'error')
                return render_template('cliente/login.html', barbearia=barbearia)
            
            # Login bem-sucedido
            session['usuario_id'] = usuario.id
            session['user_id'] = usuario.id  # compatibilidade
            session['usuario_nome'] = usuario.nome
            session['barbearia_id'] = barbearia.id  # Garantir contexto
            session['usuario_role'] = usuario_barbearia.role  # Armazenar role na sessão
            session.permanent = True  # Usar PERMANENT_SESSION_LIFETIME
            
            # Registrar sucesso
            record_login_attempt(client_ip, success=True)
            audit_log('login_success', user_id=usuario.id, details={'slug': slug, 'role': usuario_barbearia.role})
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard', slug=slug))
        else:
            # Login falhou
            record_login_attempt(client_ip, success=False)
            if usuario:
                audit_log('login_failed', user_id=usuario.id, details={'reason': 'wrong_password', 'slug': slug})
            else:
                audit_log('login_failed', details={'reason': 'user_not_found', 'login_input': login_input[:20], 'slug': slug})
            
            if remaining <= 2:
                flash(f'Credenciais inválidas! Você tem mais {remaining} tentativas.', 'error')
            else:
                flash('Credenciais inválidas!', 'error')
    
    return render_template('cliente/login.html', barbearia=get_current_barbearia())

# Legacy server-based session login is used via /<slug>/login

@app.route('/<slug>/cadastro', methods=['GET','POST'])
def cadastro(slug):
    # Verificar se a barbearia existe
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        return redirect('/')
    
    # Define contexto da barbearia
    session['barbearia_id'] = barbearia.id
        
    if request.method == 'POST':
        # Sanitizar inputs
        nome = sanitize_input(request.form.get('nome', '').strip())
        email = sanitize_input(request.form.get('email', '').strip().lower())
        telefone = sanitize_input(request.form.get('telefone', '').strip())
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validações
        if not all([nome, email, telefone, senha]):
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('cliente/cadastro_cliente.html', barbearia=barbearia)
        
        if len(nome) < 3:
            flash('Nome deve ter pelo menos 3 caracteres!', 'error')
            return render_template('cliente/cadastro_cliente.html', barbearia=barbearia)
        
        if not validate_email(email):
            flash('Email inválido!', 'error')
            return render_template('cliente/cadastro_cliente.html', barbearia=barbearia)
        
        if not validate_phone(telefone):
            flash('Telefone inválido! Use formato: (00) 00000-0000', 'error')
            return render_template('cliente/cadastro_cliente.html', barbearia=barbearia)
        
        # Validar senha
        valid, message = validate_password_strength(senha)
        if not valid:
            flash(message, 'error')
            return render_template('cliente/cadastro_cliente.html', barbearia=barbearia)
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'error')
            return render_template('cliente/cadastro_cliente.html', barbearia=barbearia)
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'warning')
            audit_log('cadastro_failed', details={'reason': 'email_exists', 'email': email[:20], 'slug': slug})
            return redirect(url_for('cadastro', slug=slug))
        
        # Criar usuário
        novo = Usuario(
            nome=nome, 
            email=email, 
            telefone=telefone,
            senha=generate_password_hash(senha), 
            tipo_conta='cliente',
            ativo=True
        )
        db.session.add(novo)
        db.session.commit()
        
        # Vincular à barbearia específica
        vinculo = UsuarioBarbearia(
            usuario_id=novo.id,
            barbearia_id=barbearia.id,
            role='cliente',
            ativo=True
        )
        db.session.add(vinculo)
        db.session.commit()
        
        # Registrar auditoria
        audit_log('cadastro_success', user_id=novo.id, details={'slug': slug})
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login', slug=slug))
    
    return render_template('cliente/cadastro_cliente.html', barbearia=get_current_barbearia())


# Rota de dashboard genérica — direciona para dashboard do admin ou do cliente conforme sessão
@app.route('/dashboard', defaults={'slug': 'principal'})
@app.route('/<slug>/dashboard')
def dashboard(slug):
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        return redirect('/')
    # garantir contexto
    session['barbearia_id'] = barbearia.id

    # se usuário logado e for admin da barbearia ou barbeiro, mostrar dashboard admin
    usuario = None
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
    # Considerar super_admin também como administrador para fins de visualização
    try:
        from flask import g
        is_super = hasattr(g, 'tenant') and getattr(g.tenant, 'is_super_admin', False)
    except Exception:
        is_super = False
    if is_super or (usuario and usuario.tipo_conta in ('admin_barbearia', 'barbeiro', 'admin_sistema')):
        # Buscar estatísticas para o dashboard admin
        servicos_ativos = Servico.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
        
        # Buscar clientes que já agendaram nesta barbearia
        clientes_ids = db.session.query(Reserva.cliente_id).filter_by(barbearia_id=barbearia.id).distinct().all()
        clientes_ids = [c[0] for c in clientes_ids]
        clientes_vinculados = UsuarioBarbearia.query.filter_by(barbearia_id=barbearia.id, role='cliente').all()
        vinculos_ids = [v.usuario_id for v in clientes_vinculados]
        
        todos_clientes_ids = list(set(clientes_ids + vinculos_ids))
        usuarios_lista = Usuario.query.filter(Usuario.id.in_(todos_clientes_ids)).all() if todos_clientes_ids else []

        return render_template('admin/dashboard.html', 
                             barbearia=barbearia, 
                             servicos=servicos_ativos,
                             usuarios=usuarios_lista)

    # caso contrário, mostrar dashboard do cliente
    reservas = []
    total_reservas = 0
    if 'usuario_id' in session:
        reservas = Reserva.query.filter_by(barbearia_id=barbearia.id, cliente_id=session['usuario_id']).filter(Reserva.status.in_(['agendada', 'confirmada'])).all()
        total_reservas = Reserva.query.filter_by(barbearia_id=barbearia.id, cliente_id=session['usuario_id']).filter(Reserva.status != 'cancelada').count()
    servicos = Servico.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    planos = PlanoMensal.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    return render_template('usuario_dashboard.html', reservas=reservas, total_reservas=total_reservas, servicos=servicos, planos=planos, barbearia=barbearia, user_type='cliente', filtro='pendentes')

@app.route('/<slug>/logout')
def logout(slug):
    session.clear(); flash('Você saiu.', 'info'); return redirect(url_for('barbearia_publica', slug=slug))

@app.route('/super_admin/logout')
def super_admin_logout():
    session.clear(); flash('Super Admin desconectado.', 'info'); return redirect('/')

@app.route('/<slug>/planos')
def planos_mensais(slug):
    """Lista planos mensais da barbearia"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        flash('Barbearia não encontrada.', 'error')
        return redirect('/')
    
    # Buscar planos ativos da barbearia
    planos = PlanoMensal.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    
    if not planos:
        return redirect(url_for('dashboard', slug=slug))
    
    # Verificar se o usuário já tem assinatura ativa
    assinatura_ativa = AssinaturaPlano.query.join(PlanoMensal).filter(
        AssinaturaPlano.cliente_id == session['usuario_id'],
        PlanoMensal.barbearia_id == barbearia.id,
        AssinaturaPlano.status == 'ativa'
    ).first()
    
    return render_template('cliente/planos.html', 
                         planos=planos, 
                         assinatura_ativa=assinatura_ativa,
                         barbearia=barbearia)


# Super Admin: entrar como admin de uma barbearia específica
@app.route('/super_admin/login_as/<slug>')
@require_super_admin
def super_admin_login_as(slug):
    # Busca barbearia
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        flash('Barbearia não encontrada.', 'error')
        return redirect(url_for('super_admin_barbearias'))

    # Define contexto via sessão para que tenant identifique a barbearia
    session['barbearia_id'] = barbearia.id

    # Redireciona para o dashboard da barbearia (tenant vai detectar que o user é super_admin)
    flash(f'Você entrou como Super Admin na barbearia "{barbearia.nome}".', 'info')
    return redirect(url_for('dashboard', slug=slug))

@app.route('/<slug>/assinar_plano/<string:plano_uuid>', methods=['POST'])
def assinar_plano(slug, plano_uuid):
    """Cliente assina um plano mensal"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(plano_uuid)
    if not is_valid:
        flash('Plano inválido!', 'error')
        return redirect(url_for('planos_mensais', slug=slug))
    
    plano = PlanoMensal.query.filter_by(uuid=sanitized_uuid, ativo=True).first()
    if not plano:
        flash('Plano não encontrado!', 'error')
        return redirect(url_for('planos_mensais', slug=slug))
    
    # Verificar se já tem assinatura ativa
    assinatura_existente = AssinaturaPlano.query.join(PlanoMensal).filter(
        AssinaturaPlano.cliente_id == session['usuario_id'],
        PlanoMensal.barbearia_id == plano.barbearia_id,
        AssinaturaPlano.status == 'ativa'
    ).first()
    
    if assinatura_existente:
        flash('Você já possui um plano ativo nesta barbearia!', 'warning')
        return redirect(url_for('planos_mensais', slug=slug))
    
    # Criar assinatura
    from datetime import datetime, timedelta
    nova_assinatura = AssinaturaPlano(
        plano_id=plano.id,
        cliente_id=session['usuario_id'],
        status='ativa',
        atendimentos_restantes=plano.atendimentos_mes,
        data_renovacao=datetime.now() + timedelta(days=30)
    )
    
    db.session.add(nova_assinatura)
    db.session.commit()
    
    flash(f'Parabéns! Você assinou o {plano.nome}. Aproveite seus benefícios!', 'success')
    return redirect(url_for('planos_mensais', slug=slug))

@app.route('/<slug>/cancelar_assinatura/<string:assinatura_uuid>', methods=['POST'])
def cancelar_assinatura(slug, assinatura_uuid):
    """Cliente cancela sua assinatura"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(assinatura_uuid)
    if not is_valid:
        flash('Assinatura inválida!', 'error')
        return redirect(url_for('planos_mensais', slug=slug))
    
    assinatura = AssinaturaPlano.query.filter_by(
        uuid=sanitized_uuid,
        cliente_id=session['usuario_id'],
        status='ativa'
    ).first()
    
    if not assinatura:
        flash('Assinatura não encontrada!', 'error')
        return redirect(url_for('planos_mensais', slug=slug))
    
    # Cancelar assinatura
    from datetime import datetime
    assinatura.status = 'cancelada'
    assinatura.data_fim = datetime.now()
    
    db.session.commit()
    
    flash('Assinatura cancelada com sucesso.', 'info')
    return redirect(url_for('planos_mensais', slug=slug))


@app.route('/api/horarios_disponiveis')
def horarios_disponiveis():
    data = request.args.get('data')
    if not data:
        return jsonify({'error': 'Data não fornecida'}), 400
    
    try:
        from datetime import datetime
        data_obj = datetime.strptime(data, '%Y-%m-%d')
        dia_semana = data_obj.strftime('%A').lower()
        
        # Obter barbearia atual
        barbearia_id = get_current_barbearia_id()
        if not barbearia_id:
            return jsonify({'error': 'Barbearia não encontrada'}), 400
        
        # Obter configuração da semana para esta data
        config_semana = DisponibilidadeSemanal.get_ou_criar_semana(data, barbearia_id)
        config = config_semana.get_config()
        
        # Verificar se o dia está ativo
        dia_config = config.get(dia_semana, {'ativo': False, 'horarios': []})
        if not dia_config.get('ativo', False):
            return jsonify({'horarios': []})
        
        # Obter horários configurados para este dia
        horarios_config = dia_config.get('horarios', [])
        
        # Obter horários já reservados para essa data na barbearia atual
        reservas_existentes = Reserva.query.filter_by(
            data=data, 
            barbearia_id=barbearia_id
        ).all()
        horarios_ocupados = [r.hora_inicio for r in reservas_existentes]
        
        # Filtrar horários disponíveis
        horarios_disponiveis_list = [h for h in horarios_config if h not in horarios_ocupados]
        
        return jsonify({'horarios': horarios_disponiveis_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/<slug>/nova_reserva', methods=['GET','POST'])
def nova_reserva(slug):
    if 'usuario_id' not in session: return redirect(url_for('login', slug=slug))
    if hasattr(g, 'tenant') and g.tenant and g.tenant.is_admin(): 
        flash('Admins não podem reservar.', 'danger'); 
        return redirect(url_for('dashboard', slug=slug))
    
    # Obter barbearia pelo slug
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        flash('Barbearia não encontrada.', 'error')
        return redirect(url_for('admin_index'))
    
    # Definir contexto
    session['barbearia_id'] = barbearia.id
    
    servicos = Servico.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    if request.method == 'POST':
        try:
            servico_id = int(request.form.get('servico'))
        except Exception:
            flash('Selecione serviço válido.', 'warning'); return redirect(url_for('nova_reserva', slug=slug))
        data = request.form.get('data'); hora = request.form.get('hora')
        
        # Verificar se o cliente tem plano ativo com atendimentos restantes
        cliente_id = session['usuario_id']
        assinatura_ativa = AssinaturaPlano.query.join(
            PlanoMensal, AssinaturaPlano.plano_id == PlanoMensal.id
        ).filter(
            AssinaturaPlano.cliente_id == cliente_id,
            AssinaturaPlano.status == 'ativa',
            PlanoMensal.barbearia_id == barbearia.id
        ).first()
        
        if assinatura_ativa and assinatura_ativa.atendimentos_restantes == 0:
            flash(f'❌ Você não possui mais cortes restantes no plano "{assinatura_ativa.plano.nome}". Entre em contato com a barbearia para renovar seu plano.', 'danger')
            return redirect(url_for('nova_reserva', slug=slug))
        
        # Verificar se o horário está dentro da disponibilidade configurada
        try:
            from datetime import datetime
            data_obj = datetime.strptime(data, '%Y-%m-%d')
            dia_semana = data_obj.strftime('%A').lower()
            
            # Usar a barbearia já obtida
            temp_barbearia_id = barbearia.id
                
            config_semana = DisponibilidadeSemanal.get_ou_criar_semana(data, temp_barbearia_id)
            config = config_semana.get_config()
            
            dia_config = config.get(dia_semana, {'ativo': False, 'horarios': []})
            
            if not dia_config.get('ativo', False):
                flash('Data não disponível para agendamentos.', 'danger')
                return redirect(url_for('nova_reserva', slug=slug))
            
            if hora not in dia_config.get('horarios', []):
                flash('Horário não disponível.', 'danger')
                return redirect(url_for('nova_reserva', slug=slug))
        
        except Exception:
            flash('Data ou horário inválido.', 'danger')
            return redirect(url_for('nova_reserva', slug=slug))
        
        # Verificar capacidade da barbearia para este horário
        config = barbearia.get_configuracoes()
        capacidade = config.get('vagas_por_horario', 1)
        
        agendamentos_no_horario = Reserva.query.filter_by(
            barbearia_id=barbearia.id, 
            data=data, 
            hora_inicio=hora
        ).filter(Reserva.status.in_(['agendada', 'confirmada'])).count()
        
        if agendamentos_no_horario >= capacidade:
            flash(f'Desculpe, este horário já está totalmente preenchido (máximo {capacidade} clientes).', 'danger')
            return redirect(url_for('nova_reserva', slug=slug))
        
        # Calcular hora fim baseado na duração do serviço
        servico = Servico.query.get(servico_id)
        from datetime import datetime, timedelta
        hora_inicio_dt = datetime.strptime(hora, '%H:%M')
        hora_fim_dt = hora_inicio_dt + timedelta(minutes=servico.duracao)
        hora_fim = hora_fim_dt.strftime('%H:%M')
        
        reserva = Reserva(
            barbearia_id=barbearia.id,
            cliente_id=session['usuario_id'], 
            servico_id=servico_id, 
            data=data, 
            hora_inicio=hora,
            hora_fim=hora_fim
        )
        db.session.add(reserva); db.session.commit(); flash('Reserva criada com sucesso!', 'success'); return redirect(url_for('dashboard', slug=slug))
    return render_template('cliente/nova_reserva.html', servicos=servicos, barbearia=barbearia)

# ---------- ROTAS ADMINISTRATIVAS POR BARBEARIA ----------

@app.route('/<slug>/admin/clientes')
def admin_clientes(slug):
    """Lista clientes da barbearia específica"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    usuarios_barbearia = db.session.query(Usuario).join(UsuarioBarbearia).filter(
        UsuarioBarbearia.barbearia_id == barbearia_id,
        UsuarioBarbearia.role == 'cliente',
        UsuarioBarbearia.ativo == True
    ).all()
    
    return render_template('cliente/clientes.html', 
                         usuarios=usuarios_barbearia,
                         barbearia=get_current_barbearia())

@app.route('/<slug>/admin/planos-ativos')
def admin_planos_ativos(slug):
    """Lista clientes com planos mensais ativos"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    
    # Buscar assinaturas ativas da barbearia
    assinaturas_ativas = db.session.query(AssinaturaPlano).join(
        PlanoMensal, AssinaturaPlano.plano_id == PlanoMensal.id
    ).join(
        Usuario, AssinaturaPlano.cliente_id == Usuario.id
    ).filter(
        PlanoMensal.barbearia_id == barbearia_id,
        AssinaturaPlano.status == 'ativa'
    ).order_by(AssinaturaPlano.data_inicio.desc()).all()
    
    # Calcular estatísticas
    total_assinaturas = len(assinaturas_ativas)
    receita_mensal = sum(ass.plano.preco for ass in assinaturas_ativas)
    total_atendimentos = sum(ass.plano.atendimentos_mes for ass in assinaturas_ativas)
    # Buscar clientes da barbearia para permitir atribuição
    clientes_barbearia = db.session.query(Usuario).join(UsuarioBarbearia).filter(
        UsuarioBarbearia.barbearia_id == barbearia_id,
        UsuarioBarbearia.role == 'cliente',
        UsuarioBarbearia.ativo == True
    ).all()

    # Buscar planos disponíveis
    planos = PlanoMensal.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()

    return render_template('admin/planos_ativos.html',
                         assinaturas=assinaturas_ativas,
                         barbearia=get_current_barbearia(),
                         total_assinaturas=total_assinaturas,
                         receita_mensal=receita_mensal,
                         total_atendimentos=total_atendimentos,
                         clientes=clientes_barbearia,
                         planos=planos)


@app.route('/<slug>/admin/adicionar_assinatura', methods=['POST'])
def admin_adicionar_assinatura(slug):
    """Permite ao admin adicionar uma assinatura para um cliente manualmente"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))
    cliente_id_raw = request.form.get('cliente_id')
    plano_id_raw = request.form.get('plano_id')
    try:
        cliente_id = int(cliente_id_raw) if cliente_id_raw else None
        plano_id = int(plano_id_raw) if plano_id_raw else None
    except (ValueError, TypeError):
        flash('IDs inválidos enviados pelo formulário.', 'danger')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    if not cliente_id or not plano_id:
        flash('Cliente e plano são obrigatórios.', 'warning')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    # Validar que cliente pertence à barbearia
    barbearia_id = get_current_barbearia_id()
    vinculo = UsuarioBarbearia.query.filter_by(usuario_id=cliente_id, barbearia_id=barbearia_id, role='cliente').first()
    if not vinculo:
        flash('Cliente não encontrado nesta barbearia.', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    plano = PlanoMensal.query.filter_by(id=plano_id, barbearia_id=barbearia_id, ativo=True).first()
    if not plano:
        flash('Plano inválido.', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    # Verificar se já existe assinatura ativa para esse cliente
    existente = AssinaturaPlano.query.filter_by(cliente_id=cliente_id, status='ativa').join(PlanoMensal).filter(PlanoMensal.barbearia_id == barbearia_id).first()
    if existente:
        flash('Cliente já possui uma assinatura ativa nesta barbearia.', 'warning')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    from datetime import datetime, timedelta
    nova = AssinaturaPlano(
        plano_id=plano.id,
        cliente_id=cliente_id,
        status='ativa',
        atendimentos_restantes=plano.atendimentos_mes,
        data_renovacao=datetime.now() + timedelta(days=30)
    )
    db.session.add(nova)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar assinatura: {e}', 'danger')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    flash(f'Assinatura do cliente adicionada ao plano "{plano.nome}" com sucesso.', 'success')
    return redirect(url_for('admin_planos_ativos', slug=slug))

@app.route('/<slug>/admin/cancelar_assinatura/<string:assinatura_uuid>', methods=['POST'])
def admin_cancelar_assinatura(slug, assinatura_uuid):
    """Permite ao admin cancelar uma assinatura manualmente"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(assinatura_uuid)
    if not is_valid:
        flash('Assinatura inválida.', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    # Buscar assinatura ativa vinculada à barbearia
    barbearia_id = get_current_barbearia_id()
    assinatura = AssinaturaPlano.query.join(PlanoMensal).filter(
        AssinaturaPlano.uuid == sanitized_uuid,
        AssinaturaPlano.status == 'ativa',
        PlanoMensal.barbearia_id == barbearia_id
    ).first()

    if not assinatura:
        flash('Assinatura não encontrada ou já cancelada.', 'warning')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    from datetime import datetime
    assinatura.status = 'cancelada'
    assinatura.data_fim = datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar assinatura: {e}', 'danger')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    flash('Assinatura cancelada com sucesso.', 'success')
    return redirect(url_for('admin_planos_ativos', slug=slug))

@app.route('/<slug>/admin/renovar_assinatura/<string:assinatura_uuid>', methods=['POST'])
def admin_renovar_assinatura(slug, assinatura_uuid):
    """Permite ao admin renovar uma assinatura, resetando os atendimentos restantes"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(assinatura_uuid)
    if not is_valid:
        flash('Assinatura inválida.', 'error')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    # Buscar assinatura ativa vinculada à barbearia
    barbearia_id = get_current_barbearia_id()
    assinatura = AssinaturaPlano.query.join(PlanoMensal).filter(
        AssinaturaPlano.uuid == sanitized_uuid,
        AssinaturaPlano.status == 'ativa',
        PlanoMensal.barbearia_id == barbearia_id
    ).first()

    if not assinatura:
        flash('Assinatura não encontrada ou já cancelada.', 'warning')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    # Renovar assinatura: resetar atendimentos restantes
    assinatura.atendimentos_restantes = assinatura.plano.atendimentos_mes
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao renovar assinatura: {e}', 'danger')
        return redirect(url_for('admin_planos_ativos', slug=slug))

    flash(f'Assinatura de {assinatura.cliente.nome} renovada com sucesso! {assinatura.atendimentos_restantes} cortes disponíveis.', 'success')
    return redirect(url_for('admin_planos_ativos', slug=slug))

@app.route('/<slug>/admin/despesas')
def admin_despesas(slug):
    """Lista e gerencia despesas da barbearia"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    from datetime import datetime, date
    from sqlalchemy import extract, func
    
    barbearia_id = get_current_barbearia_id()
    
    # Filtros
    mes_filtro = request.args.get('mes', datetime.now().strftime('%Y-%m'))
    categoria_filtro = request.args.get('categoria', 'todas')
    status_filtro = request.args.get('status', 'todas')
    
    # Query base
    query = Despesa.query.filter_by(barbearia_id=barbearia_id)
    
    # Aplicar filtro de mês
    if mes_filtro:
        ano, mes = mes_filtro.split('-')
        query = query.filter(
            extract('year', Despesa.data_vencimento) == int(ano),
            extract('month', Despesa.data_vencimento) == int(mes)
        )
    
    # Aplicar filtro de categoria
    if categoria_filtro != 'todas':
        query = query.filter_by(categoria=categoria_filtro)
    
    # Aplicar filtro de status
    if status_filtro != 'todas':
        query = query.filter_by(status=status_filtro)
    
    despesas = query.order_by(Despesa.data_vencimento.desc()).all()
    
    # Atualizar status de despesas atrasadas
    for despesa in despesas:
        if despesa.esta_atrasada and despesa.status == 'pendente':
            despesa.status = 'atrasada'
    db.session.commit()
    
    # Estatísticas do mês
    total_despesas = sum(d.valor for d in despesas)
    total_pagas = sum(d.valor for d in despesas if d.status == 'paga')
    total_pendentes = sum(d.valor for d in despesas if d.status == 'pendente')
    total_atrasadas = sum(d.valor for d in despesas if d.status == 'atrasada')
    
    # Despesas por categoria
    despesas_por_categoria = {}
    for despesa in despesas:
        if despesa.categoria not in despesas_por_categoria:
            despesas_por_categoria[despesa.categoria] = 0
        despesas_por_categoria[despesa.categoria] += despesa.valor
    
    return render_template('admin/despesas.html',
                         despesas=despesas,
                         barbearia=get_current_barbearia(),
                         mes_filtro=mes_filtro,
                         categoria_filtro=categoria_filtro,
                         status_filtro=status_filtro,
                         total_despesas=total_despesas,
                         total_pagas=total_pagas,
                         total_pendentes=total_pendentes,
                         total_atrasadas=total_atrasadas,
                         despesas_por_categoria=despesas_por_categoria)

@app.route('/<slug>/admin/despesas/adicionar', methods=['POST'])
def admin_adicionar_despesa(slug):
    """Adiciona uma nova despesa"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    from datetime import datetime
    
    try:
        data = request.get_json()
        
        despesa = Despesa(
            barbearia_id=get_current_barbearia_id(),
            descricao=data['descricao'],
            categoria=data['categoria'],
            valor=float(data['valor']),
            data_vencimento=datetime.strptime(data['data_vencimento'], '%Y-%m-%d').date(),
            recorrente=data.get('recorrente', False),
            observacoes=data.get('observacoes', ''),
            criado_por=session['usuario_id']
        )
        
        db.session.add(despesa)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Despesa adicionada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/<slug>/admin/despesas/<string:despesa_uuid>/pagar', methods=['POST'])
def admin_pagar_despesa(slug, despesa_uuid):
    """Marca despesa como paga"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    from datetime import date
    
    despesa = Despesa.query.filter_by(uuid=despesa_uuid).first()
    if not despesa:
        return jsonify({'success': False, 'message': 'Despesa não encontrada'}), 404
    
    despesa.status = 'paga'
    despesa.data_pagamento = date.today()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Despesa marcada como paga!'})

@app.route('/<slug>/admin/despesas/<string:despesa_uuid>/excluir', methods=['POST'])
def admin_excluir_despesa(slug, despesa_uuid):
    """Exclui uma despesa"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    despesa = Despesa.query.filter_by(uuid=despesa_uuid).first()
    if not despesa:
        return jsonify({'success': False, 'message': 'Despesa não encontrada'}), 404
    
    db.session.delete(despesa)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Despesa excluída com sucesso!'})

@app.route('/<slug>/admin/servicos')
def admin_servicos(slug):
    """Lista serviços da barbearia específica"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    servicos = Servico.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()
    
    return render_template('cliente/servicos.html', 
                         servicos=servicos,
                         barbearia=get_current_barbearia())

@app.route('/<slug>/admin/agendamentos')
def admin_agendamentos_slug(slug):
    """Lista todos os agendamentos da barbearia específica com filtros"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        flash('Barbearia não encontrada.', 'error')
        return redirect(url_for('admin_index'))
    
    # Definir contexto
    session['barbearia_id'] = barbearia.id
    barbearia_id = barbearia.id
    
    # Obter filtros da query string
    status_filtro = request.args.get('status', 'todos')
    filtro_periodo = request.args.get('filtro', '')  # Filtro de período (hoje, semana, etc)
    search_term = request.args.get('search', '')     # Busca por nome do cliente
    
    # Construir query base
    query = Reserva.query.filter_by(barbearia_id=barbearia_id)
    
    # Aplicar busca por nome se houver
    if search_term:
        query = query.join(Usuario, Reserva.cliente_id == Usuario.id).filter(
            Usuario.nome.ilike(f'%{search_term}%')
        )

    # Aplicar filtro de período
    if filtro_periodo == 'hoje':
        hoje_str = datetime.now().strftime('%Y-%m-%d')
        query = query.filter(Reserva.data == hoje_str)
    elif filtro_periodo == 'amanha':
        from datetime import timedelta
        amanha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        query = query.filter(Reserva.data == amanha)
    elif filtro_periodo == 'semana':
        from datetime import timedelta
        hoje = datetime.now()
        inicio_semana = (hoje - timedelta(days=hoje.weekday())).strftime('%Y-%m-%d')
        fim_semana = (hoje + timedelta(days=(6 - hoje.weekday()))).strftime('%Y-%m-%d')
        query = query.filter(Reserva.data >= inicio_semana, Reserva.data <= fim_semana)
    elif filtro_periodo == 'mes':
        mes_atual = datetime.now().strftime('%Y-%m')
        query = query.filter(Reserva.data.like(f'{mes_atual}%'))
    
    # Aplicar filtro de status
    if status_filtro == 'ativos':
        # Mostrar apenas agendados, confirmados e atendendo (excluir cancelados e concluídos)
        query = query.filter(Reserva.status.in_(['agendada', 'confirmada', 'atendendo']))
    elif status_filtro == 'concluidos':
        # Mostrar apenas concluídos
        query = query.filter_by(status='concluida')
    elif status_filtro == 'todos':
        # Mostrar tudo exceto cancelados
        query = query.filter(Reserva.status != 'cancelada')
    elif status_filtro != 'todos':
        query = query.filter_by(status=status_filtro)
    
    # Ordenar por data e hora
    reservas = query.order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
    
    # Contar por status
    status_counts = {
        'ativos': Reserva.query.filter_by(barbearia_id=barbearia_id).filter(
            Reserva.status.in_(['agendada', 'confirmada', 'atendendo'])
        ).count(),
        'concluidos': Reserva.query.filter_by(barbearia_id=barbearia_id, status='concluida').count(),
        'todos': Reserva.query.filter_by(barbearia_id=barbearia_id).filter(
            Reserva.status != 'cancelada'
        ).count(),
        'agendada': Reserva.query.filter_by(barbearia_id=barbearia_id, status='agendada').count(),
        'confirmada': Reserva.query.filter_by(barbearia_id=barbearia_id, status='confirmada').count(),
        'atendendo': Reserva.query.filter_by(barbearia_id=barbearia_id, status='atendendo').count()
    }
    
    # Adicionar informação de plano para cada reserva
    for reserva in reservas:
        reserva.tem_plano = False
        reserva.plano_nome = None
        reserva.sem_cortes_restantes = False
        if reserva.cliente:
            assinatura_ativa = AssinaturaPlano.query.join(
                PlanoMensal, AssinaturaPlano.plano_id == PlanoMensal.id
            ).filter(
                AssinaturaPlano.cliente_id == reserva.cliente_id,
                AssinaturaPlano.status == 'ativa',
                PlanoMensal.barbearia_id == barbearia_id
            ).first()
            
            if assinatura_ativa:
                reserva.tem_plano = True
                reserva.plano_nome = assinatura_ativa.plano.nome
                reserva.sem_cortes_restantes = assinatura_ativa.atendimentos_restantes == 0
    
    return render_template('admin/admin_agendamentos.html', 
                         reservas=reservas,
                         barbearia=barbearia,
                         status_filtro=status_filtro,
                         filtro_periodo=filtro_periodo,
                         search_term=search_term,
                         status_counts=status_counts)

@app.route('/<slug>/admin/faturamento', methods=['GET', 'POST'])
def admin_faturamento(slug):
    """Dashboard de faturamento com análise por período"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    barbearia = get_current_barbearia()
    
    # --- Verificação de Senha Financeira ---
    if barbearia.senha_financeira:
        # Se houver senha, verificar se a sessão já está autorizada
        auth_key = f'financeiro_auth_{barbearia_id}'
        if not session.get(auth_key):
            if request.method == 'POST' and request.form.get('acao') == 'verificar_senha':
                senha_digitada = request.form.get('senha_financeira')
                if check_password_hash(barbearia.senha_financeira, senha_digitada):
                    session[auth_key] = True
                    # Permanecer na mesma página (GET)
                    return redirect(url_for('admin_faturamento', slug=slug))
                else:
                    flash('Senha financeira incorreta!', 'danger')
            
            return render_template('admin/faturamento_lock.html', barbearia=barbearia, locked=True)
    
    # Se não houver senha, permitir acesso mas enviar flag para o template sugerir criar uma
    mostrar_setup_senha = not barbearia.senha_financeira

    if request.method == 'POST':
        acao = request.form.get('acao')
        if acao == 'definir_senha':
            nova_senha = request.form.get('nova_senha')
            confirmar = request.form.get('confirmar_senha')
            if nova_senha and nova_senha == confirmar:
                barbearia.senha_financeira = generate_password_hash(nova_senha)
                db.session.commit()
                session[f'financeiro_auth_{barbearia_id}'] = True
                flash('Senha financeira definida com sucesso!', 'success')
                return redirect(url_for('admin_faturamento', slug=slug))
            else:
                flash('As senhas não coincidem!', 'danger')
        
        elif acao == 'bloquear':
            session.pop(f'financeiro_auth_{barbearia_id}', None)
            flash('Acesso financeiro bloqueado com sucesso.', 'info')
            return redirect(url_for('dashboard', slug=slug))

    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    
    barbearia_id = get_current_barbearia_id()
    barbearia = get_current_barbearia()
    
    # Obter data selecionada (padrão: hoje)
    data_selecionada_str = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    try:
        data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d')
    except:
        data_selecionada = datetime.now()
    
    # ===== FATURAMENTO DO DIA =====
    reservas_dia = Reserva.query.join(Servico).filter(
        Reserva.barbearia_id == barbearia_id,
        Reserva.data == data_selecionada.strftime('%Y-%m-%d'),
        Reserva.status.in_(['confirmada', 'concluida'])
    ).all()
    
    faturamento_dia = sum([r.servico.preco for r in reservas_dia if r.servico])
    quantidade_dia = len(reservas_dia)
    
    # ===== FATURAMENTO DA SEMANA =====
    inicio_semana = data_selecionada - timedelta(days=data_selecionada.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    
    reservas_semana = Reserva.query.join(Servico).filter(
        Reserva.barbearia_id == barbearia_id,
        Reserva.data >= inicio_semana.strftime('%Y-%m-%d'),
        Reserva.data <= fim_semana.strftime('%Y-%m-%d'),
        Reserva.status.in_(['confirmada', 'concluida'])
    ).all()
    
    faturamento_semana = sum([r.servico.preco for r in reservas_semana if r.servico])
    quantidade_semana = len(reservas_semana)
    
    # Faturamento por dia da semana
    faturamento_por_dia = {}
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        dia_str = dia.strftime('%Y-%m-%d')
        reservas_dia_semana = [r for r in reservas_semana if r.data == dia_str]
        faturamento_por_dia[dia.strftime('%A')] = {
            'data': dia_str,
            'valor': sum([r.servico.preco for r in reservas_dia_semana if r.servico]),
            'quantidade': len(reservas_dia_semana)
        }
    
    # ===== FATURAMENTO DO MÊS =====
    inicio_mes = data_selecionada.replace(day=1)
    if data_selecionada.month == 12:
        fim_mes = data_selecionada.replace(year=data_selecionada.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        fim_mes = data_selecionada.replace(month=data_selecionada.month + 1, day=1) - timedelta(days=1)
    
    reservas_mes = Reserva.query.join(Servico).filter(
        Reserva.barbearia_id == barbearia_id,
        Reserva.data >= inicio_mes.strftime('%Y-%m-%d'),
        Reserva.data <= fim_mes.strftime('%Y-%m-%d'),
        Reserva.status.in_(['confirmada', 'concluida'])
    ).all()
    
    faturamento_mes = sum([r.servico.preco for r in reservas_mes if r.servico])
    quantidade_mes = len(reservas_mes)
    
    # ===== FATURAMENTO DO ANO =====
    inicio_ano = data_selecionada.replace(month=1, day=1)
    fim_ano = data_selecionada.replace(month=12, day=31)
    
    reservas_ano = Reserva.query.join(Servico).filter(
        Reserva.barbearia_id == barbearia_id,
        Reserva.data >= inicio_ano.strftime('%Y-%m-%d'),
        Reserva.data <= fim_ano.strftime('%Y-%m-%d'),
        Reserva.status.in_(['confirmada', 'concluida'])
    ).all()
    
    faturamento_ano = sum([r.servico.preco for r in reservas_ano if r.servico])
    quantidade_ano = len(reservas_ano)
    
    # Faturamento por mês do ano
    faturamento_por_mes = {}
    for mes in range(1, 13):
        reservas_mes_ano = [r for r in reservas_ano if datetime.strptime(r.data, '%Y-%m-%d').month == mes]
        faturamento_por_mes[mes] = {
            'valor': sum([r.servico.preco for r in reservas_mes_ano if r.servico]),
            'quantidade': len(reservas_mes_ano)
        }
    
    # ===== SERVIÇOS MAIS VENDIDOS =====
    servicos_count = {}
    for reserva in reservas_mes:
        if reserva.servico:
            servico_nome = reserva.servico.nome
            if servico_nome not in servicos_count:
                servicos_count[servico_nome] = {'quantidade': 0, 'valor': 0}
            servicos_count[servico_nome]['quantidade'] += 1
            servicos_count[servico_nome]['valor'] += reserva.servico.preco
    
    servicos_mais_vendidos = sorted(servicos_count.items(), key=lambda x: x[1]['quantidade'], reverse=True)[:5]
    
    # ===== BARBEIROS TOP =====
    barbeiros_stats = {}
    for reserva in reservas_mes:
        if reserva.barbeiro and reserva.servico:
            barbeiro_nome = reserva.barbeiro.nome
            if barbeiro_nome not in barbeiros_stats:
                barbeiros_stats[barbeiro_nome] = {'quantidade': 0, 'valor': 0}
            barbeiros_stats[barbeiro_nome]['quantidade'] += 1
            barbeiros_stats[barbeiro_nome]['valor'] += reserva.servico.preco
    
    barbeiros_top = sorted(barbeiros_stats.items(), key=lambda x: x[1]['valor'], reverse=True)[:5]
    
    return render_template('admin/faturamento.html',
                         barbearia=barbearia,
                         data_selecionada=data_selecionada,
                         faturamento_dia=faturamento_dia,
                         quantidade_dia=quantidade_dia,
                         faturamento_semana=faturamento_semana,
                         quantidade_semana=quantidade_semana,
                         faturamento_por_dia=faturamento_por_dia,
                         faturamento_mes=faturamento_mes,
                         quantidade_mes=quantidade_mes,
                         faturamento_ano=faturamento_ano,
                         quantidade_ano=quantidade_ano,
                         faturamento_por_mes=faturamento_por_mes,
                         servicos_mais_vendidos=servicos_mais_vendidos,
                         barbeiros_top=barbeiros_top,
                         inicio_semana=inicio_semana,
                         fim_semana=fim_semana,
                         inicio_mes=inicio_mes,
                         fim_mes=fim_mes,
                         mostrar_setup_senha=mostrar_setup_senha)

@app.route('/<slug>/admin/disponibilidade')
def admin_disponibilidade_slug(slug):
    """Configurar disponibilidade da barbearia específica"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    disponibilidades = DisponibilidadeSemanal.query.filter_by(
        barbearia_id=barbearia_id
    ).order_by(DisponibilidadeSemanal.dia_semana).all()
    
    return render_template('admin/disponibilidade.html', 
                         disponibilidades=disponibilidades,
                         barbearia=get_current_barbearia())

@app.route('/cancelar_reserva/<string:reserva_uuid>', methods=['POST'])
def cancelar_reserva(reserva_uuid):
    """Cliente cancela sua própria reserva"""
    if 'usuario_id' not in session:
        flash('Faça login.', 'warning')
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    
    reserva = Reserva.query.filter_by(uuid=reserva_uuid).first_or_404()
    
    # Pega a barbearia da reserva para redirecionar corretamente
    barbearia = Barbearia.query.get(reserva.barbearia_id)
    slug = barbearia.slug if barbearia else get_current_barbearia_slug()
    
    if reserva.cliente_id != session['usuario_id']:
        flash('Só pode cancelar suas reservas.', 'danger')
        return redirect(url_for('dashboard', slug=slug))
    # Mudar status para cancelada ao invés de deletar
    reserva.status = 'cancelada'
    db.session.commit()
    flash('Reserva cancelada com sucesso!', 'success')
    return redirect(url_for('dashboard', slug=slug))

@app.route('/<slug>/admin/cancelar_agendamento/<string:reserva_uuid>', methods=['POST'])
def admin_cancelar_agendamento(slug, reserva_uuid):
    """Rota para admin cancelar qualquer agendamento"""
    print(f"[DEBUG] Tentando cancelar agendamento UUID: {reserva_uuid}")
    
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado - apenas administradores'}), 403
    
    reserva = Reserva.query.filter_by(uuid=reserva_uuid).first()
    print(f"[DEBUG] Reserva encontrada: {reserva}")
    
    if not reserva:
        print(f"[DEBUG] Nenhuma reserva encontrada com UUID: {reserva_uuid}")
        # Listar todas as reservas para debug
        todas = Reserva.query.all()
        print(f"[DEBUG] Total de reservas no banco: {len(todas)}")
        for r in todas[:5]:  # Mostrar apenas as 5 primeiras
            print(f"  - ID: {r.id}, UUID: {r.uuid}, Cliente: {r.cliente.nome if r.cliente else 'N/A'}")
        return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
    
    # Verificar se o agendamento pertence à barbearia do admin
    barbearia_id = get_current_barbearia_id()
    if reserva.barbearia_id != barbearia_id:
        return jsonify({'success': False, 'message': 'Agendamento não pertence a esta barbearia'}), 403
    
    # Mudar status para cancelada ao invés de deletar
    reserva.status = 'cancelada'
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Agendamento cancelado com sucesso!',
        'reserva_uuid': reserva_uuid
    })

@app.route('/<slug>/admin/confirmar_atendimento/<string:reserva_uuid>', methods=['POST'])
def admin_confirmar_atendimento(slug, reserva_uuid):
    """Rota para admin confirmar e iniciar atendimento"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado - apenas administradores'}), 403
    
    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(reserva_uuid)
    if not is_valid:
        return jsonify({'success': False, 'message': 'UUID inválido'}), 400
    
    reserva = Reserva.query.filter_by(uuid=sanitized_uuid).first()
    
    if not reserva:
        return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
    
    # Verificar se o agendamento pertence à barbearia do admin
    barbearia_id = get_current_barbearia_id()
    if reserva.barbearia_id != barbearia_id:
        return jsonify({'success': False, 'message': 'Agendamento não pertence a esta barbearia'}), 403
    
    # Mudar status para "atendendo"
    reserva.status = 'atendendo'
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Atendimento iniciado!',
        'reserva_uuid': reserva_uuid,
        'novo_status': 'atendendo'
    })

@app.route('/<slug>/admin/concluir_atendimento/<string:reserva_uuid>', methods=['POST'])
def admin_concluir_atendimento(slug, reserva_uuid):
    """Rota para admin concluir atendimento"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado - apenas administradores'}), 403
    
    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(reserva_uuid)
    if not is_valid:
        return jsonify({'success': False, 'message': 'UUID inválido'}), 400
    
    reserva = Reserva.query.filter_by(uuid=sanitized_uuid).first()
    
    if not reserva:
        return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
    
    # Verificar se o agendamento pertence à barbearia do admin
    barbearia_id = get_current_barbearia_id()
    if reserva.barbearia_id != barbearia_id:
        return jsonify({'success': False, 'message': 'Agendamento não pertence a esta barbearia'}), 403
    
    # Mudar status para "concluida"
    reserva.status = 'concluida'
    
    # Verificar se o cliente tem plano ativo e descontar atendimento
    descontou_plano = False
    atendimentos_restantes = None
    plano_nome = None
    
    if reserva.cliente:
        assinatura_ativa = AssinaturaPlano.query.join(
            PlanoMensal, AssinaturaPlano.plano_id == PlanoMensal.id
        ).filter(
            AssinaturaPlano.cliente_id == reserva.cliente_id,
            AssinaturaPlano.status == 'ativa',
            PlanoMensal.barbearia_id == barbearia_id
        ).first()
        
        if assinatura_ativa and assinatura_ativa.atendimentos_restantes > 0:
            assinatura_ativa.atendimentos_restantes -= 1
            atendimentos_restantes = assinatura_ativa.atendimentos_restantes
            plano_nome = assinatura_ativa.plano.nome
            descontou_plano = True
            
            print(f"✅ Atendimento descontado do plano {plano_nome}. Restam: {atendimentos_restantes}")
            
            # Se acabaram os atendimentos, pode optar por desativar ou renovar
            if assinatura_ativa.atendimentos_restantes == 0:
                print(f"⚠️ Plano {plano_nome} do cliente {reserva.cliente.nome} zerou atendimentos!")
    
    db.session.commit()
    
    mensagem = 'Atendimento concluído!'
    if descontou_plano:
        mensagem = f'Atendimento concluído! Restam {atendimentos_restantes} atendimentos no plano {plano_nome}.'
    
    return jsonify({
        'success': True, 
        'message': mensagem,
        'reserva_uuid': reserva_uuid,
        'novo_status': 'concluida',
        'descontou_plano': descontou_plano,
        'atendimentos_restantes': atendimentos_restantes,
        'plano_nome': plano_nome
    })

@app.route('/<slug>/admin/alterar_status/<string:reserva_uuid>', methods=['POST'])
def admin_alterar_status(slug, reserva_uuid):
    """Rota para admin alterar o status de um agendamento"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado - apenas administradores'}), 403
    
    from security import validate_uuid
    is_valid, sanitized_uuid = validate_uuid(reserva_uuid)
    if not is_valid:
        return jsonify({'success': False, 'message': 'UUID inválido'}), 400
    
    # Obter o novo status do body
    data = request.get_json()
    novo_status = data.get('status')
    
    # Validar status
    status_validos = ['agendada', 'confirmada', 'atendendo', 'concluida', 'cancelada']
    if novo_status not in status_validos:
        return jsonify({'success': False, 'message': 'Status inválido'}), 400
    
    reserva = Reserva.query.filter_by(uuid=sanitized_uuid).first()
    
    if not reserva:
        return jsonify({'success': False, 'message': 'Agendamento não encontrado'}), 404
    
    # Verificar se o agendamento pertence à barbearia do admin
    barbearia_id = get_current_barbearia_id()
    if reserva.barbearia_id != barbearia_id:
        return jsonify({'success': False, 'message': 'Agendamento não pertence a esta barbearia'}), 403
    
    # Alterar status
    status_anterior = reserva.status
    reserva.status = novo_status
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Status alterado de "{status_anterior}" para "{novo_status}"',
        'reserva_uuid': reserva_uuid,
        'status_anterior': status_anterior,
        'novo_status': novo_status
    })

@app.route('/admin/agendamentos')
def admin_agendamentos():
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    reservas = Reserva.query.all()
    return render_template('admin/admin_agendamentos.html', 
                         reservas=reservas,
                         barbearia=get_current_barbearia())

@app.route('/admin/disponibilidade')
def admin_disponibilidade():
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    
    from datetime import datetime, timedelta
    
    # Obter semana atual
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
        # Obter próximas 8 semanas para exibir
    barbearia_id = get_current_barbearia_id()
    semanas = []
    for i in range(8):
        semana_inicio = inicio_semana + timedelta(weeks=i)
        semana_fim = semana_inicio + timedelta(days=6)
        
        # Buscar configuração existente para esta barbearia
        config_semana = DisponibilidadeSemanal.query.filter(
            DisponibilidadeSemanal.data_inicio == semana_inicio.strftime('%Y-%m-%d'),
            DisponibilidadeSemanal.barbearia_id == barbearia_id
        ).first()
        
        semanas.append({
            'inicio': semana_inicio,
            'fim': semana_fim,
            'configurada': config_semana is not None,
            'config_id': config_semana.id if config_semana else None
        })
    
    return render_template('admin/disponibilidade.html', 
                         semanas=semanas, 
                         barbearia=get_current_barbearia())

@app.route('/admin/disponibilidade/semana/<data_inicio>', methods=['GET', 'POST'])
def admin_disponibilidade_semana(data_inicio):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    
    from datetime import datetime, timedelta
    
    try:
        data_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
    except ValueError:
        flash('Data inválida!', 'danger')
        return redirect(url_for('admin_disponibilidade'))
    
    if request.method == 'POST':
        # Obter ou criar configuração da semana
        barbearia_id = get_current_barbearia_id()
        config_semana = DisponibilidadeSemanal.get_ou_criar_semana(data_inicio, barbearia_id)
        
        # Processar configuração para cada dia
        nova_config = {}
        dias_semana = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for dia in dias_semana:
            ativo = request.form.get(f'{dia}_ativo') == 'on'
            horarios = []
            
            # Processar horários para este dia
            for i in range(1, 25):  # Máximo 24 horários por dia
                horario = request.form.get(f'{dia}_horario_{i}')
                if horario and horario.strip():
                    horarios.append(horario.strip())
            
            nova_config[dia] = {
                'ativo': ativo,
                'horarios': sorted(horarios) if horarios else []
            }
        
        config_semana.set_config(nova_config)
        db.session.commit()
        
        flash('Configuração da semana atualizada com sucesso!', 'success')
        return redirect(url_for('admin_disponibilidade'))
    
    # GET - mostrar formulário para a semana
    barbearia_id = get_current_barbearia_id()
    config_semana = DisponibilidadeSemanal.get_ou_criar_semana(data_inicio, barbearia_id)
    config = config_semana.get_config()
    
    data_fim = data_obj + timedelta(days=6)
    
    dias_opcoes = [
        ('monday', 'Segunda-feira'),
        ('tuesday', 'Terça-feira'),
        ('wednesday', 'Quarta-feira'),
        ('thursday', 'Quinta-feira'),
        ('friday', 'Sexta-feira'),
        ('saturday', 'Sábado'),
        ('sunday', 'Domingo')
    ]
    
    return render_template('admin/disponibilidade_semana.html', 
                         config=config,
                         data_inicio=data_obj,
                         data_fim=data_fim,
                         dias_opcoes=dias_opcoes,
                         barbearia=get_current_barbearia())

@app.route('/admin_home')
def admin_home():
    return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))

@app.route('/clientes', methods=['GET','POST'])
def clientes():
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    if request.method == 'POST':
        nome = request.form.get('nome','').strip(); email = request.form.get('email','').strip()
        apelido = request.form.get('apelido','').strip()
        if not nome or not email: flash('Preencha campos!', 'warning'); return redirect(url_for('clientes'))
        if Usuario.query.filter_by(email=email).first(): flash('Email já cadastrado!', 'warning'); return redirect(url_for('clientes'))
        
        # Criar usuário
        novo = Usuario(nome=nome, apelido=apelido, email=email, senha=generate_password_hash('senha123'), tipo_conta='cliente', ativo=True)
        db.session.add(novo)
        db.session.flush() # Para pegar o ID do novo usuário
        
        # Vincular à barbearia atual
        vinculo = UsuarioBarbearia(usuario_id=novo.id, barbearia_id=get_current_barbearia_id(), role='cliente')
        db.session.add(vinculo)
        
        db.session.commit()
        flash('Cliente adicionado!', 'success')
        return redirect(url_for('clientes'))
    barbearia_id = get_current_barbearia_id()
    clientes_list = db.session.query(Usuario).join(UsuarioBarbearia).filter(
        UsuarioBarbearia.barbearia_id == barbearia_id,
        UsuarioBarbearia.role == 'cliente'
    ).all()
    return render_template('cliente/clientes.html', usuarios=clientes_list, barbearia=get_current_barbearia())

@app.route('/servicos', methods=['GET','POST'])
def servicos():
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    if request.method == 'POST':
        nome = request.form.get('nome','').strip(); preco_str = request.form.get('preco','').strip()
        duracao_str = request.form.get('duracao', '30').strip()
        if not nome or not preco_str: flash('Preencha campos!', 'warning'); return redirect(url_for('servicos'))
        try: preco = float(preco_str); duracao = int(duracao_str)
        except ValueError: flash('Preço ou duração inválidos!', 'danger'); return redirect(url_for('servicos'))
        barbearia_id = get_current_barbearia_id()
        novo = Servico(nome=nome, preco=preco, duracao=duracao, barbearia_id=barbearia_id); db.session.add(novo); db.session.commit(); flash('Serviço adicionado!', 'success'); return redirect(url_for('servicos'))
    barbearia_id = get_current_barbearia_id()
    servicos_list = Servico.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()
    return render_template('cliente/servicos.html', servicos=servicos_list, barbearia=get_current_barbearia())

@app.route('/deletar_cliente/<string:cliente_uuid>')
def deletar_cliente(cliente_uuid):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    cliente = Usuario.query.filter_by(uuid=cliente_uuid).first_or_404()
    reservas_cliente = Reserva.query.filter_by(cliente_id=cliente.id).all()
    if reservas_cliente:
        flash(f'Não é possível deletar "{cliente.nome}". Possui {len(reservas_cliente)} reservas ativas.', 'danger')
        return redirect(url_for('clientes'))
    
    # Deletar todas as assinaturas de plano do cliente antes de deletar o cliente
    assinaturas_cliente = AssinaturaPlano.query.filter_by(cliente_id=cliente.id).all()
    for assinatura in assinaturas_cliente:
        db.session.delete(assinatura)
    
    # Remover vínculos com barbearias
    UsuarioBarbearia.query.filter_by(usuario_id=cliente.id).delete()
    
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('clientes'))

@app.route('/editar_cliente/<string:cliente_uuid>', methods=['POST'])
def editar_cliente(cliente_uuid):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
        
    cliente = Usuario.query.filter_by(uuid=cliente_uuid).first_or_404()
    apelido = request.form.get('apelido', '').strip()
    nome = request.form.get('nome', '').strip()
    telefone = request.form.get('telefone', '').strip()
    
    if nome:
        cliente.nome = nome
    cliente.apelido = apelido
    if telefone:
        cliente.telefone = telefone
        
    db.session.commit()
    flash('Dados do cliente atualizados!', 'success')
    return redirect(url_for('clientes'))

@app.route('/deletar_servico/<string:servico_uuid>')
def deletar_servico(servico_uuid):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    servico = Servico.query.filter_by(uuid=servico_uuid).first_or_404()
    reservas_associadas = Reserva.query.filter_by(servico_id=servico.id).all()
    if reservas_associadas:
        flash(f'Não é possível deletar "{servico.nome}". Possui {len(reservas_associadas)} reservas ativas.', 'danger')
        return redirect(url_for('servicos'))
    db.session.delete(servico); db.session.commit()
    flash(f'Serviço "{servico.nome}" deletado!', 'success')
    return redirect(url_for('servicos'))


@app.route('/editar_servico/<string:servico_uuid>', methods=['GET','POST'])
def editar_servico(servico_uuid):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))

    servico = Servico.query.filter_by(uuid=servico_uuid).first_or_404()
    if request.method == 'POST':
        nome = request.form.get('nome','').strip(); preco_str = request.form.get('preco','').strip()
        duracao_str = request.form.get('duracao', str(servico.duracao)).strip()
        if not nome or not preco_str:
            flash('Preencha campos!', 'warning'); return redirect(url_for('editar_servico', servico_uuid=servico_uuid))
        try:
            preco = float(preco_str); duracao = int(duracao_str)
        except ValueError:
            flash('Preço ou duração inválidos!', 'danger'); return redirect(url_for('editar_servico', servico_uuid=servico_uuid))
        servico.nome = nome
        servico.preco = preco
        servico.duracao = duracao
        db.session.commit()
        flash('Serviço atualizado!', 'success')
        return redirect(url_for('servicos'))

    return render_template('cliente/editar_servico.html', servico=servico, barbearia=get_current_barbearia())

@app.route('/<slug>/api/agendamentos_hoje')
def api_agendamentos_hoje(slug):
    """API para buscar agendamentos de hoje em tempo real"""
    try:
        if 'usuario_id' not in session:
            print("⚠️ API: Usuário não autenticado")
            return jsonify({'error': 'Não autorizado'}), 401
        
        barbearia = Barbearia.query.filter_by(slug=slug).first()
        if not barbearia:
            print(f"⚠️ API: Barbearia não encontrada - slug: {slug}")
            return jsonify({'error': 'Barbearia não encontrada'}), 404
        
        from datetime import datetime
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # BUSCAR TODAS AS RESERVAS PRIMEIRO PARA DEBUG
        todas_reservas = Reserva.query.filter_by(barbearia_id=barbearia.id).all()
        print(f"📊 DEBUG: Total de reservas na barbearia: {len(todas_reservas)}")
        for r in todas_reservas:
            print(f"   - Reserva ID {r.id}: data={r.data}, hora={r.hora_inicio}, cliente={r.cliente.nome if r.cliente else 'N/A'}")
        
        reservas = Reserva.query.filter_by(
            barbearia_id=barbearia.id,
            data=hoje
        ).filter(
            Reserva.status != 'cancelada'
        ).all()
        
        print(f"✅ API: Encontradas {len(reservas)} reservas para hoje ({hoje}) na barbearia {barbearia.nome}")
        
        result = []
        for r in reservas:
            # Verificar se o cliente tem plano ativo
            tem_plano = False
            plano_nome = None
            if r.cliente:
                assinatura_ativa = AssinaturaPlano.query.join(
                    PlanoMensal, AssinaturaPlano.plano_id == PlanoMensal.id
                ).filter(
                    AssinaturaPlano.cliente_id == r.cliente_id,
                    AssinaturaPlano.status == 'ativa',
                    PlanoMensal.barbearia_id == barbearia.id
                ).first()
                
                if assinatura_ativa:
                    tem_plano = True
                    plano_nome = assinatura_ativa.plano.nome
            
            result.append({
                'id': r.id,
                'uuid': r.uuid,
                'cliente_id': r.cliente_id,
                'cliente_nome': r.cliente.nome if r.cliente else 'Cliente Desconhecido',
                'cliente_telefone': r.cliente.telefone if r.cliente and r.cliente.telefone else 'Não informado',
                'tem_plano': tem_plano,
                'plano_nome': plano_nome,
                'servico_id': r.servico_id,
                'servico_nome': r.servico.nome if r.servico else 'Serviço N/A',
                'servico_duracao': r.servico.duracao if r.servico else 30,
                'servico_preco': r.servico.preco if r.servico else 0,
                'data': r.data,
                'hora_inicio': r.hora_inicio,
                'hora_fim': r.hora_fim,
                'status': r.status
            })
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ API Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/<slug>/api/agendamentos_todos')
def api_agendamentos_todos(slug):
    """API para buscar agendamentos. Suporta filtro por status para otimização."""
    try:
        print(f"🔵 API agendamentos_todos chamada para slug: {slug}")
        
        if 'usuario_id' not in session:
            print("❌ API: Usuário não autenticado")
            return jsonify({'error': 'Não autorizado'}), 401
        
        barbearia = Barbearia.query.filter_by(slug=slug).first()
        if not barbearia:
            print(f"❌ API: Barbearia não encontrada com slug: {slug}")
            return jsonify({'error': 'Barbearia não encontrada'}), 404
        
        # Filtros de otimização
        filtro_status = request.args.get('status') # 'ativos' = agendada/confirmada
        
        query = Reserva.query.filter_by(barbearia_id=barbearia.id)
        
        if filtro_status == 'ativos':
            # Retorna apenas novos/pendentes + o que foi concluído hoje para sincronizar
            hoje = datetime.now().strftime('%Y-%m-%d')
            query = query.filter(
                (Reserva.status.in_(['agendada', 'confirmada'])) | 
                ((Reserva.status == 'concluida') & (Reserva.data == hoje))
            )
        else:
            # Padrão: tudo exceto cancelado
            query = query.filter(Reserva.status != 'cancelada')
            
        reservas = query.order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
        
        print(f"✅ API: Encontradas {len(reservas)} reservas (Filtro: {filtro_status})")
        
        result = []
        for r in reservas:
            # Verificar se o cliente tem plano ativo
            tem_plano = False
            plano_nome = None
            if r.cliente:
                assinatura_ativa = AssinaturaPlano.query.join(
                    PlanoMensal, AssinaturaPlano.plano_id == PlanoMensal.id
                ).filter(
                    AssinaturaPlano.cliente_id == r.cliente_id,
                    AssinaturaPlano.status == 'ativa',
                    PlanoMensal.barbearia_id == barbearia.id
                ).first()
                
                if assinatura_ativa:
                    tem_plano = True
                    plano_nome = assinatura_ativa.plano.nome
            
            result.append({
                'id': r.id,
                'uuid': r.uuid,
                'cliente_id': r.cliente_id,
                'cliente_nome': r.cliente.nome if r.cliente else 'Cliente Desconhecido',
                'cliente_telefone': r.cliente.telefone if r.cliente and r.cliente.telefone else 'Não informado',
                'tem_plano': tem_plano,
                'plano_nome': plano_nome,
                'servico_id': r.servico_id,
                'servico_nome': r.servico.nome if r.servico else 'Serviço N/A',
                'servico_duracao': r.servico.duracao if r.servico else 30,
                'servico_preco': r.servico.preco if r.servico else 0,
                'data': r.data,
                'hora_inicio': r.hora_inicio,
                'hora_fim': r.hora_fim,
                'status': r.status
            })
        
        print(f"📦 API: Retornando {len(result)} agendamentos")
        return jsonify(result)
    except Exception as e:
        print(f"❌ API Erro agendamentos_todos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/<slug>/api/reservas_cliente')
def api_reservas_cliente(slug):
    """API para buscar reservas do cliente com filtro"""
    try:
        print(f"🔵 API reservas_cliente chamada para slug: {slug}")
        
        if 'usuario_id' not in session:
            print("❌ API: Usuário não autenticado")
            return jsonify({'error': 'Não autorizado'}), 401
        
        barbearia = Barbearia.query.filter_by(slug=slug).first()
        if not barbearia:
            print(f"❌ API: Barbearia não encontrada com slug: {slug}")
            return jsonify({'error': 'Barbearia não encontrada'}), 404
        
        filtro = request.args.get('filtro', 'pendentes')
        print(f"✅ API: Filtro solicitado: {filtro}")
        
        # Definir status baseado no filtro
        if filtro == 'pendentes':
            status_filter = Reserva.status.in_(['agendada', 'confirmada'])
        elif filtro == 'atendidos':
            status_filter = Reserva.status == 'concluida'
        else:
            status_filter = Reserva.status != 'cancelada'  # fallback
        
        reservas = Reserva.query.filter_by(
            barbearia_id=barbearia.id,
            cliente_id=session['usuario_id']
        ).filter(status_filter).order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
        
        print(f"✅ API: Encontradas {len(reservas)} reservas para cliente {session['usuario_id']} com filtro {filtro}")
        
        result = []
        for r in reservas:
            result.append({
                'id': r.id,
                'servico': r.servico.nome if r.servico else 'Serviço N/A',
                'preco': r.servico.preco if r.servico else 0,
                'data': r.data,
                'hora_inicio': r.hora_inicio,
                'hora_fim': r.hora_fim,
                'status': r.status
            })
        
        return jsonify({'reservas': result})
    except Exception as e:
        print(f"❌ API Erro reservas_cliente: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/deletar_agendamento/<string:agendamento_uuid>')
def deletar_agendamento(agendamento_uuid):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    reserva = Reserva.query.filter_by(uuid=agendamento_uuid).first_or_404()
    db.session.delete(reserva); db.session.commit()
    flash('Agendamento deletado!', 'success')
    return redirect(url_for('admin_agendamentos'))

@app.route('/perfil', methods=['GET','POST'])
def perfil():
    if 'usuario_id' not in session:
        flash('Faça login para acessar o perfil.', 'warning')
        return redirect(url_for('login', slug=get_current_barbearia_slug()))

    usuario = Usuario.query.get(session['usuario_id'])

    if request.method == 'POST':
        novo_nome = request.form.get('nome', usuario.nome).strip()
        nova_senha = request.form.get('nova_senha', '').strip()

        if novo_nome:
            usuario.nome = novo_nome
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)

        db.session.commit()
        session['usuario_nome'] = usuario.nome
        flash('Perfil atualizado!', 'success')
        return redirect(url_for('perfil'))

    # Tenta renderizar cliente/perfil.html se existir, caso contrário redireciona ao dashboard do cliente
    from tenant import get_current_barbearia
    barbearia = get_current_barbearia()

    # Buscar assinatura ativa do usuário (se houver)
    assinatura_ativa = AssinaturaPlano.query.filter_by(cliente_id=usuario.id, status='ativa').join(PlanoMensal).first()

    try:
        return render_template('cliente/perfil.html', usuario=usuario, barbearia=barbearia, assinatura_ativa=assinatura_ativa)
    except Exception:
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))

# Rota de debug que lista templates (útil para verificar estrutura)
@app.route('/_templates_debug')
def templates_debug():
    try:
        lista = sorted(app.jinja_env.list_templates())
    except Exception:
        lista = []
        for root, _, files in os.walk(TEMPLATES_DIR):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), TEMPLATES_DIR).replace('\\','/')
                lista.append(rel)
    return jsonify({'templates': lista})

@app.route('/barbearias')
def listar_barbearias():
    """Redireciona para a página principal que já lista as barbearias"""
    return redirect(url_for('admin_index'))

@app.route('/b/<slug>')
def acessar_barbearia(slug):
    """Acesso direto a uma barbearia pelo slug"""
    return redirect(f'/?b={slug}')

@app.route('/super_admin')
def super_admin_redirect():
    """Redirect para login do super admin"""
    return redirect(url_for('super_admin_login'))

@app.route('/super_admin/login', methods=['GET', 'POST'])
def super_admin_login():
    """Login específico para super admin"""
    # Se já está logado como super admin, redireciona para o painel da primeira barbearia ativa (se houver)
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario and usuario.tipo_conta == 'super_admin':
            return redirect(url_for('super_admin_dashboard'))
    
    if request.method == 'POST':
        # Rate limiting por IP
        client_ip = get_client_ip()
        allowed, remaining, lockout_seconds = check_rate_limit(client_ip)
        
        if not allowed:
            minutes = lockout_seconds // 60
            flash(f'Muitas tentativas de login. Tente novamente em {minutes} minutos.', 'error')
            audit_log('super_admin_login_blocked', details={'ip': client_ip})
            return render_template('super_admin/login.html')
        
        login_input = sanitize_input(request.form.get('email', '').strip())
        senha = request.form.get('senha', '')
        
        if not login_input or not senha:
            flash('Usuário e senha são obrigatórios!', 'error')
            return render_template('super_admin/login.html')
        
        # Buscar super admin por username ou email
        usuario = Usuario.query.filter(
            ((Usuario.username == login_input) | (Usuario.email == login_input)),
            Usuario.tipo_conta == 'super_admin',
            Usuario.ativo == True
        ).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            # Limpar sessão anterior
            session.clear()
            
            # Criar nova sessão
            session['usuario_id'] = usuario.id
            session['user_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            session['tipo_conta'] = 'super_admin'
            session.permanent = True
            
            # Registrar sucesso
            record_login_attempt(client_ip, success=True)
            audit_log('super_admin_login_success', user_id=usuario.id, details={'username': usuario.username})
            
            flash('Super Admin logado com sucesso!', 'success')
            return redirect(url_for('super_admin_dashboard'))
        else:
            # Login falhou
            record_login_attempt(client_ip, success=False)
            if usuario:
                audit_log('super_admin_login_failed', user_id=usuario.id, details={'reason': 'wrong_password'})
            else:
                audit_log('super_admin_login_failed', details={'reason': 'user_not_found', 'login_input': login_input[:20]})
            
            if remaining <= 2:
                flash(f'Credenciais inválidas! Você tem mais {remaining} tentativas.', 'error')
            else:
                flash('Credenciais inválidas para Super Admin!', 'error')
    
    return render_template('super_admin/login.html')

@app.route('/super_admin/dashboard')
@require_super_admin
def super_admin_dashboard():
    """Dashboard do super admin com visão global"""
    # Estatísticas globais
    total_barbearias = Barbearia.query.filter_by(ativa=True).count()
    total_usuarios = Usuario.query.filter_by(ativo=True).count()
    total_servicos = Servico.query.filter_by(ativo=True).count()
    total_reservas = Reserva.query.count()
    
    # Barbearias com detalhes
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    barbearias_stats = []
    
    for barbearia in barbearias:
        usuarios_barbearia = db.session.query(Usuario).join(UsuarioBarbearia).filter(
            UsuarioBarbearia.barbearia_id == barbearia.id
        ).count()
        servicos_barbearia = Servico.query.filter_by(barbearia_id=barbearia.id, ativo=True).count()
        reservas_barbearia = Reserva.query.filter_by(barbearia_id=barbearia.id).count()
        
        barbearias_stats.append({
            'barbearia': barbearia,
            'usuarios': usuarios_barbearia,
            'servicos': servicos_barbearia,
            'reservas': reservas_barbearia
        })
    
    # Usuários por tipo
    usuarios_stats = {
        'super_admin': Usuario.query.filter_by(tipo_conta='super_admin', ativo=True).count(),
        'admin_barbearia': Usuario.query.filter_by(tipo_conta='admin_barbearia', ativo=True).count(),
        'barbeiro': Usuario.query.filter_by(tipo_conta='barbeiro', ativo=True).count(),
        'cliente': Usuario.query.filter_by(tipo_conta='cliente', ativo=True).count()
    }
    
    return render_template('super_admin/dashboard.html',
                         total_barbearias=total_barbearias,
                         total_usuarios=total_usuarios,
                         total_servicos=total_servicos,
                         total_reservas=total_reservas,
                         barbearias_stats=barbearias_stats,
                         usuarios_stats=usuarios_stats)

@app.route('/super_admin/barbearias')
@require_super_admin
def super_admin_barbearias():
    """Gestão de todas as barbearias"""
    barbearias = Barbearia.query.all()
    return render_template('super_admin/barbearias.html', barbearias=barbearias)

@app.route('/super_admin/usuario/novo', methods=['GET', 'POST'])
@require_super_admin
def super_admin_novo_usuario():
    """Criar novo usuário pelo super admin"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        telefone = request.form.get('telefone', '').strip()
        tipo_conta = request.form.get('tipo_conta', 'cliente')
        # Bloquear criação de super_admin por esta rota
        if tipo_conta == 'super_admin':
            tipo_conta = 'cliente'
            
        barbearia_id = request.form.get('barbearia_id')
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not nome or not username or not senha:
            flash('Nome, usuário e senha são obrigatórios!', 'error')
            return redirect(url_for('super_admin_novo_usuario'))

        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'error')
            return redirect(url_for('super_admin_novo_usuario'))

        if Usuario.query.filter_by(username=username).first():
            flash('Nome de usuário já cadastrado!', 'error')
            return redirect(url_for('super_admin_novo_usuario'))

        if email and Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('super_admin_novo_usuario'))

        # Criar usuário
        novo_usuario = Usuario(
            nome=nome,
            username=username,
            email=email if email else None,
            telefone=telefone,
            senha=generate_password_hash(senha),
            tipo_conta=tipo_conta,
            ativo=True
        )
        db.session.add(novo_usuario)
        db.session.commit()

        # Vincular à barbearia se necessário
        if tipo_conta != 'super_admin' and barbearia_id:
            role = 'cliente'
            if tipo_conta == 'admin_barbearia':
                role = 'admin'
            elif tipo_conta == 'barbeiro':
                role = 'barbeiro'
            
            vinculo = UsuarioBarbearia(
                usuario_id=novo_usuario.id,
                barbearia_id=barbearia_id,
                role=role,
                ativo=True
            )
            db.session.add(vinculo)
            db.session.commit()

        flash(f'Usuário {nome} criado com sucesso!', 'success')
        return redirect(url_for('super_admin_usuarios'))

    barbearias = Barbearia.query.filter_by(ativa=True).all()
    return render_template('super_admin/usuario_form.html', barbearias=barbearias)

@app.route('/super_admin/usuarios')
@require_super_admin
def super_admin_usuarios():
    """Gestão de todos os usuários do sistema"""
    usuarios = Usuario.query.filter_by(ativo=True).all()
    
    # Organizar usuários por barbearia
    usuarios_organizados = {}
    for usuario in usuarios:
        if usuario.tipo_conta == 'super_admin':
            if 'Sistema' not in usuarios_organizados:
                usuarios_organizados['Sistema'] = []
            usuarios_organizados['Sistema'].append({
                'usuario': usuario,
                'vinculos': []
            })
        else:
            vinculos = UsuarioBarbearia.query.filter_by(usuario_id=usuario.id, ativo=True).all()
            for vinculo in vinculos:
                barbearia_nome = vinculo.barbearia.nome
                if barbearia_nome not in usuarios_organizados:
                    usuarios_organizados[barbearia_nome] = []
                
                # Verificar se usuário já está na lista desta barbearia
                usuario_existente = None
                for item in usuarios_organizados[barbearia_nome]:
                    if item['usuario'].id == usuario.id:
                        usuario_existente = item
                        break
                
                if usuario_existente:
                    usuario_existente['vinculos'].append(vinculo)
                else:
                    usuarios_organizados[barbearia_nome].append({
                        'usuario': usuario,
                        'vinculos': [vinculo]
                    })
    
    return render_template('super_admin/usuarios.html', usuarios_organizados=usuarios_organizados)

@app.route('/super_admin/relatorios')
@require_super_admin
def super_admin_relatorios():
    """Relatórios globais do sistema"""
    # Relatório de crescimento por barbearia
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    relatorio_crescimento = []
    
    for barbearia in barbearias:
        usuarios_mes = db.session.query(Usuario).join(UsuarioBarbearia).filter(
            UsuarioBarbearia.barbearia_id == barbearia.id,
            Usuario.data_criacao >= '2025-11-01'
        ).count()
        
        reservas_mes = Reserva.query.filter(
            Reserva.barbearia_id == barbearia.id,
            Reserva.data_criacao >= '2025-11-01'
        ).count()
        
        relatorio_crescimento.append({
            'barbearia': barbearia,
            'novos_usuarios': usuarios_mes,
            'reservas_mes': reservas_mes
        })
    
    # Top serviços por preço
    top_servicos = Servico.query.filter_by(ativo=True).order_by(Servico.preco.desc()).limit(10).all()
    
    return render_template('super_admin/relatorios.html',
                         relatorio_crescimento=relatorio_crescimento,
                         top_servicos=top_servicos)

# ==================== ROTAS DE PLANOS DO SUPER ADMIN ====================

@app.route('/super_admin/planos')
@require_super_admin
def super_admin_planos():
    """Gerenciar planos de todas as barbearias"""
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    
    # Criar estrutura de dados com barbearias e seus planos
    dados_barbearias = []
    for barbearia in barbearias:
        planos = PlanoMensal.query.filter_by(barbearia_id=barbearia.id).all()
        dados_barbearias.append({
            'barbearia': barbearia,
            'planos': planos,
            'total_planos': len(planos),
            'planos_ativos': len([p for p in planos if p.ativo])
        })
    
    return render_template('super_admin/planos.html', dados_barbearias=dados_barbearias)

@app.route('/super_admin/plano/criar/<string:barbearia_uuid>', methods=['GET', 'POST'])
@require_super_admin
def super_admin_criar_plano(barbearia_uuid):
    """Criar novo plano para uma barbearia"""
    barbearia = Barbearia.query.filter_by(uuid=barbearia_uuid).first_or_404()
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        preco = request.form.get('preco', '').strip()
        atendimentos_mes = request.form.get('atendimentos_mes', '').strip()
        
        # Benefícios (um por linha no textarea)
        beneficios_text = request.form.get('beneficios', '').strip()
        beneficios = [b.strip() for b in beneficios_text.split('\n') if b.strip()]
        
        # Validações
        if not nome or not preco or not atendimentos_mes:
            flash('Nome, preço e quantidade de atendimentos são obrigatórios!', 'error')
            return redirect(request.url)
        
        try:
            preco_float = float(preco.replace(',', '.'))
            atendimentos_int = int(atendimentos_mes)
            
            # Criar plano
            novo_plano = PlanoMensal(
                barbearia_id=barbearia.id,
                nome=nome,
                descricao=descricao,
                preco=preco_float,
                atendimentos_mes=atendimentos_int,
                ativo=True
            )
            novo_plano.set_beneficios(beneficios)
            
            db.session.add(novo_plano)
            db.session.commit()
            
            flash(f'Plano "{nome}" criado com sucesso!', 'success')
            return redirect(url_for('super_admin_planos'))
            
        except ValueError:
            flash('Preço e atendimentos devem ser números válidos!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar plano: {str(e)}', 'error')
    
    return render_template('super_admin/plano_form.html', barbearia=barbearia, plano=None)

@app.route('/super_admin/plano/<string:plano_uuid>/editar', methods=['GET', 'POST'])
@require_super_admin
def super_admin_editar_plano(plano_uuid):
    """Editar plano existente"""
    plano = PlanoMensal.query.filter_by(uuid=plano_uuid).first_or_404()
    barbearia = plano.barbearia
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        preco = request.form.get('preco', '').strip()
        atendimentos_mes = request.form.get('atendimentos_mes', '').strip()
        ativo = request.form.get('ativo') == 'on'
        
        # Benefícios (um por linha no textarea)
        beneficios_text = request.form.get('beneficios', '').strip()
        beneficios = [b.strip() for b in beneficios_text.split('\n') if b.strip()]
        
        # Validações
        if not nome or not preco or not atendimentos_mes:
            flash('Nome, preço e quantidade de atendimentos são obrigatórios!', 'error')
            return redirect(request.url)
        
        try:
            preco_float = float(preco.replace(',', '.'))
            atendimentos_int = int(atendimentos_mes)
            
            # Atualizar plano
            plano.nome = nome
            plano.descricao = descricao
            plano.preco = preco_float
            plano.atendimentos_mes = atendimentos_int
            plano.ativo = ativo
            plano.set_beneficios(beneficios)
            
            db.session.commit()
            
            flash(f'Plano "{nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('super_admin_planos'))
            
        except ValueError:
            flash('Preço e atendimentos devem ser números válidos!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar plano: {str(e)}', 'error')
    
    return render_template('super_admin/plano_form.html', barbearia=barbearia, plano=plano)

@app.route('/super_admin/plano/<string:plano_uuid>/excluir', methods=['POST'])
@require_super_admin
def super_admin_excluir_plano(plano_uuid):
    """Excluir permanentemente um plano"""
    plano = PlanoMensal.query.filter_by(uuid=plano_uuid).first_or_404()
    nome = plano.nome
    
    try:
        db.session.delete(plano)
        db.session.commit()
        flash(f'Plano "{nome}" excluído permanentemente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir plano: {str(e)}', 'error')
    
    return redirect(url_for('super_admin_planos'))

# ==================== FIM ROTAS DE PLANOS ====================

@app.route('/super_admin/barbearia/<string:barbearia_uuid>/editar', methods=['GET', 'POST'])
@require_super_admin
def super_admin_editar_barbearia(barbearia_uuid):
    """Editar dados de uma barbearia"""
    barbearia = Barbearia.query.filter_by(uuid=barbearia_uuid).first_or_404()
    
    if request.method == 'POST':
        # Atualizar dados da barbearia
        nome = request.form.get('nome', '').strip()
        slug = request.form.get('slug', '').strip()
        cnpj = request.form.get('cnpj', '').strip()
        telefone = request.form.get('telefone', '').strip()
        endereco = request.form.get('endereco', '').strip()
        ativa = request.form.get('ativa') == 'on'
        
        # Upload de logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Gerar nome seguro para o arquivo
                filename = secure_filename(file.filename)
                # Adicionar slug da barbearia ao nome para evitar conflitos
                nome_arquivo = f"{slug}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)
                
                # Remover logo anterior se existir
                if barbearia.logo:
                    logo_antiga = os.path.join(app.config['UPLOAD_FOLDER'], barbearia.logo)
                    if os.path.exists(logo_antiga):
                        try:
                            os.remove(logo_antiga)
                        except:
                            pass
                
                # Salvar nova logo
                file.save(filepath)
                barbearia.logo = nome_arquivo
        
        # Validações básicas
        if not nome:
            flash('Nome é obrigatório!', 'error')
            return redirect(request.url)
        
        if not slug:
            flash('Slug é obrigatório!', 'error')
            return redirect(request.url)
        
        # Verificar se slug já existe (exceto para a própria barbearia)
        slug_existente = Barbearia.query.filter(
            Barbearia.slug == slug,
            Barbearia.id != barbearia.id
        ).first()
        
        if slug_existente:
            flash('Este slug já está sendo usado por outra barbearia!', 'error')
            return redirect(request.url)
        
        # Verificar se CNPJ já existe (se fornecido e diferente do atual)
        if cnpj and cnpj != barbearia.cnpj:
            cnpj_existente = Barbearia.query.filter(
                Barbearia.cnpj == cnpj,
                Barbearia.id != barbearia.id
            ).first()
            
            if cnpj_existente:
                flash('Este CNPJ já está sendo usado por outra barbearia!', 'error')
                return redirect(request.url)
        
        # Campos de personalização visual
        hero_titulo = request.form.get('hero_titulo', '').strip()
        hero_subtitulo = request.form.get('hero_subtitulo', '').strip()
        slogan = request.form.get('slogan', '').strip()
        cor_primaria = request.form.get('cor_primaria', '').strip()
        cor_secundaria = request.form.get('cor_secundaria', '').strip()
        cor_texto = request.form.get('cor_texto', '').strip()
        
        # Cards de serviços
        card1_icone = request.form.get('card1_icone', '').strip()
        card1_titulo = request.form.get('card1_titulo', '').strip()
        card1_descricao = request.form.get('card1_descricao', '').strip()
        
        card2_icone = request.form.get('card2_icone', '').strip()
        card2_titulo = request.form.get('card2_titulo', '').strip()
        card2_descricao = request.form.get('card2_descricao', '').strip()
        
        card3_icone = request.form.get('card3_icone', '').strip()
        card3_titulo = request.form.get('card3_titulo', '').strip()
        card3_descricao = request.form.get('card3_descricao', '').strip()
        
        card4_icone = request.form.get('card4_icone', '').strip()
        card4_titulo = request.form.get('card4_titulo', '').strip()
        card4_descricao = request.form.get('card4_descricao', '').strip()

        # Estatísticas
        stat1_valor = request.form.get('stat1_valor', '').strip()
        stat1_label = request.form.get('stat1_label', '').strip()
        
        stat2_valor = request.form.get('stat2_valor', '').strip()
        stat2_label = request.form.get('stat2_label', '').strip()
        
        stat3_valor = request.form.get('stat3_valor', '').strip()
        stat3_label = request.form.get('stat3_label', '').strip()
        
        stat4_valor = request.form.get('stat4_valor', '').strip()
        stat4_label = request.form.get('stat4_label', '').strip()

        # Capacidade (Vagas por horário)
        vagas = request.form.get('vagas_por_horario', '1')
        config = barbearia.get_configuracoes()
        config['vagas_por_horario'] = int(vagas) if vagas.isdigit() else 1
        barbearia.set_configuracoes(config)
        
        # Atualizar os dados
        barbearia.nome = nome
        barbearia.slug = slug
        barbearia.cnpj = cnpj if cnpj else None
        barbearia.telefone = telefone if telefone else None
        barbearia.endereco = endereco if endereco else None
        barbearia.ativa = ativa
        
        # Atualizar personalização visual
        barbearia.hero_titulo = hero_titulo if hero_titulo else None
        barbearia.hero_subtitulo = hero_subtitulo if hero_subtitulo else None
        barbearia.slogan = slogan if slogan else None
        barbearia.cor_primaria = cor_primaria if cor_primaria else '#8b5cf6'
        barbearia.cor_secundaria = cor_secundaria if cor_secundaria else '#A78BFA'
        barbearia.cor_texto = cor_texto if cor_texto else '#1f2937'
        
        # Atualizar cards
        barbearia.card1_icone = card1_icone if card1_icone else None
        barbearia.card1_titulo = card1_titulo if card1_titulo else None
        barbearia.card1_descricao = card1_descricao if card1_descricao else None
        
        barbearia.card2_icone = card2_icone if card2_icone else None
        barbearia.card2_titulo = card2_titulo if card2_titulo else None
        barbearia.card2_descricao = card2_descricao if card2_descricao else None
        
        barbearia.card3_icone = card3_icone if card3_icone else None
        barbearia.card3_titulo = card3_titulo if card3_titulo else None
        barbearia.card3_descricao = card3_descricao if card3_descricao else None
        
        barbearia.card4_icone = card4_icone if card4_icone else None
        barbearia.card4_titulo = card4_titulo if card4_titulo else None
        barbearia.card4_descricao = card4_descricao if card4_descricao else None
        
        # Atualizar estatísticas
        barbearia.stat1_valor = stat1_valor if stat1_valor else None
        barbearia.stat1_label = stat1_label if stat1_label else None
        
        barbearia.stat2_valor = stat2_valor if stat2_valor else None
        barbearia.stat2_label = stat2_label if stat2_label else None
        
        barbearia.stat3_valor = stat3_valor if stat3_valor else None
        barbearia.stat3_label = stat3_label if stat3_label else None
        
        barbearia.stat4_valor = stat4_valor if stat4_valor else None
        barbearia.stat4_label = stat4_label if stat4_label else None
        
        try:
            db.session.commit()
            flash('Barbearia atualizada com sucesso!', 'success')
            return redirect(url_for('super_admin_barbearias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar barbearia: {str(e)}', 'error')
    
    return render_template('super_admin/editar_barbearia.html', barbearia=barbearia)

@app.route('/super_admin/barbearia/nova', methods=['GET', 'POST'])
@require_super_admin
def super_admin_nova_barbearia():
    """Criar nova barbearia"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        slug = request.form.get('slug', '').strip()
        cnpj = request.form.get('cnpj', '').strip()
        telefone = request.form.get('telefone', '').strip()
        endereco = request.form.get('endereco', '').strip()
        
        # Validações básicas
        if not nome:
            flash('Nome é obrigatório!', 'error')
            return redirect(request.url)
        
        if not slug:
            flash('Slug é obrigatório!', 'error')
            return redirect(request.url)
        
        # Verificar se slug já existe
        if Barbearia.query.filter_by(slug=slug).first():
            flash('Este slug já está sendo usado!', 'error')
            return redirect(request.url)
        
        # Verificar se CNPJ já existe (se fornecido)
        if cnpj and Barbearia.query.filter_by(cnpj=cnpj).first():
            flash('Este CNPJ já está sendo usado!', 'error')
            return redirect(request.url)
        
        # Upload de logo
        logo_filename = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Adicionar slug ao nome para evitar conflitos
                logo_filename = f"{slug}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
                file.save(filepath)
        
        # Criar nova barbearia com valores padrão de personalização
        nova_barbearia = Barbearia(
            nome=nome,
            slug=slug,
            cnpj=cnpj if cnpj else None,
            telefone=telefone if telefone else None,
            endereco=endereco if endereco else None,
            logo=logo_filename,
            ativa=True,
            # Valores padrão de personalização
            hero_titulo='Seu visual|no nível máximo',
            hero_subtitulo='Mais que um corte de cabelo, uma experiência completa. Profissionais qualificados, ambiente moderno e atendimento premium.',
            slogan='Estilo e Tradição',
            cor_primaria='#8b5cf6',
            cor_secundaria='#A78BFA',
            cor_texto='#1f2937',
            # Cards padrão
            card1_icone='✂️',
            card1_titulo='Corte masculino',
            card1_descricao='Cortes modernos e clássicos com acabamento perfeito, realizado por barbeiros experientes',
            card2_icone='🧔',
            card2_titulo='Barba completa',
            card2_descricao='Design, aparação e tratamento completo para sua barba ficar impecável',
            card3_icone='💈',
            card3_titulo='Combo premium',
            card3_descricao='Corte + barba + finalização, o pacote completo para você sair renovado',
            card4_icone='📅',
            card4_titulo='Agendamento fácil',
            card4_descricao='Reserve seu horário online de forma rápida e prática, sem complicação',
            # Estatísticas padrão
            stat1_valor='5+',
            stat1_label='Anos de experiência',
            stat2_valor='1000+',
            stat2_label='Clientes satisfeitos',
            stat3_valor='100%',
            stat3_label='Profissionais qualificados',
            stat4_valor='★★★★★',
            stat4_label='Avaliação dos clientes'
        )
        
        # Capacidade (Vagas por horário)
        vagas = request.form.get('vagas_por_horario', '1')
        config_dict = {'vagas_por_horario': int(vagas) if vagas.isdigit() else 1}
        nova_barbearia.set_configuracoes(config_dict)
        
        try:
            db.session.add(nova_barbearia)
            db.session.commit()
            flash('Barbearia criada com sucesso!', 'success')
            return redirect(url_for('super_admin_barbearias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar barbearia: {str(e)}', 'error')
    
    return render_template('super_admin/nova_barbearia.html')

@app.route('/super_admin/barbearia/<string:barbearia_uuid>/deletar', methods=['POST'])
@require_super_admin
def super_admin_deletar_barbearia(barbearia_uuid):
    """Deletar uma barbearia (apenas inativar por segurança)"""
    barbearia = Barbearia.query.filter_by(uuid=barbearia_uuid).first_or_404()
    
    # Por segurança, apenas inativar ao invés de deletar
    barbearia.ativa = False
    
    try:
        db.session.commit()
        flash(f'Barbearia "{barbearia.nome}" foi inativada!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao inativar barbearia: {str(e)}', 'error')
    
    return redirect(url_for('super_admin_barbearias'))

@app.route('/teste-isolamento')
@require_tenant
def teste_isolamento():
    """Página para testar o isolamento multi-tenant"""
    barbearia = get_current_barbearia()
    barbearia_id = get_current_barbearia_id()
    
    # Buscar dados específicos da barbearia atual
    usuarios_barbearia = db.session.query(Usuario).join(UsuarioBarbearia).filter(
        UsuarioBarbearia.barbearia_id == barbearia_id
    ).all()
    
    servicos_barbearia = Servico.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()
    reservas_barbearia = Reserva.query.filter_by(barbearia_id=barbearia_id).all()
    
    # Contar dados para estatísticas
    stats = {
        'total_usuarios': len(usuarios_barbearia),
        'total_servicos': len(servicos_barbearia),
        'total_reservas': len(reservas_barbearia),
        'usuarios_por_role': {},
        'servico_mais_caro': max(servicos_barbearia, key=lambda s: s.preco) if servicos_barbearia else None,
        'servico_mais_barato': min(servicos_barbearia, key=lambda s: s.preco) if servicos_barbearia else None
    }
    
    # Agrupar usuários por role
    for usuario in usuarios_barbearia:
        vinculo = UsuarioBarbearia.query.filter_by(
            usuario_id=usuario.id, 
            barbearia_id=barbearia_id
        ).first()
        if vinculo:
            role = vinculo.role
            if role not in stats['usuarios_por_role']:
                stats['usuarios_por_role'][role] = 0
            stats['usuarios_por_role'][role] += 1
    
    return render_template('teste_isolamento.html', 
                         barbearia=barbearia,
                         usuarios=usuarios_barbearia,
                         servicos=servicos_barbearia,
                         reservas=reservas_barbearia,
                         stats=stats)

@app.route('/<slug>/admin/suporte', methods=['GET', 'POST'])
def admin_suporte(slug):
    """Página de suporte para enviar chamados"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia = get_current_barbearia()
    usuario = Usuario.query.get(session['usuario_id'])
    
    if request.method == 'POST':
        try:
            # Coletar dados do formulário
            aplicacao = request.form.get('aplicacao', 'Minha Barbearia App')
            usuario_nome = request.form.get('usuario', usuario.nome if usuario else 'Admin')
            email = request.form.get('email', usuario.email if usuario else '')
            telefone = request.form.get('telefone', '')
            assunto = request.form.get('assunto', '')
            mensagem = request.form.get('mensagem', '')
            prioridade = request.form.get('prioridade', 'media')
            
            # Validar campos obrigatórios
            if not assunto or not mensagem:
                flash('Assunto e mensagem são obrigatórios', 'error')
                return redirect(request.url)
            
            # Preparar dados para a API
            data = {
                "aplicacao": aplicacao,
                "usuario": usuario_nome,
                "email": email,
                "telefone": telefone,
                "assunto": assunto,
                "mensagem": mensagem,
                "prioridade": prioridade,
                "webhook_url": ""  # Desabilitado - use sincronização manual
            }
            
            # Enviar para a API externa
            response = requests.post(
                "http://localhost:5001/api/v1/suporte",
                headers={"X-API-Key": "barber-connect-api-key-2025"},
                json=data,
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                # Extrair ticket_id da resposta da API
                try:
                    resposta_json = response.json()
                    # A API retorna: {"success": true, "ticket_id": "SUP-...", ...}
                    api_ticket_id = resposta_json.get('ticket_id') or resposta_json.get('id')
                except:
                    api_ticket_id = None
                
                # Salvar chamado no banco local
                barbearia_id = get_current_barbearia_id()
                novo_chamado = Chamado(
                    numero_chamado="TEMP",  # Valor temporário para evitar constraint
                    barbearia_id=barbearia_id,
                    usuario_id=session['usuario_id'],
                    aplicacao=aplicacao,
                    usuario_nome=usuario_nome,
                    email=email,
                    telefone=telefone,
                    assunto=assunto,
                    mensagem=mensagem,
                    prioridade=prioridade,
                    resposta_api=response.text,
                    api_chamado_id=api_ticket_id
                )
                db.session.add(novo_chamado)
                db.session.commit()  # Commit com valor temporário
                
                # Gerar número do chamado baseado no ID e atualizar
                chamado_numero = f"CH{novo_chamado.id:06d}"
                novo_chamado.numero_chamado = chamado_numero
                db.session.commit()  # Commit final com numero correto
                
                if api_ticket_id:
                    flash(f'✅ Chamado enviado com sucesso! Ticket: {api_ticket_id}', 'success')
                else:
                    flash('⚠️ Chamado salvo localmente, mas sem ID da API', 'warning')
                flash(f'Número do chamado: {chamado_numero}', 'info')
            else:
                flash(f'Erro ao enviar chamado: {response.status_code} - {response.text}', 'error')
                
        except requests.exceptions.RequestException as e:
            flash(f'Erro de conexão: {str(e)}', 'error')
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'error')
        
        return redirect(request.url)
    
    return render_template('admin/suporte.html', barbearia=barbearia, usuario=usuario)

@app.route('/<slug>/admin/chamados')
def admin_chamados(slug):
    """Lista os chamados enviados pelo admin"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    barbearia = get_current_barbearia()
    
    # Buscar chamados do admin atual nesta barbearia
    chamados = Chamado.query.filter_by(
        barbearia_id=barbearia_id,
        usuario_id=session['usuario_id']
    ).order_by(Chamado.data_criacao.desc()).all()
    
    return render_template('admin/chamados.html', 
                         barbearia=barbearia, 
                         chamados=chamados)

@app.route('/<slug>/admin/chamados/sincronizar', methods=['POST'])
@csrf.exempt
def sincronizar_chamados_manual(slug):
    """Endpoint para sincronizar chamados manualmente via AJAX"""
    print("\n" + "="*80)
    print(f"🔄 [DEBUG] >>> FUNÇÃO CHAMADA! Slug: {slug}")
    print(f"🔄 [DEBUG] >>> Session: {dict(session)}")
    print(f"🔄 [DEBUG] >>> Request method: {request.method}")
    print("="*80 + "\n")
    
    if 'usuario_id' not in session:
        print("❌ [DEBUG] Usuário não autenticado")
        return jsonify({'success': False, 'error': 'Não autenticado'}), 401
    
    # Verificar se é admin pela sessão
    tipo_conta = session.get('tipo_conta')
    print(f"🔍 [DEBUG] Tipo de conta: {tipo_conta}")
    
    if tipo_conta not in ['admin', 'super_admin']:
        print("❌ [DEBUG] Usuário não é admin")
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    try:
        print("🔄 [DEBUG] Executando sincronização...")
        # Executar sincronização
        sincronizar_chamados_automatica()
        
        print("✅ [DEBUG] Sincronização executada com sucesso!")
        return jsonify({
            'success': True,
            'message': 'Sincronização executada com sucesso!'
        })
    except Exception as e:
        print(f"❌ [DEBUG] Erro na sincronização: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/_endpoints_debug')
def endpoints_debug():
    rules = []
    for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
        rules.append({
            'endpoint': r.endpoint,
            'rule': str(r),
            'methods': sorted([m for m in r.methods if m not in ('HEAD','OPTIONS')])
        })
    return jsonify(rules)

# ---------- WEBHOOK PARA NOTIFICAÇÕES DA API EXTERNA ----------

@app.route('/api/webhook/suporte/status-update', methods=['POST'])
def webhook_status_update():
    """Webhook para receber atualizações de status da API externa"""
    try:
        # Verificar se a requisição tem dados JSON
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 400

        data = request.get_json()

        print(f"🔔 Webhook recebido: {json.dumps(data, indent=2)}")

        # Validar estrutura básica da notificação
        if not data.get('ticket_id'):
            return jsonify({'error': 'ticket_id é obrigatório'}), 400

        ticket_id = data['ticket_id']
        novo_status = data.get('status')
        evento = data.get('event', 'status_update')

        if not novo_status:
            return jsonify({'error': 'status é obrigatório'}), 400

        # Buscar chamado no banco local
        chamado = Chamado.query.filter_by(api_chamado_id=ticket_id).first()

        if not chamado:
            print(f"⚠️  Chamado {ticket_id} não encontrado no sistema local")
            return jsonify({'error': f'Chamado {ticket_id} não encontrado'}), 404

        # Mapear status da API para status local
        status_mapeado = mapear_status_api(novo_status)

        # Verificar se houve mudança de status
        if chamado.status == status_mapeado:
            print(f"ℹ️  Status já está atualizado: {chamado.numero_chamado} = {status_mapeado}")
            return jsonify({'message': 'Status já atualizado', 'ticket_id': ticket_id}), 200

        # Atualizar status do chamado
        status_anterior = chamado.status
        chamado.status = status_mapeado
        chamado.data_atualizacao = datetime.utcnow()

        # Salvar no banco
        db.session.commit()

        print(f"✅ Status atualizado via webhook: {chamado.numero_chamado}")
        print(f"   {status_anterior} → {status_mapeado}")

        # Aqui poderia adicionar notificações em tempo real via WebSocket
        # ou outras ações como envio de email, etc.

        return jsonify({
            'message': 'Status atualizado com sucesso',
            'ticket_id': ticket_id,
            'numero_chamado': chamado.numero_chamado,
            'status_anterior': status_anterior,
            'status_novo': status_mapeado
        }), 200

    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

def mapear_status_api(status_api):
    """Mapeia status da API externa para status local"""
    mapeamento = {
        'novo': 'enviado',
        'recebido': 'enviado',
        'em_andamento': 'em_andamento',
        'atendimento': 'em_andamento',
        'em_atendimento': 'em_andamento',
        'resolvido': 'resolvido',
        'finalizado': 'fechado',
        'fechado': 'fechado',
        'cancelado': 'cancelado',
        'deletado': 'cancelado'
    }

    return mapeamento.get(status_api.lower(), 'enviado')

# ---------- SINCRONIZAÇÃO AUTOMÁTICA DE CHAMADOS ----------

def sincronizar_chamados_automatica():
    """Função executada automaticamente pelo scheduler para sincronizar chamados"""
    try:
        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Executando sincronização automática de chamados...")

        with app.app_context():
            # Buscar chamados que têm api_chamado_id
            chamados = Chamado.query.filter(Chamado.api_chamado_id.isnot(None)).all()

            if not chamados:
                print("⚠️  Nenhum chamado para sincronizar")
                return

            atualizados = 0
            deletados = 0

            for chamado in chamados:
                try:
                    # Verificar status na API
                    status_api, _ = verificar_status_chamado_api(chamado.api_chamado_id)

                    if status_api == 'deletado' and chamado.status != 'cancelado':
                        chamado.status = 'cancelado'
                        chamado.data_atualizacao = datetime.utcnow()
                        deletados += 1
                        print(f"   🗑️  {chamado.numero_chamado} marcado como CANCELADO")
                    elif status_api and status_api != chamado.status:
                        chamado.status = status_api
                        chamado.data_atualizacao = datetime.utcnow()
                        atualizados += 1
                        print(f"   🔄 {chamado.numero_chamado}: {chamado.status} → {status_api}")

                except Exception as e:
                    print(f"   ❌ Erro em {chamado.numero_chamado}: {e}")

            if atualizados > 0 or deletados > 0:
                db.session.commit()
                print(f"✅ Sincronização concluída: {atualizados} atualizados, {deletados} cancelados")
            else:
                print("✅ Nenhum chamado precisou ser atualizado")

    except Exception as e:
        print(f"❌ Erro na sincronização automática: {e}")

def verificar_status_chamado_api(api_chamado_id):
    """Verifica status de um chamado na API externa (função auxiliar)"""
    if not api_chamado_id:
        return None, None

    try:
        # Tentar diferentes endpoints
        endpoints = [
            f"http://localhost:5001/api/v1/suporte/{api_chamado_id}",
            f"http://localhost:5001/api/v1/chamados/{api_chamado_id}",
            f"http://localhost:5001/api/chamados/{api_chamado_id}"
        ]

        headers = {"X-API-Key": "barber-connect-api-key-2025"}

        for url in endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Verificar formato da resposta
                        if data.get('success') and 'ticket' in data:
                            # Formato: {"success": true, "ticket": {...}}
                            ticket = data['ticket']
                            status_api = ticket.get('status', 'novo')
                        else:
                            # Formato direto
                            status_api = data.get('status', 'novo')
                        
                        # Mapear status da API para status local
                        status_mapeado = mapear_status_api(status_api)
                        return status_mapeado, data
                        
                    except json.JSONDecodeError:
                        print(f"⚠️  Resposta JSON inválida da API: {url}")
                        continue
                elif response.status_code == 404:
                    return 'deletado', None
            except requests.RequestException as e:
                print(f"⚠️  Erro ao conectar com {url}: {e}")
                continue

    except Exception as e:
        print(f"❌ Erro ao verificar API: {e}")

    return None, None

def iniciar_scheduler_sincronizacao():
    """Inicia o scheduler para sincronização automática"""
    try:
        # Verificar se já existe um scheduler
        if hasattr(app, 'scheduler') and app.scheduler.running:
            print("🔄 Scheduler já está rodando")
            return

        # Criar scheduler
        app.scheduler = BackgroundScheduler()
        app.scheduler.start()

        # Adicionar job de sincronização a cada 5 minutos
        app.scheduler.add_job(
            func=sincronizar_chamados_automatica,
            trigger=IntervalTrigger(minutes=5),
            id='sincronizacao_chamados',
            name='Sincronização automática de chamados',
            replace_existing=True
        )

        print("✅ Scheduler de sincronizacao iniciado - executara a cada 5 minutos")
        print("💡 Para alterar o intervalo, modifique o parâmetro 'minutes' no IntervalTrigger")

    except Exception as e:
        print(f"❌ Erro ao iniciar scheduler: {e}")

# Inicializar componentes globais (Scheduler, etc)
# Para Gunicorn, isso precisa ser chamado fora do bloco if __name__ == '__main__':
iniciar_scheduler_sincronizacao()

# ---------- START ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()

    # checa templates requeridos (avisa, mas não interrompe)
    missing = check_required_templates(REQUIRED_TEMPLATES)
    if missing:
        print("\nAcesse http://localhost:5000/_templates_debug para ver a lista completa de templates carregáveis.", file=sys.stderr)

    # Configuração para Railway
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = True  # Modo debug ativado

    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    finally:
        # Parar scheduler quando o app for encerrado
        if hasattr(app, 'scheduler'):
            print("🛑 Parando scheduler...")
            app.scheduler.shutdown()
