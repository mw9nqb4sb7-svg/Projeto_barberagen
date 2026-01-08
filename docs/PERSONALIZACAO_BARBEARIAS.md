# Sistema de Personalização de Barbearias

## ✅ Status: IMPLEMENTADO E FUNCIONAL

A funcionalidade de personalização por barbearia está totalmente implementada no sistema.

## 🎨 Recursos Disponíveis

### 1. **Personalização Visual**
Cada barbearia pode customizar sua home page através do painel Super Admin:

- **Cores:**
  - Cor Primária (botões, destaques)
  - Cor Secundária (hover, elementos secundários)
  - Cor do Texto

- **Textos:**
  - Título Principal (hero_titulo) - Use `|` para dividir em duas cores
  - Subtítulo (hero_subtitulo)
  - Slogan da barbearia

### 2. **Cards de Serviços (4 cards personalizáveis)**
Cada card possui:
- Ícone (emoji)
- Título
- Descrição

**Padrão dos cards:**
- Card 1: Corte masculino ✂️
- Card 2: Barba completa 🧔
- Card 3: Combo premium 💈
- Card 4: Agendamento fácil 📅

## 🗄️ Estrutura do Banco de Dados

### Tabela: `barbearia`

**Colunas de personalização adicionadas:**

```sql
-- Personalização Visual
hero_titulo TEXT
hero_subtitulo TEXT
slogan VARCHAR(200)
cor_primaria VARCHAR(10)
cor_secundaria VARCHAR(10)
cor_texto VARCHAR(10)

-- Card 1
card1_icone VARCHAR(10)
card1_titulo VARCHAR(100)
card1_descricao TEXT

-- Card 2
card2_icone VARCHAR(10)
card2_titulo VARCHAR(100)
card2_descricao TEXT

-- Card 3
card3_icone VARCHAR(10)
card3_titulo VARCHAR(100)
card3_descricao TEXT

-- Card 4
card4_icone VARCHAR(10)
card4_titulo VARCHAR(100)
card4_descricao TEXT
```

## 📝 Como Usar

### Para Super Admin:

1. Acesse o painel Super Admin
2. Vá em "Barbearias"
3. Clique em "Editar" na barbearia desejada
4. Role até a seção "🎨 Personalização Visual da Home Page"
5. Modifique:
   - Título principal (use `|` para dividir cores)
   - Subtítulo
   - Slogan
   - Cores (use o seletor de cores)
6. Role até "📦 Cards de Serviços"
7. Personalize cada um dos 4 cards
8. Clique em "Salvar Alterações"

### Exemplo de Título com Divisão:
```
Barbershop|Premium
```
Resultado: "Barbershop" aparece na cor primária e "Premium" na cor do texto.

## 🔧 Arquivos Modificados

### 1. **app.py**
- **Modelo Barbearia:** Adicionados 18 novos campos de personalização
- **Rota super_admin_editar_barbearia:** Atualizada para salvar personalização
- **Rota super_admin_nova_barbearia:** Adiciona valores padrão na criação

### 2. **templates/super_admin/editar_barbearia.html**
- Formulário completo com todos os campos de personalização
- Seletores de cor interativos
- Preview dos cards
- Validação no frontend

### 3. **templates/barbearia_home.html**
- Utiliza as variáveis de personalização do banco
- Sistema de cores via CSS variables
- Cards dinâmicos

### 4. **scripts/adicionar_colunas_personalizacao.py**
- Script para adicionar colunas ao banco (já executado)

### 5. **scripts/atualizar_cores_principal.py**
- Script para atualizar cores das barbearias existentes

## 📊 Status Atual

✅ Banco de dados: Todas as 3 barbearias possuem as colunas
✅ Modelo: Campos definidos no modelo Barbearia
✅ Formulário: Completo e funcional no Super Admin
✅ Salvamento: Função de edição salva todos os campos
✅ Exibição: Home page utiliza os valores personalizados
✅ Valores padrão: Definidos para novas barbearias

## 🎯 Valores Padrão

Quando uma nova barbearia é criada, recebe automaticamente:

```python
hero_titulo = 'Seu visual|no nível máximo'
hero_subtitulo = 'Mais que um corte de cabelo, uma experiência completa...'
slogan = 'Estilo e Tradição'
cor_primaria = '#8b5cf6'  # Roxo vibrante
cor_secundaria = '#A78BFA'  # Roxo claro
cor_texto = '#1f2937'  # Texto escuro
```

## 🔍 Verificação

Para verificar se está funcionando:

1. Acesse o Super Admin
2. Edite uma barbearia
3. Modifique as cores e textos
4. Salve
5. Acesse a home page da barbearia
6. Verifique se as alterações foram aplicadas

## 💡 Dicas

- Use emojis nos ícones dos cards para melhor visual
- O título principal aceita `|` para criar contraste de cores
- Cores em hexadecimal (#RRGGBB)
- Teste diferentes combinações de cores para harmonia visual

---

**Desenvolvido por:** BarberConnect
**Data:** 04/01/2026
**Status:** ✅ Implementado e Testado
