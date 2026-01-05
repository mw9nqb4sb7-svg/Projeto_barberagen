# 🔧 Biblioteca Cliente da API de Suporte

## Visão Geral

A biblioteca `cliente_api_suporte.py` fornece uma interface completa e robusta para integração programática com o sistema de suporte externo. Permite enviar chamados de suporte e consultar seu status diretamente do código Python, com tratamento completo de erros e validações.

## Instalação e Importação

### Importação Básica
```python
from cliente_api_suporte import enviar_ticket_suporte, consultar_ticket
```

### Importação Avançada
```python
from cliente_api_suporte import ClienteAPISuporte
```

## Uso Básico

### Enviando um Chamado

```python
from cliente_api_suporte import enviar_ticket_suporte

# Dados obrigatórios do chamado
dados_chamado = {
    'assunto': 'Problema com agendamento',
    'descricao': 'Não consigo criar novos agendamentos no sistema',
    'prioridade': 'alta',
    'nome_contato': 'João Silva',
    'email_contato': 'joao@exemplo.com',
    'telefone_contato': '(11) 99999-9999'
}

try:
    resultado = enviar_ticket_suporte(dados_chamado)
    print(f"✅ Chamado criado com sucesso!")
    print(f"📋 Número: {resultado['numero_chamado']}")
    print(f"📊 Status: {resultado['status']}")
except Exception as e:
    print(f"❌ Erro ao enviar chamado: {e}")
```

### Consultando um Chamado

```python
from cliente_api_suporte import consultar_ticket

numero_chamado = 'SUP-20251216-eb9d9c99'

try:
    status = consultar_ticket(numero_chamado)
    print(f"📋 Chamado: {status['numero_chamado']}")
    print(f"📊 Status: {status['status']}")
    print(f"🚨 Prioridade: {status['prioridade']}")
    print(f"📅 Criado em: {status['data_criacao']}")
    if 'ultima_atualizacao' in status:
        print(f"🔄 Última atualização: {status['ultima_atualizacao']}")
except Exception as e:
    print(f"❌ Erro ao consultar chamado: {e}")
```

## Uso Avançado com Classe ClienteAPISuporte

### Inicialização

```python
from cliente_api_suporte import ClienteAPISuporte

# Cliente básico
cliente = ClienteAPISuporte()

# Cliente com webhook configurado
cliente_com_webhook = ClienteAPISuporte(webhook_url='https://seusistema.com/webhook/suporte')
```

### Métodos Disponíveis

#### `enviar_ticket(dados_chamado)`

Envia um novo chamado para o sistema de suporte.

**Parâmetros:**
- `dados_chamado` (dict): Dicionário com os dados do chamado

**Retorno:**
- `dict`: Informações do chamado criado incluindo `numero_chamado`, `status`, etc.

**Exceções:**
- `ValueError`: Dados inválidos
- `ConnectionError`: Problema de conectividade
- `Exception`: Outros erros

#### `consultar_ticket(numero_chamado)`

Consulta informações de um chamado específico.

**Parâmetros:**
- `numero_chamado` (str): Número único do chamado

**Retorno:**
- `dict`: Informações completas do chamado

**Exceções:**
- `ValueError`: Chamado não encontrado
- `ConnectionError`: Problema de conectividade

#### `chamado_existe(numero_chamado)`

Verifica se um chamado existe na API externa.

**Parâmetros:**
- `numero_chamado` (str): Número único do chamado

**Retorno:**
- `bool`: True se existe, False caso contrário

#### `configurar_webhook(url)`

Configura URL para receber notificações de webhook.

**Parâmetros:**
- `url` (str): URL do webhook

## Estrutura dos Dados

### Dados para Envio de Chamado

```python
dados_chamado = {
    'assunto': str,           # Obrigatório: Título do problema
    'descricao': str,         # Obrigatório: Descrição detalhada
    'prioridade': str,        # Obrigatório: 'baixa', 'media', 'alta', 'urgente'
    'nome_contato': str,      # Obrigatório: Nome da pessoa de contato
    'email_contato': str,     # Obrigatório: Email válido
    'telefone_contato': str   # Opcional: Telefone de contato
}
```

### Resposta de Chamado Criado

```python
{
    'numero_chamado': 'SUP-20251216-eb9d9c99',
    'status': 'novo',
    'prioridade': 'alta',
    'data_criacao': '2025-12-16T10:30:00Z',
    'assunto': 'Problema com agendamento',
    'nome_contato': 'João Silva',
    'email_contato': 'joao@exemplo.com'
}
```

### Resposta de Consulta de Chamado

```python
{
    'numero_chamado': 'SUP-20251216-eb9d9c99',
    'status': 'em_andamento',
    'prioridade': 'alta',
    'data_criacao': '2025-12-16T10:30:00Z',
    'ultima_atualizacao': '2025-12-16T11:00:00Z',
    'assunto': 'Problema com agendamento',
    'descricao': 'Não consigo criar novos agendamentos',
    'nome_contato': 'João Silva',
    'email_contato': 'joao@exemplo.com',
    'telefone_contato': '(11) 99999-9999'
}
```

## Tratamento de Erros

### Tipos de Exceções

1. **ValueError**: Dados inválidos ou chamado não encontrado
2. **ConnectionError**: Problemas de conectividade com a API
3. **Timeout**: API não respondeu no tempo esperado
4. **Exception**: Outros erros inesperados

### Exemplo de Tratamento Completo

```python
from cliente_api_suporte import enviar_ticket_suporte, consultar_ticket

def enviar_e_monitorar_chamado(dados):
    try:
        # Enviar chamado
        resultado = enviar_ticket_suporte(dados)
        numero = resultado['numero_chamado']
        print(f"Chamado {numero} enviado com sucesso!")

        # Consultar status
        status = consultar_ticket(numero)
        print(f"Status atual: {status['status']}")

        return numero

    except ValueError as e:
        print(f"Dados inválidos: {e}")
        return None
    except ConnectionError as e:
        print(f"Erro de conexão: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None
```

## Webhooks

### Configuração

```python
cliente = ClienteAPISuporte()
cliente.configurar_webhook('https://seusistema.com/api/webhook/suporte')
```

### Eventos Suportados

- `chamado_criado`: Novo chamado enviado
- `status_alterado`: Status do chamado mudou
- `chamado_atualizado`: Informações do chamado foram atualizadas

### Formato do Payload

```json
{
  "evento": "status_alterado",
  "numero_chamado": "SUP-20251216-eb9d9c99",
  "status_anterior": "novo",
  "status_novo": "em_andamento",
  "prioridade": "alta",
  "timestamp": "2025-12-16T11:00:00Z",
  "dados_chamado": {
    "assunto": "Problema com agendamento",
    "nome_contato": "João Silva",
    "email_contato": "joao@exemplo.com"
  }
}
```

## Exemplos Práticos

### Integração com Sistema de Barbearias

```python
from cliente_api_suporte import enviar_ticket_suporte

def reportar_problema_barbearia(barbearia_id, problema, prioridade='media'):
    """Reporta um problema específico de uma barbearia"""

    dados = {
        'assunto': f'Problema na Barbearia {barbearia_id}',
        'descricao': problema,
        'prioridade': prioridade,
        'nome_contato': 'Sistema Automático',
        'email_contato': 'suporte@sistema.com',
        'telefone_contato': '(11) 99999-0000'
    }

    try:
        resultado = enviar_ticket_suporte(dados)
        return resultado['numero_chamado']
    except Exception as e:
        print(f"Erro ao reportar problema: {e}")
        return None
```

### Monitoramento de Chamados

```python
from cliente_api_suporte import consultar_ticket
import time

def monitorar_chamado(numero_chamado, intervalo_segundos=300):
    """Monitora mudanças de status de um chamado"""

    while True:
        try:
            status = consultar_ticket(numero_chamado)
            print(f"[{status['ultima_atualizacao']}] Status: {status['status']}")

            if status['status'] in ['resolvido', 'fechado', 'cancelado']:
                print("Chamado finalizado!")
                break

        except Exception as e:
            print(f"Erro ao consultar: {e}")

        time.sleep(intervalo_segundos)
```

## Validações Implementadas

- **Assunto**: Não vazio, máximo 200 caracteres
- **Descrição**: Não vazia, máximo 2000 caracteres
- **Prioridade**: Deve ser 'baixa', 'media', 'alta' ou 'urgente'
- **Nome**: Não vazio, máximo 100 caracteres
- **Email**: Formato válido de email
- **Telefone**: Formato brasileiro opcional
- **Número do Chamado**: Formato SUP-YYYYMMDD-xxxxxxxx

## Configurações

### URL da API

Por padrão, a biblioteca usa a URL de produção. Para alterar:

```python
import cliente_api_suporte

# Alterar URL da API (exemplo para desenvolvimento)
cliente_api_suporte.API_BASE_URL = 'https://api-suporte-dev.exemplo.com'
```

### Timeouts

```python
cliente_api_suporte.REQUEST_TIMEOUT = 30  # segundos
```

## Testes

Para executar os testes, consulte o arquivo `exemplo_uso_api.py`:

```bash
python exemplo_uso_api.py
```

Este arquivo demonstra:
- Criação de chamados válidos e inválidos
- Consulta de status
- Tratamento de erros
- Validações
- Uso de webhooks

## Suporte e Contribuição

Para dúvidas ou problemas:
1. Consulte esta documentação
2. Verifique o arquivo `exemplo_uso_api.py`
3. Abra um chamado de suporte usando a própria biblioteca!

---

**Versão:** 1.0.0
**Última atualização:** Dezembro 2025</content>
<parameter name="filePath">c:\Users\Micro\OneDrive\Documentos\projetobarber\Projeto_barberagen\Formulario_Flask\docs\API_CLIENTE.md