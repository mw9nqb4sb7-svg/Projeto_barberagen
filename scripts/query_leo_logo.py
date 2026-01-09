
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona o diretório do projeto ao sys.path para poder importar o app
# O script está em scripts/, então o app está no pai
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Carrega variáveis do .env se existirem
load_dotenv(os.path.join(BASE_DIR, '.env'))

try:
    from app import app, db, Barbearia
    
    with app.app_context():
        # Captura a URL para log (removendo a senha por segurança se necessário, mas aqui vamos apenas mostrar se existe)
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Não configurada')
        print(f"DEBUG: Conectando ao banco em: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}")
        
        barbearia = Barbearia.query.filter_by(slug='leo-cortes').first()
        
        if barbearia:
            print(f"RESULTADO: O nome do arquivo salvo no banco de dados para 'leo-cortes' é: {barbearia.logo}")
            
            # Verificar se o arquivo existe na pasta static/uploads/logos
            logo_path = os.path.join(BASE_DIR, 'static', 'uploads', 'logos', barbearia.logo if barbearia.logo else '')
            if barbearia.logo and os.path.exists(logo_path):
                print(f"STATUS: O arquivo existe em: static/uploads/logos/{barbearia.logo}")
            elif barbearia.logo:
                print(f"STATUS: O arquivo {barbearia.logo} NÃO foi encontrado na pasta static/uploads/logos/")
            else:
                print("STATUS: A coluna 'logo' está vazia ou nula no banco de dados.")
        else:
            print("ERRO: Barbearia com slug 'leo-cortes' não encontrada no banco de dados.")
except Exception as e:
    print(f"FALHA ao executar script: {str(e)}")
