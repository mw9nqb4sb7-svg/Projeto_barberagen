#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para limpar coluna custom_css do banco de dados
Agora cada barbearia tem seu próprio arquivo CSS físico
"""

from app import app, db, Barbearia

def limpar_custom_css():
    with app.app_context():
        print("🧹 Limpando coluna custom_css do banco de dados...")
        print("-" * 60)
        
        # Buscar todas as barbearias que tem CSS no banco
        barbearias_com_css = Barbearia.query.filter(Barbearia.custom_css.isnot(None)).all()
        
        if not barbearias_com_css:
            print("✅ Nenhuma barbearia com CSS no banco de dados!")
            print("📝 Todas já usam arquivos CSS físicos.")
            return
        
        print(f"📊 Encontradas {len(barbearias_com_css)} barbearia(s) com CSS no banco:\n")
        
        for barbearia in barbearias_com_css:
            tamanho_css = len(barbearia.custom_css) if barbearia.custom_css else 0
            print(f"  • {barbearia.nome} ({barbearia.slug})")
            print(f"    └─ Tamanho do CSS: {tamanho_css} caracteres")
            print(f"    └─ Arquivo CSS: static/css/barbearias/{barbearia.slug}.css")
            
            # Limpar o CSS do banco
            barbearia.custom_css = None
        
        # Salvar alterações
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ CSS removido do banco de dados com sucesso!")
            print("📁 Todos os estilos agora estão em arquivos físicos:")
            print("   static/css/barbearias/[slug-da-barbearia].css")
            print("=" * 60)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao limpar CSS: {str(e)}")

if __name__ == "__main__":
    limpar_custom_css()
