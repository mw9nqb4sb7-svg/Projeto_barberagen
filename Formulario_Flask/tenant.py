"""
Sistema Multi-Tenant para isolamento de dados por barbearia
"""

from flask import g, request, session, abort, redirect, url_for
from functools import wraps
import re

class TenantContext:
    """Gerencia o contexto do tenant (barbearia) atual"""
    
    def __init__(self):
        self.barbearia_id = None
        self.barbearia = None
        self.usuario_barbearia = None
        self.is_super_admin = False
    
    def set_barbearia(self, barbearia_id, barbearia=None, usuario_barbearia=None):
        """Define a barbearia atual no contexto"""
        self.barbearia_id = barbearia_id
        self.barbearia = barbearia
        self.usuario_barbearia = usuario_barbearia
    
    def set_super_admin(self, is_super=False):
        """Define se o usuário é super admin"""
        self.is_super_admin = is_super
    
    def get_barbearia_id(self):
        """Retorna o ID da barbearia atual"""
        return self.barbearia_id
    
    def get_barbearia(self):
        """Retorna o objeto barbearia atual"""
        return self.barbearia
    
    def get_usuario_role(self):
        """Retorna a role do usuário na barbearia atual"""
        if self.is_super_admin:
            return 'super_admin'
        if self.usuario_barbearia:
            return self.usuario_barbearia.role
        return None
    
    def is_admin(self):
        """Verifica se o usuário é admin da barbearia atual"""
        return self.is_super_admin or self.get_usuario_role() == 'admin'
    
    def is_barbeiro(self):
        """Verifica se o usuário é barbeiro da barbearia atual"""
        return self.is_super_admin or self.get_usuario_role() in ['admin', 'barbeiro']
    
    def is_cliente(self):
        """Verifica se o usuário é cliente da barbearia atual"""
        return self.get_usuario_role() == 'cliente'

def identificar_barbearia(Barbearia=None):
    """Identifica qual barbearia está sendo acessada baseado na URL"""
    if not Barbearia:
        # Fallback para compatibilidade - tenta import direto
        try:
            from app import Barbearia
        except ImportError:
            return None
    
    # Estratégia 1: Via slug na URL (/<slug>/...)
    if hasattr(request, 'view_args') and request.view_args and 'slug' in request.view_args:
        slug = request.view_args['slug']
        if slug:
            barbearia = Barbearia.query.filter_by(slug=slug, ativa=True).first()
            if barbearia:
                return barbearia
    
    # Estratégia 2: Via barbearia_id na sessão (para compatibilidade)
    if 'barbearia_id' in session:
        barbearia = Barbearia.query.filter_by(id=session['barbearia_id'], ativa=True).first()
        if barbearia:
            return barbearia
        
    # Estratégia 3: Via parâmetro de query (para desenvolvimento)
    barbearia_param = request.args.get('b')
    if barbearia_param:
        barbearia = Barbearia.query.filter_by(slug=barbearia_param, ativa=True).first()
        if barbearia:
            return barbearia
    
    # Se não encontrou nenhuma barbearia ativa
    return None

def setup_tenant_context(Usuario=None, UsuarioBarbearia=None, Barbearia=None, db=None):
    """Configura o contexto do tenant antes de cada request"""
    # Usar modelos passados como parâmetro ou fallback para import
    if not all([Usuario, UsuarioBarbearia, Barbearia, db]):
        try:
            from app import Usuario, UsuarioBarbearia, Barbearia, db
        except ImportError:
            g.tenant = None
            return
    
    # Criar contexto do tenant
    g.tenant = TenantContext()
    
    # Verificar se é super admin (ignora isolamento de barbearia)
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario and usuario.tipo_conta == 'super_admin':
            g.tenant.set_super_admin(True)
            # Super admin pode acessar qualquer barbearia ou visão global
            barbearia = identificar_barbearia(Barbearia)
            if barbearia:
                g.tenant.set_barbearia(barbearia.id, barbearia)
            return
    
    # Identificar barbearia para usuários normais
    barbearia = identificar_barbearia(Barbearia)
    if not barbearia:
        # Se não encontrou barbearia válida, marcar contexto como vazio
        # A rota individual decidirá o que fazer (mostrar lista, erro, etc)
        g.tenant.barbearia = None
        g.tenant.barbearia_id = None
        return
    
    # Definir barbearia no contexto
    g.tenant.set_barbearia(barbearia.id, barbearia)
    
    # Se há usuário logado, buscar sua relação com a barbearia
    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        usuario_barbearia = UsuarioBarbearia.query.filter_by(
            usuario_id=usuario_id,
            barbearia_id=barbearia.id,
            ativo=True
        ).first()
        
        if usuario_barbearia:
            g.tenant.usuario_barbearia = usuario_barbearia
        else:
            # Usuário não tem acesso a esta barbearia
            # Verificar se é cliente que pode ser criado automaticamente
            usuario = Usuario.query.get(usuario_id)
            if usuario and usuario.tipo_conta == 'cliente':
                novo_vinculo = UsuarioBarbearia(
                    usuario_id=usuario_id,
                    barbearia_id=barbearia.id,
                    role='cliente',
                    ativo=True
                )
                db.session.add(novo_vinculo)
                db.session.commit()
                g.tenant.usuario_barbearia = novo_vinculo
            else:
                # Para admin/barbeiro, não criar vínculo automático
                g.tenant.usuario_barbearia = None

def require_tenant(f):
    """Decorator que garante que há um tenant válido no contexto"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant'):
            abort(404, "Contexto tenant não encontrado")
        # Super admin pode acessar sem tenant específico
        if g.tenant.is_super_admin:
            return f(*args, **kwargs)
        # Usuários normais precisam de tenant válido
        if not g.tenant.get_barbearia_id():
            abort(404, "Barbearia não encontrada")
        return f(*args, **kwargs)
    return decorated_function

# require_super_admin movido para app.py para evitar import circular

def require_role(*roles):
    """Decorator que exige uma role específica na barbearia atual"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant'):
                abort(403, "Contexto não encontrado")
            
            # Super admin tem acesso a tudo
            if g.tenant.is_super_admin:
                return f(*args, **kwargs)
            
            if not g.tenant.usuario_barbearia:
                abort(403, "Acesso negado - usuário não vinculado à barbearia")
            
            user_role = g.tenant.get_usuario_role()
            if user_role not in roles:
                abort(403, f"Acesso negado - role '{user_role}' não permitida")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin(f):
    """Decorator que exige permissão de admin na barbearia atual"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant'):
            abort(403, "Contexto não encontrado")
        
        # Super admin ou admin local
        if not g.tenant.is_admin():
            abort(403, "Acesso negado - apenas administradores")
        return f(*args, **kwargs)
    return decorated_function

def require_barbeiro(f):
    """Decorator que exige permissão de barbeiro ou admin na barbearia atual"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant'):
            abort(403, "Contexto não encontrado")
        
        if not g.tenant.is_barbeiro():
            abort(403, "Acesso negado - apenas barbeiros e administradores")
        return f(*args, **kwargs)
    return decorated_function

def get_current_barbearia_id():
    """Utilitário para obter o ID da barbearia atual"""
    # Primeiro, tentar do contexto tenant
    if hasattr(g, 'tenant') and g.tenant and g.tenant.get_barbearia_id():
        return g.tenant.get_barbearia_id()
    
    # Segundo, tentar do parâmetro da URL
    try:
        from flask import request
        barbearia_param = request.args.get('b')
        if barbearia_param:
            from app import Barbearia
            barbearia = Barbearia.query.filter_by(slug=barbearia_param, ativa=True).first()
            if barbearia:
                return barbearia.id
    except:
        pass
    
    # Fallback: tentar pegar da primeira barbearia ativa
    try:
        from app import Barbearia
        barbearia = Barbearia.query.filter_by(slug='principal', ativa=True).first()
        if barbearia:
            return barbearia.id
        # Se não encontrou 'principal', pega a primeira ativa
        barbearia = Barbearia.query.filter_by(ativa=True).first()
        return barbearia.id if barbearia else None
    except:
        return None

def get_current_barbearia():
    """Utilitário para obter o objeto da barbearia atual"""
    if hasattr(g, 'tenant') and g.tenant:
        return g.tenant.get_barbearia()
    # Fallback: tentar pegar da primeira barbearia ativa
    try:
        from app import Barbearia
        barbearia = Barbearia.query.filter_by(slug='principal', ativa=True).first()
        if barbearia:
            return barbearia
        # Se não encontrou 'principal', pega a primeira ativa
        return Barbearia.query.filter_by(ativa=True).first()
    except:
        return None

def is_super_admin():
    """Verifica se o usuário atual é super admin"""
    if 'usuario_id' not in session:
        return False
    
    try:
        from app import Usuario
        usuario = Usuario.query.get(session['usuario_id'])
        return usuario and usuario.tipo_conta == 'super_admin'
    except:
        return False
