"""
Configuração do Gunicorn para Produção
Otimizado para lidar com múltiplos acessos simultâneos
"""

import multiprocessing
import os

# Endereço e porta
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Número de workers (processos)
# Recomendação: (2 x $num_cores) + 1
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))

# Tipo de worker
# gevent para melhor performance com I/O (recomendado para Railway)
worker_class = os.getenv('WORKER_CLASS', 'gevent')

# Threads por worker (para worker_class='sync' ou 'gthread')
threads = int(os.getenv('WORKER_THREADS', 2))

# Timeout para requisições (segundos)
timeout = int(os.getenv('WORKER_TIMEOUT', 120))

# Tempo de espera para graceful shutdown
graceful_timeout = 30

# Keepalive para conexões persistentes
keepalive = 5

# Limite de requisições por worker antes de reiniciar
# Evita memory leaks
max_requests = int(os.getenv('MAX_REQUESTS', 1000))
max_requests_jitter = 50

# Configurações de logging
accesslog = '-'  # stdout
errorlog = '-'   # stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Preload da aplicação para economizar memória
preload_app = True

# Configuração de processo
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Callbacks para monitoramento
def on_starting(server):
    """Executado quando o servidor inicia"""
    print(f"🚀 Servidor Gunicorn iniciando com {workers} workers")
    print(f"📊 Worker class: {worker_class}")
    print(f"🧵 Threads por worker: {threads}")
    print(f"⏱️ Timeout: {timeout}s")

def on_reload(server):
    """Executado quando o servidor recarrega"""
    print("🔄 Servidor recarregado")

def when_ready(server):
    """Executado quando o servidor está pronto"""
    print(f"✅ Servidor pronto para receber requisições em {bind}")

def worker_int(worker):
    """Executado quando worker recebe SIGINT ou SIGQUIT"""
    print(f"⚠️ Worker {worker.pid} interrompido pelo usuário")

def worker_abort(worker):
    """Executado quando worker é abortado"""
    print(f"❌ Worker {worker.pid} abortado")

def pre_fork(server, worker):
    """Executado antes de fazer fork de um worker"""
    pass

def post_fork(server, worker):
    """Executado após fazer fork de um worker"""
    print(f"👶 Worker {worker.pid} iniciado")

def pre_exec(server):
    """Executado antes de exec()"""
    print("🔄 Preparando para reiniciar servidor")

def child_exit(server, worker):
    """Executado quando um worker sai"""
    print(f"👋 Worker {worker.pid} finalizado")

def worker_exit(server, worker):
    """Executado quando um worker é encerrado"""
    pass

def nworkers_changed(server, new_value, old_value):
    """Executado quando número de workers muda"""
    print(f"📊 Número de workers mudou: {old_value} → {new_value}")

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

print("""
╔════════════════════════════════════════════════════════════╗
║          CONFIGURAÇÃO DE PRODUÇÃO - GUNICORN              ║
╚════════════════════════════════════════════════════════════╝

📌 Esta configuração está otimizada para:
   • Múltiplos acessos simultâneos
   • Alta disponibilidade
   • Baixa latência
   • Uso eficiente de recursos

🔧 Variáveis de ambiente disponíveis:
   • WEB_CONCURRENCY: Número de workers (padrão: CPU * 2 + 1)
   • WORKER_CLASS: Tipo de worker (sync, gevent, eventlet)
   • WORKER_THREADS: Threads por worker (padrão: 2)
   • WORKER_TIMEOUT: Timeout em segundos (padrão: 120)
   • MAX_REQUESTS: Requests antes de reiniciar worker (padrão: 1000)
   • LOG_LEVEL: Nível de log (debug, info, warning, error, critical)

💡 Para melhor performance com I/O assíncrono:
   pip install gevent
   export WORKER_CLASS=gevent
   export WEB_CONCURRENCY=4

""")
