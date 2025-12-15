"""
Script para adicionar colunas UUID ao banco de dados existente
Este script deve ser executado ANTES da migração de dados
"""
import sys
import os
from pathlib import Path
import sqlite3

# Caminho para o banco de dados
BASE_DIR = str(Path(__file__).resolve().parent.parent)
DB_PATH = os.path.join(BASE_DIR, 'meubanco.db')

def adicionar_colunas_uuid():
    """Adiciona colunas UUID às tabelas existentes"""
    print("=" * 60)
    print("PASSO 1: Adicionando colunas UUID ao banco de dados")
    print("=" * 60)
    print(f"\nBanco de dados: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"\n❌ ERRO: Banco de dados não encontrado em: {DB_PATH}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Lista de tabelas e suas colunas UUID
        tabelas = [
            ('barbearia', 'uuid'),
            ('usuario', 'uuid'),
            ('servico', 'uuid'),
            ('reserva', 'uuid'),
            ('disponibilidade_semanal', 'uuid')
        ]
        
        for tabela, coluna in tabelas:
            print(f"\n[{tabelas.index((tabela, coluna)) + 1}/{len(tabelas)}] Processando tabela '{tabela}'...")
            
            # Verificar se a coluna já existe
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas_existentes = [row[1] for row in cursor.fetchall()]
            
            if coluna in colunas_existentes:
                print(f"  ✓ Coluna '{coluna}' já existe na tabela '{tabela}'")
            else:
                # Adicionar a coluna UUID
                try:
                    cursor.execute(f"""
                        ALTER TABLE {tabela} 
                        ADD COLUMN {coluna} VARCHAR(36)
                    """)
                    print(f"  ✅ Coluna '{coluna}' adicionada à tabela '{tabela}'")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  ✓ Coluna '{coluna}' já existe na tabela '{tabela}'")
                    else:
                        raise
        
        # Commit das mudanças
        conn.commit()
        
        # Verificação final
        print("\n" + "=" * 60)
        print("VERIFICAÇÃO FINAL")
        print("=" * 60)
        
        tudo_ok = True
        for tabela, coluna in tabelas:
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = [row[1] for row in cursor.fetchall()]
            
            if coluna in colunas:
                print(f"  ✅ {tabela}.{coluna} - OK")
            else:
                print(f"  ❌ {tabela}.{coluna} - FALTANDO!")
                tudo_ok = False
        
        conn.close()
        
        print("\n" + "=" * 60)
        if tudo_ok:
            print("✅ SUCESSO! Todas as colunas UUID foram adicionadas.")
            print("\nPróximo passo:")
            print("  python scripts\\migrar_para_uuid.py")
        else:
            print("❌ ERRO! Algumas colunas não foram adicionadas.")
            print("Verifique os erros acima.")
        print("=" * 60)
        
        return tudo_ok
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        sucesso = adicionar_colunas_uuid()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
