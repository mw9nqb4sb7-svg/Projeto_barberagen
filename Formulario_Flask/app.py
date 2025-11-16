from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys
import json
from pathlib import Path
from jinja2 import ChoiceLoader, FileSystemLoader

# Caminhos absolutos
BASE_DIR = str(Path(__file__).resolve().parent)
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')        # templates padrão
CLIENTE_TEMPLATES_DIR = os.path.join(BASE_DIR, 'cliente')  # templates que você deixou fora da pasta templates
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_PATH = os.path.join(BASE_DIR, 'meubanco.db')

# Cria app com template_folder apontando para templates principal
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ.get('FLASK_SECRET', 'segredo123')

# Adiciona vários caminhos de busca de templates (templates/ e cliente/)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(TEMPLATES_DIR),
    FileSystemLoader(CLIENTE_TEMPLATES_DIR),
    app.jinja_loader
])

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Importar sistema multi-tenant após db ser criado
from tenant import setup_tenant_context, require_tenant, require_admin, require_barbeiro, require_role, get_current_barbearia_id, get_current_barbearia, is_super_admin

def require_super_admin(f):
    """Decorator que exige permissão de super admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se está logado
        if 'usuario_id' not in session:
            abort(403, "Login necessário")
        
        # Buscar usuário e verificar tipo
        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            abort(403, "Usuário não encontrado")
        
        if usuario.tipo_conta != 'super_admin':
            abort(403, "Acesso negado - apenas super administradores")
        
        return f(*args, **kwargs)
    return decorated_function

# ---------- MODELOS ----------
class Barbearia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # para URLs amigáveis
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Configurações específicas da barbearia (JSON)
    configuracoes = db.Column(db.Text, default='{}')
    
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
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Tipo geral do usuário no sistema
    tipo_conta = db.Column(db.String(20), nullable=False, default='cliente')  # admin_sistema, admin_barbearia, barbeiro, cliente
    
    # Relacionamentos
    barbearias = db.relationship('UsuarioBarbearia', back_populates='usuario', cascade="all, delete-orphan")
    
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

class Servico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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

class DisponibilidadeSemanal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
    'admin/disponibilidade_semana.html'
]

# ---------- MIDDLEWARE ----------
@app.before_request
def before_request():
    """Middleware executado antes de cada request"""
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

# ---------- ROTAS ----------

# ============= ÁREA ADMINISTRATIVA (SUPER ADMIN) =============
@app.route('/')
def admin_index():
    """Área administrativa - lista de barbearias (só para super admin)"""
    barbearias = Barbearia.query.filter_by(ativa=True).all()
    return render_template('barbearias_lista.html', barbearias=barbearias)

# ============= REDIRECIONAMENTOS LEGADOS =============
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
    
    # Mostra página da barbearia com serviços
    servicos = Servico.query.filter_by(barbearia_id=barbearia.id, ativo=True).all()
    return render_template('barbearia_home.html', 
                         barbearia=barbearia, 
                         servicos=servicos)

@app.route('/<slug>/dashboard')
def dashboard(slug):
    """Dashboard específico baseado no tipo de usuário"""
    if 'usuario_id' not in session:
        return redirect(url_for('barbearia_publica', slug=slug))
    
    if g.tenant.is_admin():
        # Admin: mostra dados da barbearia
        barbearia_id = get_current_barbearia_id()
        usuarios_barbearia = db.session.query(Usuario).join(UsuarioBarbearia).filter(
            UsuarioBarbearia.barbearia_id == barbearia_id,
            UsuarioBarbearia.role == 'cliente'
        ).all()
        reservas = Reserva.query.filter_by(barbearia_id=barbearia_id).all()
        servicos = Servico.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()
        return render_template('admin/dashboard.html', 
                             usuarios=usuarios_barbearia, 
                             reservas=reservas, 
                             servicos=servicos,
                             barbearia=get_current_barbearia())
    elif g.tenant.is_barbeiro():
        # Barbeiro: mostra suas reservas
        barbearia_id = get_current_barbearia_id()
        reservas = Reserva.query.filter_by(
            barbearia_id=barbearia_id,
            barbeiro_id=session['usuario_id']
        ).all()
        servicos = Servico.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()
        return render_template('usuario_dashboard.html', 
                             reservas=reservas, 
                             servicos=servicos,
                             barbearia=get_current_barbearia(),
                             user_type='barbeiro')
    else:
        # Cliente: mostra suas reservas
        barbearia_id = get_current_barbearia_id()
        reservas = Reserva.query.filter_by(
            barbearia_id=barbearia_id,
            cliente_id=session['usuario_id']
        ).all()
        servicos = Servico.query.filter_by(barbearia_id=barbearia_id, ativo=True).all()
        return render_template('usuario_dashboard.html', 
                             reservas=reservas, 
                             servicos=servicos,
                             barbearia=get_current_barbearia(),
                             user_type='cliente')

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
        email = request.form.get('email','').strip()
        senha = request.form.get('senha','')
        
        # Buscar usuário e verificar se tem acesso à barbearia atual
        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        if usuario and check_password_hash(usuario.senha, senha):
            # Super admin tem acesso a qualquer barbearia
            if usuario.tipo_conta == 'super_admin':
                session['usuario_id'] = usuario.id
                session['user_id'] = usuario.id  # compatibilidade
                session['usuario_nome'] = usuario.nome
                session['barbearia_id'] = barbearia.id  # Garantir contexto
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard', slug=slug))
            
            # Para outros tipos de usuário, verificar vínculo com a barbearia
            usuario_barbearia = UsuarioBarbearia.query.filter_by(
                usuario_id=usuario.id,
                barbearia_id=barbearia.id,
                ativo=True
            ).first()
            
            if not usuario_barbearia:
                flash('Usuário não tem acesso a esta barbearia!', 'error')
                return render_template('cliente/login.html', barbearia=barbearia)
            
            # Login bem-sucedido
            session['usuario_id'] = usuario.id
            session['user_id'] = usuario.id  # compatibilidade
            session['usuario_nome'] = usuario.nome
            session['barbearia_id'] = barbearia.id  # Garantir contexto
            session['usuario_role'] = usuario_barbearia.role  # Armazenar role na sessão
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard', slug=slug))
        else:
            flash('Credenciais inválidas!', 'error')
    return render_template('cliente/login.html', barbearia=get_current_barbearia())

@app.route('/<slug>/cadastro', methods=['GET','POST'])
def cadastro(slug):
    # Verificar se a barbearia existe
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        return redirect('/')
    
    # Define contexto da barbearia
    session['barbearia_id'] = barbearia.id
        
    if request.method == 'POST':
        nome = request.form.get('nome','').strip()
        email = request.form.get('email','').strip()
        telefone = request.form.get('telefone', '').strip()
        senha = request.form.get('senha','')
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'warning')
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
        
        # Vincular à barbearia específica (usar diretamente a barbearia do slug)
        vinculo = UsuarioBarbearia(
            usuario_id=novo.id,
            barbearia_id=barbearia.id,
            role='cliente',
            ativo=True
        )
        db.session.add(vinculo)
        db.session.commit()
        
        flash('Cadastro realizado! Faça login.', 'success')
        return redirect(url_for('login', slug=slug))
    return render_template('cliente/cadastro_cliente.html', barbearia=get_current_barbearia())

@app.route('/<slug>/logout')
def logout(slug):
    session.clear(); flash('Você saiu.', 'info'); return redirect(url_for('barbearia_publica', slug=slug))

@app.route('/<slug>/meus_agendamentos')
def meus_agendamentos(slug):
    """Mostra os agendamentos do usuário para a barbearia específica"""
    if 'usuario_id' not in session: 
        return redirect(url_for('login', slug=slug))
    
    # Obter barbearia pelo slug
    barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
    if not barbearia:
        flash('Barbearia não encontrada.', 'error')
        return redirect(url_for('admin_index'))
    
    # Buscar reservas do usuário para esta barbearia
    reservas = Reserva.query.filter_by(
        cliente_id=session['usuario_id'],
        barbearia_id=barbearia.id
    ).order_by(Reserva.data.desc(), Reserva.hora_inicio.desc()).all()
    
    return render_template('cliente/meus_agendamentos.html', 
                         reservas=reservas, 
                         barbearia=barbearia)

# Rota de redirecionamento para compatibilidade
@app.route('/meus_agendamentos')
def meus_agendamentos_redirect():
    """Redireciona para meus agendamentos da barbearia principal"""
    if 'usuario_id' not in session: 
        return redirect(url_for('login', slug='principal'))
    return redirect(url_for('meus_agendamentos', slug=get_current_barbearia_slug()))

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
        
        # Verificar se já existe reserva para este horário na barbearia atual
        if Reserva.query.filter_by(
            barbearia_id=barbearia.id, 
            servico_id=servico_id, 
            data=data, 
            hora_inicio=hora
        ).first():
            flash('Horário já reservado.', 'danger'); return redirect(url_for('nova_reserva', slug=slug))
        
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
        db.session.add(reserva); db.session.commit(); flash('Reserva criada!', 'success'); return redirect(url_for('meus_agendamentos', slug=slug))
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
    """Lista todos os agendamentos da barbearia específica"""
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=slug))
    
    barbearia_id = get_current_barbearia_id()
    reservas = Reserva.query.filter_by(barbearia_id=barbearia_id).all()
    
    return render_template('admin/admin_agendamentos.html', 
                         reservas=reservas,
                         barbearia=get_current_barbearia())

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

@app.route('/cancelar_reserva/<int:reserva_id>')
def cancelar_reserva(reserva_id):
    if 'usuario_id' not in session: flash('Faça login.', 'warning'); return redirect(url_for('login', slug=get_current_barbearia_slug()))
    reserva = Reserva.query.get_or_404(reserva_id)
    if reserva.usuario_id != session['usuario_id']: flash('Só pode cancelar suas reservas.', 'danger'); return redirect(url_for('meus_agendamentos', slug=get_current_barbearia_slug()))
    db.session.delete(reserva); db.session.commit(); flash('Reserva cancelada.', 'info'); return redirect(url_for('meus_agendamentos', slug=get_current_barbearia_slug()))

@app.route('/admin/agendamentos')
def admin_agendamentos():
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    reservas = Reserva.query.all()
    return render_template('admin/admin_agendamentos.html', reservas=reservas)

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
    
    return render_template('admin/disponibilidade.html', semanas=semanas)

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
                         dias_opcoes=dias_opcoes)

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
        if not nome or not email: flash('Preencha campos!', 'warning'); return redirect(url_for('clientes'))
        if Usuario.query.filter_by(email=email).first(): flash('Email já cadastrado!', 'warning'); return redirect(url_for('clientes'))
        novo = Usuario(nome=nome, email=email, senha=generate_password_hash('senha123'), tipo_conta='cliente', ativo=True)
        db.session.add(novo); db.session.commit(); flash('Cliente adicionado!', 'success'); return redirect(url_for('clientes'))
    barbearia_id = get_current_barbearia_id()
    clientes_list = db.session.query(Usuario).join(UsuarioBarbearia).filter(
        UsuarioBarbearia.barbearia_id == barbearia_id,
        UsuarioBarbearia.role == 'cliente'
    ).all()
    return render_template('cliente/clientes.html', clientes=clientes_list)

@app.route('/servicos', methods=['GET','POST'])
def servicos():
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    if request.method == 'POST':
        nome = request.form.get('nome','').strip(); preco_str = request.form.get('preco','').strip()
        if not nome or not preco_str: flash('Preencha campos!', 'warning'); return redirect(url_for('servicos'))
        try: preco = float(preco_str)
        except ValueError: flash('Preço inválido!', 'danger'); return redirect(url_for('servicos'))
        novo = Servico(nome=nome, preco=preco); db.session.add(novo); db.session.commit(); flash('Serviço adicionado!', 'success'); return redirect(url_for('servicos'))
    servicos_list = Servico.query.all()
    return render_template('cliente/servicos.html', servicos=servicos_list)

@app.route('/deletar_cliente/<int:cliente_id>')
def deletar_cliente(cliente_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    cliente = Usuario.query.get_or_404(cliente_id)
    reservas_cliente = Reserva.query.filter_by(usuario_id=cliente_id).all()
    if reservas_cliente:
        flash(f'Não é possível deletar "{cliente.nome}". Possui {len(reservas_cliente)} reservas ativas.', 'danger')
        return redirect(url_for('clientes'))
    db.session.delete(cliente); db.session.commit()
    flash(f'Cliente "{cliente.nome}" deletado!', 'success')
    return redirect(url_for('clientes'))

@app.route('/deletar_servico/<int:servico_id>')
def deletar_servico(servico_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    servico = Servico.query.get_or_404(servico_id)
    reservas_associadas = Reserva.query.filter_by(servico_id=servico_id).all()
    if reservas_associadas:
        flash(f'Não é possível deletar "{servico.nome}". Possui {len(reservas_associadas)} reservas ativas.', 'danger')
        return redirect(url_for('servicos'))
    db.session.delete(servico); db.session.commit()
    flash(f'Serviço "{servico.nome}" deletado!', 'success')
    return redirect(url_for('servicos'))

@app.route('/deletar_agendamento/<int:agendamento_id>')
def deletar_agendamento(agendamento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=get_current_barbearia_slug()))
    if not hasattr(g, 'tenant') or not g.tenant or not g.tenant.is_admin():
        flash('Acesso negado - apenas administradores', 'error')
        return redirect(url_for('dashboard', slug=get_current_barbearia_slug()))
    reserva = Reserva.query.get_or_404(agendamento_id)
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
        return redirect(url_for('meus_agendamentos', slug=get_current_barbearia_slug()))

    # Tenta renderizar cliente/perfil.html se existir, caso contrário redireciona ao dashboard do cliente
    try:
        return render_template('cliente/perfil.html', usuario=usuario)
    except Exception:
        return redirect(url_for('meus_agendamentos', slug=get_current_barbearia_slug()))

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
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        # Buscar apenas usuários super admin
        usuario = Usuario.query.filter_by(email=email, tipo_conta='super_admin', ativo=True).first()
        if usuario and check_password_hash(usuario.senha, senha):
            session['usuario_id'] = usuario.id
            session['user_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            flash('Super Admin logado com sucesso!', 'success')
            return redirect(url_for('super_admin_dashboard'))
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

@app.route('/super_admin/barbearia/<int:barbearia_id>/editar', methods=['GET', 'POST'])
@require_super_admin
def super_admin_editar_barbearia(barbearia_id):
    """Editar dados de uma barbearia"""
    barbearia = Barbearia.query.get_or_404(barbearia_id)
    
    if request.method == 'POST':
        # Atualizar dados da barbearia
        nome = request.form.get('nome', '').strip()
        slug = request.form.get('slug', '').strip()
        cnpj = request.form.get('cnpj', '').strip()
        telefone = request.form.get('telefone', '').strip()
        endereco = request.form.get('endereco', '').strip()
        ativa = request.form.get('ativa') == 'on'
        
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
            Barbearia.id != barbearia_id
        ).first()
        
        if slug_existente:
            flash('Este slug já está sendo usado por outra barbearia!', 'error')
            return redirect(request.url)
        
        # Verificar se CNPJ já existe (se fornecido e diferente do atual)
        if cnpj and cnpj != barbearia.cnpj:
            cnpj_existente = Barbearia.query.filter(
                Barbearia.cnpj == cnpj,
                Barbearia.id != barbearia_id
            ).first()
            
            if cnpj_existente:
                flash('Este CNPJ já está sendo usado por outra barbearia!', 'error')
                return redirect(request.url)
        
        # Atualizar os dados
        barbearia.nome = nome
        barbearia.slug = slug
        barbearia.cnpj = cnpj if cnpj else None
        barbearia.telefone = telefone if telefone else None
        barbearia.endereco = endereco if endereco else None
        barbearia.ativa = ativa
        
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
        
        # Criar nova barbearia
        nova_barbearia = Barbearia(
            nome=nome,
            slug=slug,
            cnpj=cnpj if cnpj else None,
            telefone=telefone if telefone else None,
            endereco=endereco if endereco else None,
            ativa=True
        )
        
        try:
            db.session.add(nova_barbearia)
            db.session.commit()
            flash('Barbearia criada com sucesso!', 'success')
            return redirect(url_for('super_admin_barbearias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar barbearia: {str(e)}', 'error')
    
    return render_template('super_admin/nova_barbearia.html')

@app.route('/super_admin/barbearia/<int:barbearia_id>/deletar', methods=['POST'])
@require_super_admin
def super_admin_deletar_barbearia(barbearia_id):
    """Deletar uma barbearia (apenas inativar por segurança)"""
    barbearia = Barbearia.query.get_or_404(barbearia_id)
    
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

# ---------- START ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # cria admin padrão se não existir
        if not Usuario.query.filter_by(email='admin@admin.com').first():
            # Admin já criado via setup_db.py
            pass
        db.session.commit()

    # checa templates requeridos (avisa, mas não interrompe)
    missing = check_required_templates(REQUIRED_TEMPLATES)
    if missing:
        print("\nAcesse http://localhost:5000/_templates_debug para ver a lista completa de templates carregáveis.", file=sys.stderr)

    app.run(debug=True)