# 🚀 Guia de Início Rápido

Este guia te ajudará a configurar e executar o sistema em menos de 5 minutos.

## ⚡ Instalação Rápida

### 1. Preparar Ambiente

```bash
# Ativar ambiente virtual (se já existe)
# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Inicializar Sistema

#### Opção A: Instalação Completa (Recomendado)
```bash
python inicializar_barbearias.py --completo
```

Isso criará:
- ✅ 3 barbearias (Principal, Elite, Man)
- ✅ Serviços básicos para cada barbearia
- ✅ Super Admin do sistema
- ✅ Usuários de exemplo (admin, barbeiro, cliente) para cada barbearia

#### Opção B: Apenas Barbearias
```bash
python inicializar_barbearias.py
```

Cria apenas as barbearias e serviços, sem usuários.

### 3. Iniciar Servidor

```bash
python app.py
```

### 4. Acessar Sistema

Abra seu navegador em: **http://localhost:5000/**

## 🔑 Credenciais Padrão (--completo)

### Super Admin
- **URL**: http://localhost:5000/super_admin/login
- **Email**: `superadmin@sistema.com`
- **Senha**: `admin123`

### Barbearia Principal
- **URL**: http://localhost:5000/principal
- **Admin**: `admin@principal.com` / `admin123`
- **Barbeiro**: `barbeiro@principal.com` / `barbeiro123`
- **Cliente**: `cliente@principal.com` / `cliente123`

### Barbearia Elite
- **URL**: http://localhost:5000/elite
- **Admin**: `admin@elite.com` / `admin123`

### Barbearia Man
- **URL**: http://localhost:5000/man
- **Admin**: `admin@man.com` / `admin123`

## 🛠️ Comandos Úteis

### Verificar Estado do Banco
```bash
python inicializar_barbearias.py --verificar
# ou
python verificar_barbearias.py
```

### Recriar Banco de Dados
```bash
# Deletar banco atual
del meubanco.db  # Windows
rm meubanco.db   # Linux/Mac

# Recriar com dados completos
python inicializar_barbearias.py --completo
```

## 📋 Estrutura de URLs

| Tipo | URL | Descrição |
|------|-----|-----------|
| **Sistema** | `/` | Página inicial - lista de barbearias |
| **Super Admin** | `/super_admin/login` | Login do super administrador |
| **Super Admin** | `/super_admin/dashboard` | Dashboard administrativo |
| **Barbearia** | `/<slug>` | Home de uma barbearia específica |
| **Login** | `/<slug>/login` | Login de usuários da barbearia |
| **Cadastro** | `/<slug>/cadastro` | Cadastro de novos clientes |
| **Dashboard** | `/<slug>/dashboard` | Dashboard (varia por tipo de usuário) |

## 🎯 Próximos Passos

1. **Teste o Super Admin**: Faça login e explore o painel administrativo
2. **Acesse uma Barbearia**: Clique em um card na página inicial
3. **Crie um Cliente**: Faça cadastro em uma das barbearias
4. **Teste Agendamento**: Faça login como cliente e crie um agendamento
5. **Veja como Admin**: Faça login como admin e veja os agendamentos

## ❓ Problemas Comuns

### "Barbearia não encontrada"
**Solução**: Execute `python inicializar_barbearias.py`

### "Erro ao conectar ao banco"
**Solução**: Verifique se o arquivo `meubanco.db` tem permissões corretas

### "Módulo não encontrado"
**Solução**: Verifique se o ambiente virtual está ativado e execute `pip install -r requirements.txt`

## 📚 Documentação Completa

Para informações detalhadas, consulte:
- [README.md](README.md) - Documentação completa
- [DOCS.md](DOCS.md) - Documentação técnica
- [CONTRIBUTING.md](CONTRIBUTING.md) - Guia de contribuição

---

💡 **Dica**: Para desenvolvimento, sempre use a opção `--completo` para ter dados de teste prontos!
