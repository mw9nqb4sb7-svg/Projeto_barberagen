# 🎨 CSS Personalizado por Barbearia

## 📂 Estrutura

Cada barbearia tem seu próprio arquivo CSS nesta pasta, nomeado pelo **slug** da barbearia:

```
static/css/barbearias/
├── barbearia-lucas.css       # CSS da Barbearia Lucas (Styllo 23)
├── barbearia-leo.css          # CSS da Barbearia Leo
├── barbearia-principal.css    # CSS da Barbearia Principal
└── README.md                  # Este arquivo
```

## ⚙️ Como Funciona

1. **O template `barbearia_home.html` carrega automaticamente** o CSS baseado no slug:
   ```html
   <link rel="stylesheet" href="/static/css/barbearias/{{ barbearia.slug }}.css">
   ```

2. **Cada arquivo CSS sobrescreve os estilos padrão** do sistema para aquela barbearia específica

3. **Sem interface web** - edite os arquivos CSS diretamente no código para evitar conflitos

## 🎯 Como Personalizar uma Barbearia

### 1. Identifique o slug da barbearia
Acesse o Super Admin → Barbearias para ver o slug (ex: `barbearia-lucas`)

### 2. Edite o arquivo CSS correspondente
Abra `static/css/barbearias/barbearia-[slug].css`

### 3. Defina as cores principais
```css
:root {
    --cor-primaria: #6B4423;
    --cor-secundaria: #F5E6D3;
    --cor-destaque: #8B6239;
}
```

### 4. Customize os elementos
```css
/* Navbar */
.custom-nav {
    background: sua-cor !important;
}

/* Títulos */
h1 {
    color: sua-cor !important;
}

/* Botões */
.btn-primary {
    background: sua-cor !important;
}
```

## 📝 Exemplos de Temas

### Tema Vintage (Barbearia Lucas - Styllo 23)
- Cores: Bege (#F5E6D3), Marrom (#6B4423)
- Estilo: Vintage, elegante, quente
- Arquivo: `barbearia-lucas.css`

### Tema Padrão (Azul Premium)
- Cores: Azul (#4a9eff), Ouro (#d4af37)
- Estilo: Moderno, premium, clean
- Usado em: barbearia-leo, barbearia-principal

## ⚠️ Dicas Importantes

1. **Use `!important`** para garantir que os estilos sobrescrevam os padrões
2. **Teste em mobile** - adicione media queries se necessário
3. **Mantenha consistência** - use as mesmas cores em todos os elementos
4. **Backup antes de editar** - faça cópia do arquivo antes de grandes mudanças
5. **Cache do navegador** - use Ctrl+F5 para recarregar sem cache ao testar

## 🔄 Atualizar CSS em Produção

Após editar um arquivo CSS:

1. Salve o arquivo
2. Recarregue a página da barbearia (Ctrl+F5)
3. Verifique se as mudanças foram aplicadas
4. Teste em diferentes navegadores/dispositivos

## 🚀 Criar Tema para Nova Barbearia

```bash
# 1. Identifique o slug (ex: barbearia-nova)
# 2. Crie o arquivo CSS
cp barbearia-principal.css barbearia-nova.css

# 3. Edite as cores no novo arquivo
# 4. Acesse /{slug} para ver o resultado
```

## 📚 Recursos

- Paletas de cores: [Coolors.co](https://coolors.co)
- Gradientes: [CSS Gradient](https://cssgradient.io)
- Sombras: [Box Shadows](https://box-shadow.dev)
