"""
Script para adicionar a logo na barbearia Leo Cortes
"""
import sqlite3
import os
import shutil

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'meubanco.db')
base_dir = os.path.dirname(__file__)

print(f"Conectando ao banco de dados: {db_path}")

# Conectar ao banco
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Buscar a barbearia Leo Cortes
    cursor.execute("SELECT id, nome, slug, logo FROM barbearia WHERE slug LIKE '%leo%' OR nome LIKE '%leo%'")
    resultado = cursor.fetchone()
    
    if resultado:
        barbearia_id, nome, slug, logo_atual = resultado
        print(f"\n✓ Barbearia encontrada: {nome} (ID: {barbearia_id}, Slug: {slug})")
        print(f"  Logo atual: {logo_atual or 'Nenhuma'}")
        
        # Copiar logo para pasta de uploads
        origem = os.path.join(base_dir, 'static', 'images', 'logo_leo.png')
        destino_dir = os.path.join(base_dir, 'static', 'uploads', 'logos')
        os.makedirs(destino_dir, exist_ok=True)
        destino = os.path.join(destino_dir, 'logo_leo.png')
        
        if os.path.exists(origem):
            shutil.copy2(origem, destino)
            print(f"✓ Logo copiada para: {destino}")
            
            # Atualizar no banco de dados
            cursor.execute("UPDATE barbearia SET logo = ? WHERE id = ?", ('logo_leo.png', barbearia_id))
            conn.commit()
            print(f"✓ Logo atualizada no banco de dados para a barbearia '{nome}'")
        else:
            print(f"❌ Arquivo não encontrado: {origem}")
            print("\nVerificando arquivos na pasta static/images:")
            images_dir = os.path.join(base_dir, 'static', 'images')
            if os.path.exists(images_dir):
                arquivos = os.listdir(images_dir)
                for arquivo in arquivos:
                    print(f"  - {arquivo}")
    else:
        print("\n❌ Barbearia Leo Cortes não encontrada")
        print("\nBarbearias disponíveis:")
        cursor.execute("SELECT id, nome, slug FROM barbearia")
        for row in cursor.fetchall():
            print(f"  - {row[1]} (slug: {row[2]})")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\n✓ Concluído!")
