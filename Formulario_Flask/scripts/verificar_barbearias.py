#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar barbearias no banco de dados

NOTA: Este script foi simplificado.
Para inicialização completa, use: python inicializar_barbearias.py --completo
Para apenas verificar, use: python inicializar_barbearias.py --verificar
"""

from app import app, db, Barbearia, Servico, UsuarioBarbearia

def verificar_barbearias():
    with app.app_context():
        print("\n=== VERIFICANDO BARBEARIAS NO BANCO ===\n")
        
        barbearias = Barbearia.query.all()
        
        if not barbearias:
            print("❌ NENHUMA BARBEARIA ENCONTRADA!")
            print("\n💡 Execute o comando abaixo para inicializar o sistema:")
            print("   python inicializar_barbearias.py --completo")
            return
        
        print(f"✅ Encontradas {len(barbearias)} barbearia(s):\n")
        
        for b in barbearias:
            status = "✅ ATIVA" if b.ativa else "❌ INATIVA"
            servicos_count = Servico.query.filter_by(barbearia_id=b.id, ativo=True).count()
            usuarios_count = UsuarioBarbearia.query.filter_by(barbearia_id=b.id, ativo=True).count()
            
            print(f"  ID: {b.id}")
            print(f"  Nome: {b.nome}")
            print(f"  Slug: {b.slug}")
            print(f"  Status: {status}")
            print(f"  URL: http://localhost:5000/{b.slug}")
            print(f"  Serviços: {servicos_count}")
            print(f"  Usuários: {usuarios_count}")
            print("-" * 50)

if __name__ == '__main__':
    verificar_barbearias()
