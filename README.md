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

### 🆘 Sistema de Suporte
- Formulário de contato integrado ao dashboard admin
- Envio automático para API externa de suporte
- Armazenamento local de chamados com numeração única
- Acompanhamento visual com timeline de status
- Interface rica com indicadores visuais de prioridade
- Detalhes expansíveis com informações completas
- Status em tempo real: Enviado → Em Andamento → Resolvido → Fechado
- Sincronização automática com API externa para detectar chamados cancelados
- Interface visual diferenciada para chamados cancelados (removidos da API)

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

## 🆘 Sistema de Suporte

### Como Usar o Suporte

1. **Acesse o Dashboard Admin:**
   - Faça login como administrador de barbearia
   - No menu lateral, clique em "SUPORTE"

2. **Crie um Novo Chamado:**
   - Preencha o formulário com:
     - Assunto do problema
     - Descrição detalhada
     - Prioridade (Baixa, Média, Alta, Urgente)
   - Clique em "Enviar Chamado"

3. **Acompanhe Seus Chamados:**
   - No menu lateral, clique em "MEUS CHAMADOS"
   - Visualize todos os seus chamados em cards organizados
   - Cada chamado mostra:
     - Número único do chamado (ex: CH000001)
     - Status atual com ícones visuais
     - Timeline de progresso
     - Prioridade com cores distintas
     - Data de criação e última atualização

4. **Detalhes do Chamado:**
   - Clique no botão "Ver Detalhes" para expandir
   - Veja informações completas:
     - Dados do contato
     - Descrição completa
     - Resposta da API externa (quando disponível)
     - Histórico de status

### Status dos Chamados

- **🟡 Enviado:** Chamado criado e enviado para análise
- **🟠 Em Andamento:** Suporte iniciou o atendimento
- **🟢 Resolvido:** Problema foi solucionado
- **⚫ Fechado:** Chamado finalizado
- **❌ Cancelado:** Chamado removido da API externa (sincronizado automaticamente)

### Sincronização com API Externa

O sistema possui sincronização automática para detectar chamados que foram removidos/cancelados na API externa:

```bash
python scripts/sincronizar_chamados.py
```

## 🔧 Biblioteca Cliente da API

### Visão Geral

A biblioteca `cliente_api_suporte.py` fornece uma interface completa para integração programática com o sistema de suporte. Permite enviar chamados e consultar status diretamente do código Python.

### Como Usar

#### Importação
```python
from cliente_api_suporte import enviar_ticket_suporte, consultar_ticket
```

#### Enviando um Chamado
```python
# Dados do chamado
dados_chamado = {
    'assunto': 'Problema com agendamento',
    'descricao': 'Não consigo criar novos agendamentos',
    'prioridade': 'alta',
    'nome_contato': 'João Silva',
    'email_contato': 'joao@exemplo.com',
    'telefone_contato': '(11) 99999-9999'
}

# Enviar chamado
resultado = enviar_ticket_suporte(dados_chamado)
print(f"Chamado criado: {resultado['numero_chamado']}")
```

#### Consultando um Chamado
```python
# Consultar por número do chamado
numero_chamado = 'SUP-20251216-eb9d9c99'
status = consultar_ticket(numero_chamado)
print(f"Status: {status['status']}")
print(f"Prioridade: {status['prioridade']}")
```

### Classe ClienteAPISuporte

Para uso avançado, utilize a classe principal:

```python
from cliente_api_suporte import ClienteAPISuporte

# Inicializar cliente
cliente = ClienteAPISuporte()

# Enviar chamado
resposta = cliente.enviar_ticket(dados_chamado)

# Consultar chamado
info = cliente.consultar_ticket(numero_chamado)

# Verificar se chamado existe
existe = cliente.chamado_existe(numero_chamado)
```

### Tratamento de Erros

A biblioteca inclui tratamento robusto de erros:

```python
try:
    resultado = enviar_ticket_suporte(dados_chamado)
    print("Chamado enviado com sucesso!")
except ValueError as e:
    print(f"Dados inválidos: {e}")
except ConnectionError as e:
    print(f"Erro de conexão: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

### Exemplo Completo

Veja o arquivo `exemplo_uso_api.py` para exemplos completos de uso, incluindo tratamento de erros e validações.

### Funcionalidades

- ✅ Envio de chamados com validação completa
- ✅ Consulta de status em tempo real
- ✅ Tratamento robusto de erros
- ✅ Suporte a webhooks para notificações
- ✅ Validação automática de dados
- ✅ Mapeamento automático de status
- ✅ Interface simples e avançada

### Webhooks para Notificações

A biblioteca suporta webhooks para receber notificações automáticas sobre mudanças de status:

```python
from cliente_api_suporte import ClienteAPISuporte

cliente = ClienteAPISuporte()

# Configurar webhook (opcional)
cliente.configurar_webhook('https://seusistema.com/webhook/suporte')

# O webhook será chamado automaticamente quando:
# - Status do chamado mudar
# - Novo chamado for criado
# - Chamado for atualizado
```

#### Formato do Payload do Webhook

```json
{
  "evento": "status_alterado",
  "numero_chamado": "SUP-20251216-eb9d9c99",
  "status_anterior": "novo",
  "status_novo": "em_andamento",
  "prioridade": "alta",
  "timestamp": "2025-12-16T10:30:00Z",
  "dados_chamado": {
    "assunto": "Problema com agendamento",
    "nome_contato": "João Silva",
    "email_contato": "joao@exemplo.com"
  }
}
```

Este script:
- Verifica o status de todos os chamados na API externa
- Marca como "CANCELADO" chamados que não existem mais na API
- Atualiza status quando há diferenças entre sistemas
- Deve ser executado periodicamente ou via tarefa agendada

### Scripts de Demonstração

Para testar o sistema com dados de exemplo:
```bash
python scripts/criar_chamados_exemplo.py
```

Este script cria 4 chamados com diferentes status para demonstração da interface.

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

Para criar chamados de exemplo e testar o sistema de suporte:
```bash
python scripts/criar_chamados_exemplo.py
```

Para sincronizar status dos chamados com a API externa:
```bash
python scripts/sincronizar_chamados.py
```

### 🔄 Migrações de Banco de Dados

Após atualizações do sistema, execute os scripts de migração necessários:
```bash
# Sempre execute da pasta raiz do projeto
python scripts/adicionar_tabela_chamados.py
python scripts/migrar_para_uuid.py
# ... outros scripts conforme necessário
```

Veja mais detalhes em `scripts/README.md`

## 📦 Tecnologias

- **Backend:** Flask (Python)
- **Banco de Dados:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **Autenticação:** Werkzeug Security
- **Upload de Arquivos:** Sistema próprio
- **Integração API:** Requests (para sistema de suporte)
- **Cliente API:** Biblioteca própria `cliente_api_suporte.py`

## 📝 Licença

Ver arquivo `LICENSE`

## 🤝 Contribuindo

Ver arquivo `docs/CONTRIBUTING.md`

## 📚 Documentação Completa

Ver arquivo `docs/DOCS.md`

---

**Desenvolvido com ❤️ para barbearias modernas**
