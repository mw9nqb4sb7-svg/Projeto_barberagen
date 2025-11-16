# Documentação Técnica - Sistema de Barbearias

## 🏗️ Arquitetura

### Multi-Tenant Architecture
O sistema implementa uma arquitetura multi-tenant onde cada barbearia opera de forma isolada:

- **URL Pattern**: `/{slug}/` para páginas públicas da barbearia
- **Admin Pattern**: `/{slug}/admin/` para área administrativa
- **Super Admin**: `/super_admin/` para gestão global

### Modelos de Dados

#### Barbearia
```python
class Barbearia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    ativa = db.Column(db.Boolean, default=True)
```

#### Usuario
```python
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo_conta = db.Column(db.String(20), default='cliente')
    # Tipos: super_admin, admin_barbearia, barbeiro, cliente
```

#### UsuarioBarbearia (Junction Table)
```python
class UsuarioBarbearia(db.Model):
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    barbearia_id = db.Column(db.Integer, db.ForeignKey('barbearia.id'), primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    # Roles: admin, barbeiro, cliente
```

### Sistema de Autenticação

#### Hierarquia de Permissões
1. **Super Admin**: Acesso total ao sistema
2. **Admin de Barbearia**: Gestão completa da barbearia específica
3. **Barbeiro**: Visualização dos próprios agendamentos
4. **Cliente**: Agendamentos e histórico pessoal

#### Tenant Context
```python
# tenant.py
class TenantContext:
    def is_admin(self):
        return self.is_super_admin or self.get_usuario_role() == 'admin'
    
    def is_barbeiro(self):
        return self.is_super_admin or self.get_usuario_role() in ['admin', 'barbeiro']
```

## 🔄 Fluxo de Requisições

### 1. Before Request Middleware
```python
@app.before_request
def before_request():
    # Configurar contexto do tenant baseado na URL
    setup_tenant_context(Usuario, UsuarioBarbearia, Barbearia, db)
```

### 2. Identificação do Tenant
```python
def identificar_barbearia():
    # 1. Via slug na URL (/<slug>/...)
    # 2. Via barbearia_id na sessão
    # 3. Via parâmetro de query (?b=slug)
```

### 3. Verificação de Permissões
```python
# Exemplo de rota protegida
@app.route('/<slug>/admin/clientes')
def admin_clientes(slug):
    if not g.tenant.is_admin():
        flash('Acesso negado', 'error')
        return redirect(url_for('dashboard', slug=slug))
```

## 📊 Banco de Dados

### Isolamento de Dados
- Cada query filtra por `barbearia_id`
- Junction table `UsuarioBarbearia` controla acesso
- Dados completamente isolados entre barbearias

### Migrações
```python
# Para criar novas tabelas
with app.app_context():
    db.create_all()

# Para modificar estrutura existente
# Usar Flask-Migrate (não implementado ainda)
```

## 🎨 Frontend

### Templates
- **Base Template**: `templates/base.html`
- **Admin Templates**: `templates/admin/`
- **Cliente Templates**: `templates/cliente/`
- **Super Admin**: `templates/super_admin/`

### Assets
- **CSS**: `static/css/styles.css`
- **JavaScript**: `static/js/script.js`

## 🔧 Configuração

### Variáveis de Ambiente
```python
# app.py
app.secret_key = os.environ.get('FLASK_SECRET', 'segredo123')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///meubanco.db')
```

### Configuração de Produção
```python
# Para Railway/Heroku
if os.environ.get('RAILWAY_ENVIRONMENT'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['DEBUG'] = False
```

## 🚀 Deploy

### Railway
1. Conectar repositório GitHub
2. Configurar variáveis de ambiente
3. Deploy automático

### Docker (Opcional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## 🧪 Testes

### Scripts de Teste
- `criar_usuarios.py`: Gestão manual de usuários
- `criar_usuarios_lote.py`: Criação em massa
- `setup.py`: Inicialização completa do sistema

### Dados de Teste
```python
# Barbearia de exemplo
nome: "Barbearia Man"
slug: "man"
admin: admin@man.com / admin123
barbeiro: barbeiro@man.com / barbeiro123
```

## 🔍 Debugging

### Logs Importantes
```python
# tenant.py - debug de contexto
print(f"DEBUG: Barbearia identificada: {barbearia.slug}")
print(f"DEBUG: Usuario role: {g.tenant.get_usuario_role()}")
```

### Problemas Comuns
1. **BuildError**: URLs sem parâmetro `slug`
2. **Acesso Negado**: Verificar `g.tenant.is_admin()`
3. **Contexto Perdido**: Verificar `setup_tenant_context()`

## 📈 Performance

### Otimizações Implementadas
- Uso de junction table para relacionamentos N:N
- Índices em campos de busca frequente
- Filtragem por barbearia_id em todas as queries

### Melhorias Futuras
- Cache de sessão
- Paginação de resultados
- Compressão de assets
- CDN para arquivos estáticos

## 🔒 Segurança

### Implementado
- Hash de senhas com Werkzeug
- Isolamento de dados por tenant
- Verificação de permissões em todas as rotas
- Sanitização de inputs

### Recomendações para Produção
- HTTPS obrigatório
- Rate limiting
- Validação de CSP
- Logs de auditoria
- Backup automático do banco