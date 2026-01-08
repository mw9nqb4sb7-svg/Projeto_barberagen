"""
Script para adicionar CSRF tokens em todos os formulários HTML
"""
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / 'templates'

def adicionar_csrf_em_formularios():
    """Adiciona CSRF token em todos os formulários que não têm"""
    
    print("=" * 60)
    print("Adicionando CSRF tokens aos formulários")
    print("=" * 60)
    
    # Padrões para detectar formulários
    form_pattern = re.compile(r'<form[^>]*method=["\']POST["\'][^>]*>', re.IGNORECASE)
    csrf_pattern = re.compile(r'csrf_token', re.IGNORECASE)
    
    arquivos_modificados = 0
    formularios_protegidos = 0
    
    # Percorrer todos os arquivos HTML
    for html_file in TEMPLATES_DIR.rglob('*.html'):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Verificar se tem formulários POST
            formularios = form_pattern.findall(conteudo)
            
            if not formularios:
                continue
            
            # Verificar se já tem CSRF token
            if csrf_pattern.search(conteudo):
                print(f"  ✓ {html_file.relative_to(BASE_DIR)} - Já possui CSRF token")
                continue
            
            # Adicionar CSRF token após cada <form method="POST">
            def add_csrf(match):
                form_tag = match.group(0)
                csrf_line = '\n                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>'
                return form_tag + csrf_line
            
            conteudo_novo = form_pattern.sub(add_csrf, conteudo)
            
            # Salvar arquivo modificado
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(conteudo_novo)
            
            arquivos_modificados += 1
            formularios_protegidos += len(formularios)
            print(f"  ✅ {html_file.relative_to(BASE_DIR)} - {len(formularios)} formulário(s) protegido(s)")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {html_file.relative_to(BASE_DIR)}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Concluído!")
    print(f"Arquivos modificados: {arquivos_modificados}")
    print(f"Formulários protegidos: {formularios_protegidos}")
    print("=" * 60)

if __name__ == '__main__':
    adicionar_csrf_em_formularios()
