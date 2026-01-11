# 🚀 Como Rodar o Servidor Localmente

## 📋 Pré-requisitos

- ✅ Python 3.10+ instalado
- ✅ Git instalado (para clonar o projeto)

## ⚡ Início Rápido (Windows)

### Opção 1: Usando o Script Automático (RECOMENDADO)

1. **Execute o arquivo `run_local.bat`:**
   ```
   Duplo clique em: run_local.bat
   ```

   Ou via terminal:
   ```powershell
   cd "c:\Users\Micro\OneDrive\Documentos\projetobarber\Projeto_barberagen"
   .\run_local.bat
   ```

2. **Aguarde a instalação** (primeira vez demora mais)

3. **Acesse no navegador:**
   - http://localhost:5000

### Opção 2: Comandos Manuais

```powershell
# 1. Navegar até a pasta do projeto
cd "c:\Users\Micro\OneDrive\Documentos\projetobarber\Projeto_barberagen"

# 2. Criar ambiente virtual (apenas primeira vez)
py -m venv venv

# 3. Ativar ambiente virtual
.\venv\Scripts\activate

# 4. Instalar dependências (apenas primeira vez)
pip install -r requirements.txt

# 5. Rodar o servidor
py app.py
```

## 🌐 Acessando o Sistema

Após iniciar o servidor, acesse:

- **Página Principal:** http://localhost:5000
- **Login Cliente:** http://localhost:5000/login
- **Super Admin:** http://localhost:5000/super_admin/login
- **Debug Templates:** http://localhost:5000/_templates_debug

## 🔑 Credenciais Padrão

### Super Admin
- **Email/Username:** Configure via scripts/configurar_super_admin.py

### Criar Admin Interativo
```powershell
.\venv\Scripts\activate
py scripts/criar_admin_interativo.py
```

## 📂 Estrutura de Arquivos

```
Projeto_barberagen/
├── app.py                  # Aplicação principal Flask
├── meubanco.db            # Banco de dados SQLite (criado automaticamente)
├── requirements.txt       # Dependências do projeto
├── run_local.bat         # Script para rodar localmente (Windows)
├── venv/                 # Ambiente virtual (criado automaticamente)
├── static/               # Arquivos estáticos (CSS, JS, imagens)
├── templates/            # Templates HTML
└── scripts/              # Scripts utilitários
```

## 🛠️ Comandos Úteis

### Parar o Servidor
```
Pressione: CTRL + C
```

### Limpar o Cache do Navegador
```
No navegador: CTRL + SHIFT + DELETE
Ou: CTRL + F5 (hard refresh)
```

### Recriar o Banco de Dados
```powershell
# ATENÇÃO: Isso apaga todos os dados!
del meubanco.db
py app.py
```

### Ver Logs em Tempo Real
Os logs aparecem direto no terminal onde o servidor está rodando.

### Abrir Console do Navegador
```
Pressione: F12
```

## 🐛 Troubleshooting

### Erro: "Python was not found"
**Solução:** Instale Python de https://www.python.org/downloads/
- ✅ Marque "Add Python to PATH" durante instalação

### Erro: "pip não é reconhecido"
**Solução:** 
```powershell
py -m pip install --upgrade pip
```

### Erro: "Porta 5000 já está em uso"
**Solução:** Mude a porta no arquivo ou mate o processo:
```powershell
# Ver processos na porta 5000
netstat -ano | findstr :5000

# Matar processo (substitua PID pelo número encontrado)
taskkill /PID <PID> /F
```

Ou altere a porta:
```powershell
set PORT=8000
py app.py
```

### Erro ao instalar dependências
**Solução:** Instale o Visual C++ Build Tools
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

### O servidor não recarrega automaticamente
**Solução:** Reinicie manualmente (CTRL+C e rode novamente)
- Ou desative: `use_reloader=False` já está configurado

## 📊 Modo Debug vs Produção

### Local (Desenvolvimento)
- ✅ Debug mode: ATIVADO
- ✅ Host: localhost (127.0.0.1)
- ✅ Porta: 5000
- ✅ Banco: SQLite (meubanco.db)

### Railway (Produção)
- ❌ Debug mode: DESATIVADO
- 🌍 Host: 0.0.0.0
- 🔢 Porta: Definida pelo Railway
- 🐘 Banco: PostgreSQL

## 🔄 Sincronizar com Railway

```powershell
# Puxar últimas alterações do Git
git pull origin main

# Fazer alterações locais
# ... editar arquivos ...

# Enviar para Railway
git add .
git commit -m "Suas alterações"
git push origin main
```

O Railway detecta automaticamente e faz deploy!

## 📝 Testar Funcionalidades

### Testar Loading Screen
1. Abra: http://localhost:5000/perfil
2. Clique em "🔄 Testar Loading"
3. Ou submeta qualquer formulário

### Testar CSS do Perfil
1. Abra: http://localhost:5000/perfil
2. Faça hard refresh: CTRL + F5
3. Inputs devem ter fundo BRANCO

### Ver Console do Browser
1. Pressione F12
2. Vá em Console
3. Deve ver: "Script carregado - LoadingOverlay disponível"

## 🆘 Ajuda

### Documentação do Projeto
- [Loading Screen](docs/LOADING_SCREEN.md)
- [Personalizações](docs/PERSONALIZACAO_BARBEARIAS.md)
- [Segurança](SECURITY.md)
- [Changelog](docs/CHANGELOG.md)

### Comandos Git
```powershell
# Ver status
git status

# Ver diferenças
git diff

# Desfazer alterações (cuidado!)
git restore arquivo.py
```

## 🎯 Dicas de Desenvolvimento

1. **Sempre teste localmente antes de fazer push**
2. **Use hard refresh (CTRL+F5) após mudanças CSS/JS**
3. **Mantenha o terminal aberto para ver erros**
4. **Faça commits pequenos e frequentes**
5. **Use o console do navegador (F12) para debug**

## 📞 Suporte

- Abra o console do navegador (F12) e envie screenshot dos erros
- Verifique o terminal onde o servidor está rodando
- Confira os logs em: `logs/audit_YYYY-MM.jsonl`

---

**✅ Pronto! Agora você pode desenvolver localmente e testar todas as funcionalidades!**
