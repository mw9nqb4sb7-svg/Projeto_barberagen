#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para aplicar CSS tema Styllo 23 na Barbearia Lucas"""

from app import app, db, Barbearia

CSS_STYLLO23 = """/* Tema Barbearia Styllo 23 - Vintage Bege e Marrom */
:root {
    --styllo-bege: #F5E6D3;
    --styllo-marrom: #6B4423;
    --styllo-marrom-escuro: #4a2f18;
    --styllo-marrom-claro: #8B6239;
    --styllo-creme: #FFF8E7;
}

/* Background geral */
body {
    background: linear-gradient(135deg, #1a1410 0%, #2a1f18 50%, #1a1410 100%) !important;
}

body::before {
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(107, 68, 35, 0.03) 2px,
        rgba(107, 68, 35, 0.03) 4px
    ) !important;
}

/* Navbar */
.custom-nav {
    background: linear-gradient(180deg, rgba(26, 20, 16, 0.98) 0%, rgba(42, 31, 24, 0.95) 100%) !important;
    border-bottom: 3px solid var(--styllo-marrom) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.9), 0 2px 16px rgba(107, 68, 35, 0.3) !important;
}

/* CORREÇÃO: Nome da barbearia na navbar */
.nav-brand,
.nav-brand *,
.nav-brand span,
.nav-brand-text,
.nav-brand-text * {
    color: var(--styllo-bege) !important;
    background: transparent !important;
    -webkit-text-fill-color: var(--styllo-bege) !important;
    -webkit-background-clip: unset !important;
    background-clip: unset !important;
    text-shadow: 0 0 20px rgba(245, 230, 211, 0.3) !important;
    filter: none !important;
}

nav span,
nav .nav-brand span,
nav span[style] {
    color: var(--styllo-bege) !important;
    -webkit-text-fill-color: var(--styllo-bege) !important;
    background: transparent !important;
}

.nav-link {
    color: var(--styllo-bege) !important;
}

.nav-link:hover {
    border-color: var(--styllo-marrom) !important;
    background: rgba(107, 68, 35, 0.2) !important;
    color: var(--styllo-creme) !important;
    box-shadow: 0 5px 15px rgba(107, 68, 35, 0.3) !important;
}

/* CORREÇÃO: Título principal H1 */
h1,
h1 *,
h1 span,
h1 span[style] {
    color: var(--styllo-bege) !important;
    -webkit-text-fill-color: var(--styllo-bege) !important;
    background: transparent !important;
    -webkit-background-clip: unset !important;
    background-clip: unset !important;
    text-shadow: 0 4px 8px rgba(107, 68, 35, 0.6) !important;
    filter: drop-shadow(0 4px 8px rgba(107, 68, 35, 0.6)) !important;
}

h1 > span:nth-child(2),
h1 br + span {
    color: var(--styllo-marrom-claro) !important;
    -webkit-text-fill-color: var(--styllo-marrom-claro) !important;
    text-shadow: 0 0 20px rgba(139, 98, 57, 0.6) !important;
}

h2 {
    color: var(--styllo-bege) !important;
    border-left-color: var(--styllo-marrom) !important;
}

h3 {
    color: var(--styllo-bege) !important;
}

p, span, div {
    color: var(--styllo-creme) !important;
}

.hero-section p {
    color: rgba(245, 230, 211, 0.9) !important;
}

/* Botões */
.btn-primary,
a[style*="background: #4a9eff"],
a[style*="background: linear-gradient(135deg, #4a9eff"] {
    background: linear-gradient(135deg, var(--styllo-marrom) 0%, var(--styllo-marrom-escuro) 100%) !important;
    color: var(--styllo-creme) !important;
    border-color: var(--styllo-marrom-claro) !important;
    box-shadow: 0 8px 32px rgba(107, 68, 35, 0.5) !important;
}

.btn-primary:hover,
a[style*="background: #4a9eff"]:hover {
    background: linear-gradient(135deg, var(--styllo-marrom-claro) 0%, var(--styllo-marrom) 100%) !important;
    box-shadow: 0 16px 48px rgba(107, 68, 35, 0.7), 0 0 80px rgba(245, 230, 211, 0.3) !important;
}

.btn-secondary,
a[style*="border: 2px solid #4a9eff"] {
    border-color: var(--styllo-marrom) !important;
    color: var(--styllo-bege) !important;
    background: rgba(107, 68, 35, 0.1) !important;
}

.btn-secondary:hover {
    border-color: var(--styllo-marrom-claro) !important;
    background: rgba(107, 68, 35, 0.25) !important;
    color: var(--styllo-creme) !important;
}

/* Cards e containers */
div[style*="background: rgba(255, 255, 255, 0.1)"] {
    background: rgba(107, 68, 35, 0.25) !important;
    border: 2px solid rgba(107, 68, 35, 0.4) !important;
}

.grid > div,
div[style*="background: rgba(26, 26, 26"] {
    background: linear-gradient(135deg, rgba(42, 31, 24, 0.7) 0%, rgba(26, 20, 16, 0.8) 100%) !important;
    border-color: rgba(107, 68, 35, 0.4) !important;
}

.grid > div:hover {
    border-color: var(--styllo-marrom) !important;
    box-shadow: 0 10px 40px rgba(107, 68, 35, 0.4) !important;
}

.grid > div h3 {
    color: var(--styllo-bege) !important;
}

.grid > div p {
    color: rgba(245, 230, 211, 0.8) !important;
}

/* Destaques de texto */
span[style*="color: var(--gold)"],
span[style*="color: #4a9eff"] {
    color: var(--styllo-marrom-claro) !important;
    text-shadow: 0 0 20px rgba(139, 98, 57, 0.6) !important;
}

/* Elementos especiais */
div[style*="background: linear-gradient(135deg, var(--gold-dark)"] {
    background: linear-gradient(135deg, var(--styllo-marrom) 0%, var(--styllo-marrom-escuro) 100%) !important;
    border-color: var(--styllo-marrom-claro) !important;
}

div[style*="border: 2px solid rgba(74, 158, 255, 0.15)"] {
    border-color: rgba(107, 68, 35, 0.3) !important;
    background: rgba(42, 31, 24, 0.5) !important;
}

div[style*="border: 2px solid rgba(74, 158, 255, 0.15)"]:hover {
    border-color: var(--styllo-marrom) !important;
    background: rgba(107, 68, 35, 0.15) !important;
}

/* Footer */
footer {
    background: linear-gradient(180deg, transparent 0%, rgba(26, 20, 16, 0.6) 50%, rgba(42, 31, 24, 0.9) 100%) !important;
    border-top-color: var(--styllo-marrom) !important;
}

footer h3,
footer h4 {
    color: var(--styllo-bege) !important;
}

footer p,
footer span {
    color: rgba(245, 230, 211, 0.8) !important;
}

footer a {
    color: var(--styllo-bege) !important;
}

footer a:hover {
    color: var(--styllo-creme) !important;
}

footer a[style*="border-radius: 50%"] {
    background: rgba(107, 68, 35, 0.2) !important;
    border-color: rgba(107, 68, 35, 0.4) !important;
}

footer a[style*="border-radius: 50%"]:hover {
    background: rgba(107, 68, 35, 0.4) !important;
    border-color: var(--styllo-marrom) !important;
}

/* Logo BarberConnect */
a[href="/"] div span:first-child {
    color: var(--styllo-bege) !important;
}

a[href="/"] div span:last-child {
    color: var(--styllo-marrom-claro) !important;
}

/* Correções finais de cores azuis */
[style*="color: #4a9eff"],
[style*="color: rgb(74, 158, 255)"] {
    color: var(--styllo-bege) !important;
}

[style*="-webkit-text-fill-color: #4a9eff"] {
    -webkit-text-fill-color: var(--styllo-bege) !important;
}
"""

def main():
    with app.app_context():
        # Buscar Barbearia Lucas
        barbearia = Barbearia.query.filter_by(slug='barbearia-lucas').first()
        
        if not barbearia:
            print("❌ Barbearia Lucas não encontrada!")
            return
        
        # Aplicar CSS
        barbearia.custom_css = CSS_STYLLO23
        db.session.commit()
        
        print("✅ CSS Styllo 23 aplicado com sucesso na Barbearia Lucas!")
        print(f"📊 Barbearia: {barbearia.nome}")
        print(f"🔗 URL: /barbearia-{barbearia.slug}")
        print(f"🎨 Tema: Vintage Bege e Marrom")

if __name__ == "__main__":
    main()
