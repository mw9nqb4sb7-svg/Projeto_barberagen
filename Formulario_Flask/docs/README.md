# Sistema de Gestão para Barbearias

Sistema web completo para gerenciamento de barbearias com arquitetura multi-tenant, desenvolvido em Flask.

## 🚀 Funcionalidades

### 👥 **Multi-Tenant**
- Isolamento completo de dados por barbearia
- URLs únicas para cada estabelecimento (`/slug-da-barbearia/`)
- Gestão independente de usuários, serviços e agendamentos

### 🔐 **Sistema de Autenticação**
- **Super Admin**: Gestão global do sistema
- **Admin de Barbearia**: Gestão completa da barbearia específica
- **Barbeiro**: Visualização de agendamentos próprios
- **Cliente**: Agendamentos e histórico pessoal

### 📅 **Gestão de Agendamentos**
- Sistema completo de reservas
- Controle de disponibilidade por barbearia
- Histórico de agendamentos
- Cancelamento de reservas

### 🛠️ **Área Administrativa**
- Dashboard com métricas
- Gestão de clientes e serviços
- Configuração de disponibilidade
- Relatórios e controles

## 🛠️ Tecnologias

- **Backend**: Flask (Python)
- **Banco de Dados**: SQLAlchemy + SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Autenticação**: Werkzeug Security
- **Template Engine**: Jinja2

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Configuração do Ambiente

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/sistema-barbearia.git
cd sistema-barbearia/Formulario_Flask
```

2. **Crie um ambiente virtual:**
```bash
python -m venv .venv
```

3. **Ative o ambiente virtual:**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

5. **Inicialize o banco de dados:**
```bash
# Opção 1: Apenas barbearias básicas (3 barbearias + serviços)
python inicializar_barbearias.py

# Opção 2: Completo (barbearias + super admin + usuários exemplo)
python inicializar_barbearias.py --completo

# Opção 3: Apenas verificar o banco
python inicializar_barbearias.py --verificar
```

6. **Execute a aplicação:**
```bash
python app.py
```

7. **Acesse no navegador:**
```
http://localhost:5000/
```

## 🎯 Uso

### Acesso ao Sistema

#### Página Inicial
- **URL**: `http://localhost:5000/`
- Lista todas as barbearias disponíveis
- Acesso ao login do Super Admin

#### Super Administrador (se inicializado com --completo)
- **URL**: `http://localhost:5000/super_admin/login`
- **Email**: `superadmin@sistema.com`
- **Senha**: `admin123`
- Pode gerenciar todas as barbearias, usuários e relatórios

#### Barbearias Criadas Automaticamente

**Barbearia Principal**
- **URL**: `http://localhost:5000/principal`
- **Admin**: `admin@principal.com` / `admin123` (apenas com --completo)
- **Barbeiro**: `barbeiro@principal.com` / `barbeiro123` (apenas com --completo)
- **Cliente**: `cliente@principal.com` / `cliente123` (apenas com --completo)

**Barbearia Elite**
- **URL**: `http://localhost:5000/elite`
- **Admin**: `admin@elite.com` / `admin123` (apenas com --completo)

**Barbearia Man**
- **URL**: `http://localhost:5000/man`
- **Admin**: `admin@man.com` / `admin123` (apenas com --completo)

### Scripts Disponíveis

#### Inicialização Unificada
```bash
# Criar apenas barbearias
python inicializar_barbearias.py

# Criar tudo (recomendado para desenvolvimento)
python inicializar_barbearias.py --completo

# Verificar estado do banco
python inicializar_barbearias.py --verificar
```

#### Verificar Barbearias
```bash
python verificar_barbearias.py
```

## 🏗️ Estrutura do Projeto

```
Formulario_Flask/
├── app.py                      # Aplicação principal Flask
├── tenant.py                   # Sistema multi-tenant
├── inicializar_barbearias.py  # Script unificado de inicialização
├── verificar_barbearias.py    # Verificação do banco de dados
├── requirements.txt            # Dependências Python
├── meubanco.db                 # Banco de dados SQLite (criado automaticamente)
├── .scripts-obsoletos/         # Scripts antigos (mantidos para referência)
├── static/                     # Arquivos estáticos (CSS, JS)
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── script.js
└── templates/                  # Templates HTML
    ├── admin/                  # Templates administrativos
    ├── cliente/                # Templates de cliente
    ├── super_admin/            # Templates do super admin
    ├── barbearias_lista.html   # Página inicial
    ├── barbearia_home.html     # Home de cada barbearia
    └── base.html               # Template base
```

## 🔧 Configuração

### Variáveis de Ambiente
```bash
FLASK_SECRET=sua_chave_secreta_aqui
FLASK_ENV=development  # ou production
```

### Banco de Dados
O sistema usa SQLite por padrão. Para produção, altere a configuração em `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/dbname'
```

## 🚀 Deploy

### Railway
1. Conecte seu repositório ao Railway
2. Configure as variáveis de ambiente
3. O deploy será automático

### Heroku
```bash
git add .
git commit -m "Deploy para Heroku"
git push heroku main
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 👨‍💻 Autor

**Lucas Almeida**
- GitHub: [@seu-usuario](https://github.com/seu-usuario)
- Email: seu-email@exemplo.com

## 📞 Suporte

Se você tiver alguma dúvida ou problema, abra uma [issue](https://github.com/seu-usuario/sistema-barbearia/issues) no GitHub.

---

⭐ **Se este projeto foi útil para você, considere dar uma estrela!**