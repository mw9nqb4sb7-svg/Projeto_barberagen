@echo off
REM ========================================
REM Script para Rodar em Producao (Windows)
REM ========================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     INICIANDO SERVIDOR DE PRODUCAO - WAITRESS             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar se Waitress está instalado
python -c "import waitress" 2>nul
if errorlevel 1 (
    echo ⚠️  Waitress nao encontrado. Instalando...
    pip install waitress
    echo.
)

echo 🚀 Iniciando servidor com Waitress...
echo 📊 Configuracao:
echo    - Host: 0.0.0.0
echo    - Porta: 5000
echo    - Threads: 8
echo    - Otimizado para multiplos acessos
echo.
echo 💡 Acesse: http://localhost:5000
echo.
echo ⚠️  Para parar: Pressione CTRL+C
echo.

waitress-serve --host=0.0.0.0 --port=5000 --threads=8 --channel-timeout=120 app:app
