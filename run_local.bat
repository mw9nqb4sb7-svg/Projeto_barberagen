@echo off
chcp 65001 >nul
echo ========================================
echo   SERVIDOR LOCAL - PROJETO BARBEARIA
echo ========================================
echo.

REM Define variáveis de ambiente para desenvolvimento
set FLASK_ENV=development
set FLASK_DEBUG=1
set FLASK_APP=app.py
set PORT=5000

echo [1/4] Verificando Python...
py --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ERRO: Python não encontrado!
    echo Instale Python em: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python OK
echo.

echo [2/4] Criando ambiente virtual (se não existir)...
if not exist "venv" (
    echo Criando venv...
    py -m venv venv
    echo ✅ Ambiente virtual criado!
) else (
    echo ✅ Ambiente virtual já existe!
)
echo.

echo [3/4] Ativando ambiente virtual e instalando dependências...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Ambiente virtual ativado
) else (
    echo ❌ ERRO: Ambiente virtual não encontrado!
    pause
    exit /b 1
)

echo.
echo Instalando/Atualizando dependências...
python -m pip install --upgrade pip
python -m pip install -r requirements_local.txt
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ AVISO: Algumas dependências podem ter falhado
    echo Tentando continuar...
)
echo ✅ Dependências instaladas
echo.

echo [4/4] Iniciando servidor local...
echo.
echo ========================================
echo   ✅ SERVIDOR RODANDO EM:
echo   
echo   🌐 http://localhost:5000
echo   🌐 http://127.0.0.1:5000
echo.
echo   📁 Banco de dados: meubanco.db
echo   🔄 Hot reload: ATIVADO
echo   🐛 Debug mode: ATIVADO
echo ========================================
echo.
echo 💡 DICA: Mantenha esta janela aberta!
echo ⏹️  Pressione CTRL+C para parar o servidor
echo.

python app.py

pause
