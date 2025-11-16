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
cd sistema-barbearia
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

5. **Configure o banco de dados:**
```bash
python criar_super_admin.py
python criar_barbearia_man.py
```

6. **Execute a aplicação:**
```bash
python app.py
```

## 🎯 Uso

### Acesso ao Sistema

#### Super Administrador
- **URL**: `http://localhost:5000/super_admin/login`
- **Email**: `superadmin@sistema.com`
- **Senha**: `admin123`

#### Barbearias de Exemplo
Após configurar, você pode acessar:

**Barbearia Man**
- **URL**: `http://localhost:5000/man/`
- **Admin**: `admin@man.com` / `admin123`
- **Barbeiro**: `barbeiro@man.com` / `barbeiro123`

### Scripts de Gestão

#### Criação de Usuários Individual
```bash
python criar_usuarios.py
```

#### Criação de Usuários em Lote
```bash
python criar_usuarios_lote.py
```

## 🏗️ Estrutura do Projeto

```
sistema-barbearia/
├── app.py                 # Aplicação principal Flask
├── tenant.py              # Sistema multi-tenant
├── criar_super_admin.py   # Script para criar super admin
├── criar_barbearia_man.py # Script para criar barbearia exemplo
├── criar_usuarios.py      # Gestão individual de usuários
├── criar_usuarios_lote.py # Gestão em lote de usuários
├── requirements.txt       # Dependências Python
├── static/               # Arquivos estáticos (CSS, JS)
│   ├── css/
│   └── js/
└── templates/            # Templates HTML
    ├── admin/
    ├── cliente/
    ├── super_admin/
    └── base.html
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