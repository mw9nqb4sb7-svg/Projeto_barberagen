# 📜 Scripts Administrativos

Scripts Python para gerenciamento e manutenção do sistema de barbearias.

## 🎯 Scripts Principais

### `criar_admin_interativo.py`
**Descrição:** Gerenciamento completo de administradores  
**Funcionalidades:**
- ➕ Criar novos administradores para barbearias
- 🗑️ Excluir administradores existentes
- 🔐 Autenticação obrigatória de super admin

**Como usar:**
```bash
python scripts/criar_admin_interativo.py
```

---

## 🔧 Scripts de Configuração

### `configurar_super_admin.py`
Cria ou atualiza o super administrador do sistema com credenciais específicas.

### `adicionar_coluna_logo.py`
Migração: Adiciona coluna 'logo' na tabela barbearias.

### `adicionar_username.py`
Migração: Adiciona coluna 'username' na tabela usuarios.

### `adicionar_logo_leo.py`
Script específico para adicionar logo da Barbearia Leo Cortes.

---

## 🔄 Scripts de Manutenção

### `inicializar_barbearias.py`
Inicializa barbearias padrão no sistema.

### `resetar_admins.py`
Reseta senhas de administradores quando necessário.

### `verificar_barbearias.py`
Verifica integridade e configurações das barbearias cadastradas.

### `tenant.py`
Funções auxiliares para sistema multi-tenant.

---

## ⚠️ Importante

- Todos os scripts requerem estar na pasta raiz do projeto
- O arquivo `meubanco.db` precisa existir na pasta principal
- Scripts de migração devem ser executados apenas uma vez
- Sempre faça backup antes de executar scripts de manutenção

---

## 🚀 Execução

**Da pasta raiz do projeto:**
```bash
python scripts/nome_do_script.py
```

**Criando atalho na área de trabalho:**
1. Clique com botão direito no script
2. "Criar atalho"
3. Arraste o atalho para onde desejar
