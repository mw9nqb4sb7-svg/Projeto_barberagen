# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2025-11-27

### 🎉 Adicionado
- Script unificado de inicialização (`inicializar_barbearias.py`)
- Opção `--completo` para criar barbearias + super admin + usuários exemplo
- Opção `--verificar` para verificar estado do banco
- Arquivo QUICKSTART.md com guia de início rápido
- Criação automática de 3 barbearias (Principal, Elite, Man)
- Criação automática de serviços básicos para cada barbearia
- Criação opcional de usuários exemplo (admin, barbeiro, cliente)

### ♻️ Refatorado
- Consolidação de scripts duplicados em um único arquivo
- Movimentação de scripts obsoletos para `.scripts-obsoletos/`
- Movimentação de documentação histórica para `.docs-historico/`
- Atualização do README.md com instruções claras
- Melhoria no `.gitignore` para incluir pastas organizacionais

### 🗑️ Removido (Movido)
- `criar_barbearia_man.py` → `.scripts-obsoletos/`
- `criar_segunda_barbearia.py` → `.scripts-obsoletos/`
- `criar_usuarios.py` → `.scripts-obsoletos/`
- `criar_usuarios_lote.py` → `.scripts-obsoletos/`
- `criar_super_admin.py` → `.scripts-obsoletos/`
- `setup.py` → `.scripts-obsoletos/`
- Documentação histórica → `.docs-historico/`

### 🐛 Corrigido
- Problema de "barbearia não encontrada" ao clicar nos cards
- Duplicação de código entre scripts
- Confusão na documentação com múltiplos scripts

## [1.0.0] - 2025-11-XX

### 🎉 Adicionado
- Sistema multi-tenant completo
- Autenticação com múltiplos níveis (Super Admin, Admin, Barbeiro, Cliente)
- Sistema de agendamentos
- Gestão de serviços por barbearia
- Dashboard administrativo
- Interface responsiva
- Sistema de disponibilidade semanal

---

## Legenda

- 🎉 **Adicionado**: Para novas funcionalidades
- ♻️ **Refatorado**: Para mudanças no código existente
- 🐛 **Corrigido**: Para correção de bugs
- 🗑️ **Removido**: Para funcionalidades removidas
- 🔒 **Segurança**: Para correções de vulnerabilidades
- 📚 **Documentação**: Para mudanças na documentação
