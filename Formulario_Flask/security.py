"""
Módulo de Segurança para a Aplicação BarberConnect
"""
from functools import wraps
from flask import session, request, abort, flash, redirect, url_for
from datetime import datetime, timedelta
import re
import bleach
import uuid

# Configurações de Rate Limiting (simulado)
LOGIN_ATTEMPTS = {}  # {ip: [(timestamp, success), ...]}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = 15 * 60  # 15 minutos em segundos

def sanitize_input(text, allow_html=False):
    """
    Sanitiza input do usuário para prevenir XSS
    """
    if not text:
        return text
    
    if allow_html:
        # Permite apenas tags HTML seguras
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
        return bleach.clean(text, tags=allowed_tags, strip=True)
    else:
        # Remove todas as tags HTML
        return bleach.clean(text, tags=[], strip=True)

def validate_email(email):
    """
    Valida formato de email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """
    Valida formato de telefone brasileiro
    """
    # Remove caracteres não numéricos
    phone_numbers = re.sub(r'\D', '', phone)
    # Aceita 10 ou 11 dígitos (com ou sem DDD)
    return len(phone_numbers) in [10, 11]

def validate_uuid(uuid_string):
    """
    Valida se uma string é um UUID válido
    Retorna (is_valid, sanitized_uuid)
    """
    if not uuid_string:
        return False, None
    
    try:
        # Tenta criar um objeto UUID a partir da string
        uuid_obj = uuid.UUID(str(uuid_string), version=4)
        # Retorna o UUID em formato string padronizado
        return True, str(uuid_obj)
    except (ValueError, AttributeError):
        return False, None

def validate_password_strength(password):
    """
    Valida força da senha
    Retorna (is_valid, message)
    """
    if len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    
    if len(password) < 10:
        return True, "Senha média - considere usar pelo menos 10 caracteres"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    strength = sum([has_upper, has_lower, has_digit, has_special])
    
    if strength >= 3:
        return True, "Senha forte"
    elif strength >= 2:
        return True, "Senha média - considere adicionar caracteres especiais"
    else:
        return True, "Senha fraca - use letras maiúsculas, minúsculas e números"

def check_rate_limit(identifier, max_attempts=MAX_LOGIN_ATTEMPTS, window=LOCKOUT_TIME):
    """
    Verifica rate limit para prevenir brute force
    Retorna (allowed, remaining_attempts, lockout_seconds)
    """
    now = datetime.now()
    
    if identifier not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[identifier] = []
    
    # Remove tentativas antigas (fora da janela de tempo)
    LOGIN_ATTEMPTS[identifier] = [
        (timestamp, success) for timestamp, success in LOGIN_ATTEMPTS[identifier]
        if (now - timestamp).total_seconds() < window
    ]
    
    # Conta tentativas falhadas recentes
    failed_attempts = sum(1 for _, success in LOGIN_ATTEMPTS[identifier] if not success)
    
    if failed_attempts >= max_attempts:
        # Usuário está bloqueado - calcular tempo restante
        oldest_attempt = min(timestamp for timestamp, _ in LOGIN_ATTEMPTS[identifier])
        lockout_end = oldest_attempt + timedelta(seconds=window)
        remaining_seconds = int((lockout_end - now).total_seconds())
        
        if remaining_seconds > 0:
            return False, 0, remaining_seconds
        else:
            # Período de bloqueio expirou - limpar tentativas
            LOGIN_ATTEMPTS[identifier] = []
            return True, max_attempts, 0
    
    remaining = max_attempts - failed_attempts
    return True, remaining, 0

def record_login_attempt(identifier, success=True):
    """
    Registra tentativa de login
    """
    now = datetime.now()
    
    if identifier not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[identifier] = []
    
    LOGIN_ATTEMPTS[identifier].append((now, success))
    
    # Limitar histórico a últimas 20 tentativas
    if len(LOGIN_ATTEMPTS[identifier]) > 20:
        LOGIN_ATTEMPTS[identifier] = LOGIN_ATTEMPTS[identifier][-20:]

def require_login(f):
    """
    Decorator que requer usuário logado
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            # Tentar redirecionar para login da barbearia atual
            slug = kwargs.get('slug') or session.get('barbearia_slug', 'principal')
            return redirect(url_for('login', slug=slug))
        return f(*args, **kwargs)
    return decorated_function

def validate_csrf_token():
    """
    Validação básica de CSRF via referer
    (Flask-WTF seria melhor para produção)
    """
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        referer = request.headers.get('Referer')
        if not referer or not referer.startswith(request.host_url):
            abort(403, "CSRF validation failed")

def sanitize_filename(filename):
    """
    Sanitiza nome de arquivo para prevenir path traversal
    """
    # Remove path separators e caracteres perigosos
    filename = re.sub(r'[/\\]', '', filename)
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename.strip()

def check_file_size(file, max_size_mb=5):
    """
    Verifica tamanho do arquivo
    """
    file.seek(0, 2)  # Vai para o final do arquivo
    size = file.tell()
    file.seek(0)  # Volta para o início
    
    max_size = max_size_mb * 1024 * 1024
    return size <= max_size

def validate_slug(slug):
    """
    Valida formato de slug (URL-safe)
    """
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    return re.match(pattern, slug) is not None

def get_client_ip():
    """
    Obtém IP real do cliente (considerando proxies)
    """
    if request.headers.get('X-Forwarded-For'):
        # Pega o primeiro IP da lista (IP real do cliente)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def audit_log(action, user_id=None, details=None):
    """
    Registra ações importantes para auditoria
    (Em produção, salvar em arquivo ou banco de dados)
    """
    timestamp = datetime.now().isoformat()
    ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    log_entry = {
        'timestamp': timestamp,
        'action': action,
        'user_id': user_id,
        'ip': ip,
        'user_agent': user_agent,
        'details': details
    }
    
    # TODO: Salvar em arquivo de log ou banco de dados
    # Por enquanto, apenas print para debug
    print(f"[AUDIT] {log_entry}")
    
    return log_entry
