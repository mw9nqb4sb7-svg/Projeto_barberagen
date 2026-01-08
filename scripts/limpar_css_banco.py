#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para limpar coluna custom_css do banco de dados
Agora cada barbearia tem seu próprio arquivo CSS físico
"""

from app import app, db, Barbearia
import logging
import sys

# Logger para scripts
logger = logging.getLogger('projeto_barber.scripts.limpar_css_banco')
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(_handler)

def limpar_custom_css():
    with app.app_context():
        logger.info("🧹 Limpando coluna custom_css do banco de dados...")
        logger.info("-" * 60)
        
        # Buscar todas as barbearias que tem CSS no banco
        barbearias_com_css = Barbearia.query.filter(Barbearia.custom_css.isnot(None)).all()
        
        if not barbearias_com_css:
            logger.info("✅ Nenhuma barbearia com CSS no banco de dados!")
            logger.info("📝 Todas já usam arquivos CSS físicos.")
            return
        
        logger.info(f"📊 Encontradas {len(barbearias_com_css)} barbearia(s) com CSS no banco:")
        
        for barbearia in barbearias_com_css:
            tamanho_css = len(barbearia.custom_css) if barbearia.custom_css else 0
            logger.info(f"  • {barbearia.nome} ({barbearia.slug})")
            logger.info(f"    └─ Tamanho do CSS: {tamanho_css} caracteres")
            logger.info(f"    └─ Arquivo CSS: static/css/barbearias/{barbearia.slug}.css")
            
            # Limpar o CSS do banco
            barbearia.custom_css = None
        
        # Salvar alterações
        try:
            db.session.commit()
            logger.info("\n" + "=" * 60)
            logger.info("✅ CSS removido do banco de dados com sucesso!")
            logger.info("📁 Todos os estilos agora estão em arquivos físicos:")
            logger.info("   static/css/barbearias/[slug-da-barbearia].css")
            logger.info("=" * 60)
        except Exception:
            db.session.rollback()
            logger.exception("Erro ao limpar CSS")

if __name__ == "__main__":
    limpar_custom_css()
