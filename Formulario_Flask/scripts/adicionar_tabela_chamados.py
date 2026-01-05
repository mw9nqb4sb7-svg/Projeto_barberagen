#!/usr/bin/env python3
"""
Script para adicionar tabela de Chamados ao banco de dados
Executar após implementar o sistema de suporte

IMPORTANTE: Execute este script da pasta raiz do projeto (Formulario_Flask)
Exemplo: python scripts/adicionar_tabela_chamados.py
"""

import sys
import os
from pathlib import Path

# Verificar se estamos na pasta correta
current_dir = Path(__file__).resolve().parent.parent
app_file = current_dir / 'app.py'

if not app_file.exists():
    print("❌ ERRO: Execute este script da pasta raiz do projeto (Formulario_Flask)")
    print(f"   Arquivo app.py não encontrado em: {current_dir}")
    print("   Use: cd Formulario_Flask && python scripts/adicionar_tabela_chamados.py")
    sys.exit(1)

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(current_dir))

try:
    from app import app, db, Chamado
except ImportError as e:
    print(f"❌ ERRO ao importar módulos: {e}")
    print("Verifique se o arquivo app.py existe e está funcionando corretamente.")
    sys.exit(1)

def criar_tabela_chamados():
    """Cria a tabela Chamado se não existir"""
    with app.app_context():
        try:
            # Criar tabela
            db.create_all()
            print("✅ Tabela 'chamado' criada/verificada com sucesso!")

            # Verificar se a tabela foi criada
            inspector = db.inspect(db.engine)
            if 'chamado' in inspector.get_table_names():
                print("✅ Tabela 'chamado' existe no banco de dados")
            else:
                print("❌ Erro: Tabela 'chamado' não foi encontrada")

        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return False

    return True

if __name__ == "__main__":
    print("🔄 Criando tabela de Chamados...")
    if criar_tabela_chamados():
        print("✅ Migração concluída com sucesso!")
    else:
        print("❌ Falha na migração")
        sys.exit(1)