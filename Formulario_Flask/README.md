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

## � Deploy no Railway

### Pré-requisitos
- Conta no [Railway](https://railway.app)
- Git instalado localmente

### Passos para Deploy

1. **Clone e prepare o repositório:**
   ```bash
   git clone <seu-repositorio>
   cd Formulario_Flask
   cp .env.example .env  # Configure as variáveis
   ```

2. **Configure as variáveis de ambiente no Railway:**
   - `FLASK_SECRET`: Chave secreta forte (gere com `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `FLASK_DEBUG`: `False` (produção)
   - `DATABASE_URL`: Configurada automaticamente pelo Railway (PostgreSQL)
   - `PORT`: `8080` (padrão Railway)

3. **Deploy via GitHub:**
   - Conecte seu repositório GitHub ao Railway
   - Railway detectará automaticamente o `Procfile` e `requirements.txt`
   - O banco PostgreSQL será provisionado automaticamente

4. **Configuração inicial:**
   ```bash
   # Após deploy, execute no Railway:
   python railway_init.py
   ```

5. **Acesse sua aplicação:**
   - URL será fornecida pelo Railway após deploy

### Arquivos de Configuração para Railway
- `Procfile`: Comando de inicialização
- `runtime.txt`: Versão do Python
- `requirements.txt`: Dependências atualizadas
- `.env`: Variáveis de ambiente (NÃO commite)

### ⚠️ Importante
- Nunca commite o arquivo `.env` (já está no `.gitignore`)
- Configure backups automáticos do banco no Railway
- Monitore logs através do painel do Railway

## �🛠️ Scripts Administrativos

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
