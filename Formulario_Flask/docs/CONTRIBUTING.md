# Guia de Contribuição

Obrigado por considerar contribuir para o Sistema de Gestão para Barbearias! 

## 🚀 Como Começar

### 1. Fork e Clone
```bash
git fork https://github.com/seu-usuario/sistema-barbearia.git
git clone https://github.com/seu-usuario/sistema-barbearia.git
cd sistema-barbearia
```

### 2. Configuração do Ambiente
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python setup.py
```

### 3. Executar o Projeto
```bash
python app.py
```

## 🛠️ Tipos de Contribuição

### 🐛 Reportar Bugs
- Use o template de issue para bugs
- Inclua passos para reproduzir
- Informe versão do Python e SO
- Screenshots são bem-vindos

### ✨ Sugerir Funcionalidades
- Use o template de issue para features
- Descreva o problema que resolve
- Proponha uma solução
- Considere a arquitetura multi-tenant

### 💻 Contribuir com Código
- Siga o estilo de código existente
- Teste suas alterações
- Atualize documentação se necessário
- Mantenha commits pequenos e focados

## 📋 Padrões de Código

### Python (PEP 8)
```python
# Nomes de função: snake_case
def criar_usuario():
    pass

# Nomes de classe: PascalCase
class UsuarioBarbearia:
    pass

# Constantes: UPPER_CASE
TIPOS_USUARIO = ['admin', 'barbeiro', 'cliente']
```

### Flask Routes
```python
# Sempre incluir docstring
@app.route('/<slug>/admin/funcao')
def admin_funcao(slug):
    """Descrição clara da função"""
    
    # Verificações de segurança primeiro
    if 'usuario_id' not in session:
        return redirect(url_for('login', slug=slug))
    
    if not g.tenant.is_admin():
        flash('Acesso negado', 'error')
        return redirect(url_for('dashboard', slug=slug))
```

### Templates
```html
<!-- Sempre estender base.html -->
{% extends "base.html" %}
{% block title %}Título da Página{% endblock %}

{% block content %}
<!-- Usar classes CSS consistentes -->
<div class="card-form">
    <h2>Título</h2>
    <!-- URLs sempre com slug -->
    <a href="{{ url_for('funcao', slug=barbearia.slug) }}">Link</a>
</div>
{% endblock %}
```

## 🧪 Testes

### Testando Funcionalidade
1. **Login como diferentes tipos de usuário**
2. **Testar isolamento entre barbearias**
3. **Verificar permissões de acesso**
4. **Testar em diferentes navegadores**

### Dados de Teste
```bash
# Criar ambiente de teste
python setup.py

# Usar scripts utilitários
python criar_usuarios_lote.py
```

## 📝 Documentação

### Atualizando README.md
- Mantenha instruções claras
- Atualize screenshots se necessário
- Documente novas funcionalidades

### Atualizando DOCS.md
- Explique arquitetura de novas features
- Documente padrões de código
- Inclua exemplos práticos

## 🔄 Processo de Pull Request

### 1. Preparação
```bash
git checkout -b feature/nome-da-feature
# Fazer alterações
git add .
git commit -m "feat: adicionar nova funcionalidade"
```

### 2. Formato de Commit
```
feat: adicionar nova funcionalidade
fix: corrigir bug específico
docs: atualizar documentação
style: ajustes de formatação
refactor: refatoração de código
test: adicionar testes
```

### 3. Antes de Enviar
- [ ] Código testado localmente
- [ ] Documentação atualizada
- [ ] Commits com mensagens claras
- [ ] Não há conflitos com main

### 4. Pull Request
- Descreva o que foi alterado
- Referencie issues relacionadas
- Adicione screenshots se aplicável
- Aguarde review

## 🏗️ Arquitetura

### Multi-Tenant
- Toda nova funcionalidade deve respeitar isolamento
- Sempre filtrar por `barbearia_id`
- Usar contexto `g.tenant`

### Permissões
- Verificar sempre `g.tenant.is_admin()`
- Implementar verificações granulares
- Redirecionar apropriadamente

### URLs
- Seguir padrão `/<slug>/` para barbearias
- Super admin usa `/super_admin/`
- Sempre incluir slug em `url_for()`

## 🤝 Comunidade

### Código de Conduta
- Seja respeitoso e inclusivo
- Ajude iniciantes
- Foque no código, não na pessoa
- Celebre contribuições de todos os tamanhos

### Comunicação
- Issues para discussões técnicas
- Discussions para ideias gerais
- Email para assuntos sensíveis

## 🎯 Próximas Funcionalidades

### Prioridade Alta
- [ ] Sistema de notificações
- [ ] Integração com WhatsApp
- [ ] Relatórios avançados
- [ ] Sistema de pagamento

### Prioridade Média
- [ ] PWA (Progressive Web App)
- [ ] Dark mode
- [ ] Multilíngue
- [ ] API REST

### Contribuições Procuradas
- Frontend (CSS/JavaScript)
- Testes automatizados
- Documentação
- Tradução
- Design UX/UI

---

💝 **Obrigado por contribuir! Cada linha de código, cada bug reportado, cada sugestão faz a diferença!**