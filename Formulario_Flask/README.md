# 💈 Sistema de Gestão de Barbearias

Sistema completo para gerenciamento de múltiplas barbearias com agendamentos, serviços e administração.

## 📋 Sobre o Projeto

Sistema multi-tenant desenvolvido em Flask que permite gerenciar várias barbearias independentes em uma única plataforma. Cada barbearia possui seu próprio subdomínio, administradores, serviços e clientes.

## ✨ Funcionalidades Principais

### 🏢 Multi-Tenant
- Sistema com múltiplas barbearias isoladas
- Cada barbearia tem sua própria identidade visual
- Logos personalizadas por estabelecimento
- URLs amigáveis por slug

### 👥 Gestão de Usuários
- **Super Admin:** Controle total do sistema
- **Admins de Barbearia:** Gerenciam sua própria unidade
- **Clientes:** Fazem agendamentos e gerenciam perfil
- Sistema de autenticação com username (admins) e email (clientes)

### 📅 Agendamentos
- Sistema completo de reservas
- Controle de disponibilidade por horário
- Gestão de serviços e preços
- Dashboard com visão geral dos agendamentos

### 🎨 Personalização
- Logo customizada por barbearia
- Identidade visual própria
- Configurações independentes

## 🗂️ Estrutura do Projeto

```
Formulario_Flask/
├── app.py                      # Aplicação principal Flask
├── requirements.txt            # Dependências do projeto
├── meubanco.db                 # Banco de dados SQLite
│
├── scripts/                    # Scripts administrativos
│   ├── criar_admin_interativo.py
│   ├── configurar_super_admin.py
│   └── README.md
│
├── static/                     # Arquivos estáticos
│   ├── css/                   # Estilos
│   ├── js/                    # JavaScript
│   ├── images/                # Imagens fixas
│   └── uploads/               # Uploads dinâmicos
│       └── logos/             # Logos das barbearias
│
├── templates/                  # Templates HTML
│   ├── base.html
│   ├── cliente/               # Templates de clientes
│   ├── admin/                 # Templates de admins
│   └── super_admin/           # Templates de super admin
│
├── docs/                       # Documentação
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── DOCS.md
│   └── QUICKSTART.md
│
└── backups/                    # Backups do banco de dados
```

## 🚀 Como Iniciar

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar a Aplicação
```bash
python app.py
```

### 3. Acessar o Sistema
- **Aplicação:** http://localhost:5000
- **Super Admin:** http://localhost:5000/super_admin/login

### 4. Credenciais Padrão
```
Super Admin:
  Username: lualmeida
  Senha: 562402
```

## 🛠️ Scripts Administrativos

Para gerenciar administradores das barbearias:
```bash
python scripts/criar_admin_interativo.py
```

Veja mais detalhes em `scripts/README.md`

## 📦 Tecnologias

- **Backend:** Flask (Python)
- **Banco de Dados:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **Autenticação:** Werkzeug Security
- **Upload de Arquivos:** Sistema próprio

## 📝 Licença

Ver arquivo `LICENSE`

## 🤝 Contribuindo

Ver arquivo `docs/CONTRIBUTING.md`

## 📚 Documentação Completa

Ver arquivo `docs/DOCS.md`

---

**Desenvolvido com ❤️ para barbearias modernas**
