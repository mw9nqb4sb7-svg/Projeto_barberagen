# Migração de Segurança: IDs Autoincrementais → UUIDs

## 📋 Resumo da Implementação

Esta migração substitui os IDs autoincrementais previsíveis por UUIDs (Universally Unique Identifiers) para aumentar significativamente a segurança da aplicação.

---

## ⚠️ Problemas Identificados com IDs Autoincrementais

### 1. **IDOR (Insecure Direct Object Reference)**
- Atacantes podem adivinhar IDs sequenciais (1, 2, 3, 4...)
- Facilita acesso não autorizado a recursos de outros usuários
- Exemplo vulnerável: `/cancelar_reserva/123` → pode tentar 124, 125, etc.

### 2. **Enumeração de Recursos**
- Possível descobrir quantos registros existem no sistema
- Facilita reconhecimento para ataques direcionados
- Expõe informações sobre o crescimento do negócio

### 3. **Validação Insuficiente**
- IDs previsíveis tornam bypass de validação mais fácil
- Facilita testes automatizados de vulnerabilidades

---

## ✅ Solução Implementada: UUIDs

### O que é UUID?
UUID (Universally Unique Identifier) é um identificador de 128 bits representado como:
```
550e8400-e29b-41d4-a716-446655440000
```

### Vantagens
- **Imprevisíveis**: 340 undecilhões de combinações possíveis
- **Não sequenciais**: Impossível adivinhar próximo ID
- **Sem enumeração**: Não revelam quantidade de registros
- **Seguros por design**: Resistentes a ataques de força bruta

---

## 🔧 Mudanças Implementadas

### 1. Modelos de Banco de Dados Atualizados

Foram adicionados campos UUID aos seguintes modelos:

```python
# Barbearia
uuid = db.Column(db.String(36), unique=True, nullable=False, 
                 default=lambda: str(uuid.uuid4()))

# Usuario
uuid = db.Column(db.String(36), unique=True, nullable=False, 
                 default=lambda: str(uuid.uuid4()))

# Servico
uuid = db.Column(db.String(36), unique=True, nullable=False, 
                 default=lambda: str(uuid.uuid4()))

# Reserva
uuid = db.Column(db.String(36), unique=True, nullable=False, 
                 default=lambda: str(uuid.uuid4()))

# DisponibilidadeSemanal
uuid = db.Column(db.String(36), unique=True, nullable=False, 
                 default=lambda: str(uuid.uuid4()))
```

**Características:**
- Campo único e obrigatório
- Geração automática na criação de novos registros
- IDs internos mantidos para relacionamentos (foreign keys)

---

### 2. Rotas Atualizadas (Antes → Depois)

#### ❌ Antes (Vulnerável)
```python
@app.route('/cancelar_reserva/<int:reserva_id>')
def cancelar_reserva(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)
    # ...
```

#### ✅ Depois (Seguro)
```python
@app.route('/cancelar_reserva/<string:reserva_uuid>')
def cancelar_reserva(reserva_uuid):
    reserva = Reserva.query.filter_by(uuid=reserva_uuid).first_or_404()
    # ...
```

#### Rotas Atualizadas:
1. `/cancelar_reserva/<uuid>` - Cancelamento de reservas por clientes
2. `/<slug>/admin/cancelar_agendamento/<uuid>` - Cancelamento por admin
3. `/deletar_cliente/<uuid>` - Exclusão de clientes
4. `/deletar_servico/<uuid>` - Exclusão de serviços
5. `/deletar_agendamento/<uuid>` - Exclusão de agendamentos
6. `/super_admin/barbearia/<uuid>/editar` - Edição de barbearias
7. `/super_admin/barbearia/<uuid>/deletar` - Exclusão de barbearias

---

### 3. Validação de UUID Adicionada

Nova função de segurança em `security.py`:

```python
def validate_uuid(uuid_string):
    """
    Valida se uma string é um UUID válido
    Retorna (is_valid, sanitized_uuid)
    """
    if not uuid_string:
        return False, None
    
    try:
        uuid_obj = uuid.UUID(str(uuid_string), version=4)
        return True, str(uuid_obj)
    except (ValueError, AttributeError):
        return False, None
```

**Uso recomendado:**
```python
is_valid, clean_uuid = validate_uuid(request_uuid)
if not is_valid:
    abort(400, 'UUID inválido')
```

---

## 🚀 Como Aplicar a Migração

### Passo 1: Atualizar o Banco de Dados

Execute o script de migração:

```powershell
cd c:\Users\Micro\OneDrive\Documentos\projetobarber\Projeto_barberagen\Formulario_Flask
python scripts\migrar_para_uuid.py
```

**O script irá:**
- Gerar UUIDs únicos para todos os registros existentes
- Atualizar tabelas: Barbearia, Usuario, Servico, Reserva, DisponibilidadeSemanal
- Verificar que todos os registros receberam UUIDs
- Exibir relatório detalhado

### Passo 2: Atualizar Templates HTML

Busque nos templates por referências a IDs e atualize para usar UUIDs:

```bash
# Buscar URLs que usam IDs
grep -r "url_for.*_id" templates/
```

**Exemplo de atualização:**

❌ Antes:
```html
<a href="{{ url_for('cancelar_reserva', reserva_id=reserva.id) }}">Cancelar</a>
```

✅ Depois:
```html
<a href="{{ url_for('cancelar_reserva', reserva_uuid=reserva.uuid) }}">Cancelar</a>
```

### Passo 3: Atualizar JavaScript

Busque chamadas AJAX que usam IDs:

```javascript
// ❌ Antes
fetch(`/admin/cancelar_agendamento/${reserva.id}`)

// ✅ Depois
fetch(`/admin/cancelar_agendamento/${reserva.uuid}`)
```

---

## 🔍 Verificação de Segurança

### Antes da Migração
```
URL: /cancelar_reserva/1
      /cancelar_reserva/2  ← Previsível!
      /cancelar_reserva/3  ← Fácil enumerar!
```

### Depois da Migração
```
URL: /cancelar_reserva/a3f2e1b9-4c5d-6e7f-8a9b-0c1d2e3f4a5b
      /cancelar_reserva/7b8c9d0e-1f2a-3b4c-5d6e-7f8a9b0c1d2e  ← Imprevisível!
      /cancelar_reserva/2e3f4a5b-6c7d-8e9f-0a1b-2c3d4e5f6a7b  ← Impossível adivinhar!
```

---

## 📊 Testes de Segurança

### Teste 1: Enumeração de IDs
```python
# Antes (VULNERÁVEL)
for i in range(1, 1000):
    response = requests.get(f"/cancelar_reserva/{i}")
    # Consegue descobrir todas as reservas!

# Depois (SEGURO)
for uuid in tentativas_aleatorias:
    response = requests.get(f"/cancelar_reserva/{uuid}")
    # Sempre retorna 404 - impossível adivinhar
```

### Teste 2: IDOR (Acesso Não Autorizado)
```python
# Antes: Fácil testar IDs de outros usuários
# Depois: Impossível adivinhar UUID de outra pessoa
```

---

## ⚡ Performance

### Impacto no Desempenho
- **Tamanho do UUID**: 36 caracteres (vs. 4-8 bytes do INT)
- **Índice único**: Criado automaticamente no campo UUID
- **Query speed**: Praticamente idêntica (índices B-tree)

### Otimizações Aplicadas
- UUIDs como STRING(36) para compatibilidade SQLite
- Índice único para busca rápida
- IDs internos mantidos para foreign keys (performance)

---

## 🔐 Camadas de Segurança Mantidas

A implementação de UUIDs **complementa** (não substitui) as seguranças existentes:

1. ✅ **Autenticação**: Login obrigatório
2. ✅ **Autorização**: Verificação de permissões (admin/cliente)
3. ✅ **Isolamento Multi-tenant**: Validação de barbearia_id
4. ✅ **Rate Limiting**: Proteção contra brute force
5. ✅ **Sanitização**: Prevenção de XSS/SQL Injection
6. ✅ **UUIDs**: Proteção contra IDOR e enumeração ← **NOVO**

---

## 🐛 Troubleshooting

### Erro: "UUID field doesn't exist"
**Causa**: Banco de dados não foi migrado
**Solução**: Execute `python scripts\migrar_para_uuid.py`

### Erro: 404 em rotas antigas
**Causa**: Templates ainda usam IDs em vez de UUIDs
**Solução**: Atualize templates conforme Passo 2

### Erro: "Invalid UUID format"
**Causa**: Tentativa de usar ID numérico em rota UUID
**Solução**: Use sempre `reserva.uuid` em vez de `reserva.id`

---

## 📈 Próximos Passos (Opcional)

### Melhorias Adicionais Sugeridas

1. **UUID Binário (Performance)**
   ```python
   # Para MySQL/PostgreSQL - melhor performance
   uuid = db.Column(db.Binary(16), unique=True, nullable=False)
   ```

2. **Auditoria de Acesso**
   ```python
   audit_log('access_attempt', details={
       'resource': 'reserva',
       'uuid': reserva_uuid,
       'allowed': False
   })
   ```

3. **Tokens de Curta Duração**
   ```python
   # Para operações sensíveis como cancelamento
   token = generate_short_lived_token(reserva.uuid, expires=300)
   ```

---

## 📝 Checklist de Migração

- [x] Adicionar campos UUID aos modelos
- [x] Criar script de migração de dados
- [x] Atualizar rotas para usar UUID
- [x] Adicionar função de validação UUID
- [ ] Atualizar todos os templates HTML
- [ ] Atualizar código JavaScript/AJAX
- [ ] Executar script de migração em produção
- [ ] Testar todas as rotas modificadas
- [ ] Backup do banco antes da migração
- [ ] Monitorar logs de erro pós-migração

---

## 📞 Suporte

Em caso de dúvidas ou problemas na migração:

1. Verifique os logs do script de migração
2. Teste em ambiente de desenvolvimento primeiro
3. Faça backup completo antes de aplicar em produção
4. Revise esta documentação passo a passo

---

## 🎯 Conclusão

A implementação de UUIDs elimina completamente as vulnerabilidades relacionadas a IDs autoincrementais previsíveis, tornando sua aplicação significativamente mais segura contra ataques de:

- ✅ IDOR (Insecure Direct Object Reference)
- ✅ Enumeração de recursos
- ✅ Força bruta em identificadores
- ✅ Reconhecimento de infraestrutura

**Data da Migração**: 4 de dezembro de 2025
**Versão**: 1.0.0
