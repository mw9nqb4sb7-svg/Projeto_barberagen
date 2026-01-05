#!/bin/bash
# ========================================
# Script para Rodar em Producao (Linux)
# ========================================

clear

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     INICIANDO SERVIDOR DE PRODUCAO - GUNICORN             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se Gunicorn está instalado
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️  Gunicorn não encontrado. Instalando..."
    pip install gunicorn
    echo ""
fi

# Detectar número de CPUs
CPUS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
WORKERS=$((CPUS * 2 + 1))

echo "🚀 Iniciando servidor com Gunicorn..."
echo "📊 Configuração:"
echo "   - Workers: $WORKERS"
echo "   - Threads por worker: 2"
echo "   - Porta: ${PORT:-5000}"
echo "   - Timeout: 120s"
echo "   - Otimizado para múltiplos acessos"
echo ""
echo "💡 Servidor estará disponível em breve..."
echo ""
echo "⚠️  Para parar: Pressione CTRL+C"
echo ""

# Iniciar com arquivo de configuração
gunicorn -c gunicorn_config.py app:app
