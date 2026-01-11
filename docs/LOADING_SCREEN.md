# Sistema de Loading Screen

## 📋 Visão Geral

O sistema de loading foi implementado para melhorar a experiência do usuário durante operações que demandam mais tempo de processamento.

## 🎯 Funcionalidades

- Overlay com spinner animado
- Mensagens customizáveis
- Ativação automática em operações específicas
- Ativação manual via JavaScript
- Ativação via atributos HTML

## 🚀 Como Usar

### 1. Ativação Automática

O loading é ativado automaticamente em:
- Formulários com ações de agendamento
- Formulários de pagamento
- Geração de relatórios
- Links de exportação

```html
<!-- Ativação automática - apenas inclua a rota -->
<form action="{{ url_for('agendar_horario') }}" method="POST">
    <!-- campos do formulário -->
</form>
```

### 2. Ativação Manual via HTML

Use os atributos `data-loading` para controlar o loading:

```html
<!-- Formulário com loading customizado -->
<form method="POST" 
      data-loading="true"
      data-loading-text="Salvando dados..."
      data-loading-subtext="Aguarde alguns instantes">
    <button type="submit">Salvar</button>
</form>

<!-- Link com loading -->
<a href="{{ url_for('gerar_relatorio') }}" 
   data-loading="true"
   data-loading-text="Gerando relatório..."
   data-loading-subtext="Isso pode levar até 30 segundos">
    Gerar Relatório Mensal
</a>

<!-- Botão com loading -->
<button onclick="processarPagamento()" 
        data-loading="true"
        data-loading-text="Processando pagamento..."
        data-loading-subtext="Aguardando confirmação">
    Confirmar Pagamento
</button>
```

### 3. Ativação Manual via JavaScript

```javascript
// Mostrar loading
LoadingOverlay.show('Processando...', 'Por favor, aguarde');

// Mostrar loading com mensagem customizada
LoadingOverlay.show('Enviando e-mails...', 'Isso pode levar alguns minutos');

// Ocultar loading
LoadingOverlay.hide();

// Exemplo completo em uma função
async function enviarDados() {
    LoadingOverlay.show('Enviando dados...', 'Aguarde a confirmação');
    
    try {
        const response = await fetch('/api/enviar', {
            method: 'POST',
            body: JSON.stringify(dados)
        });
        
        if (response.ok) {
            alert('Dados enviados com sucesso!');
        }
    } catch (error) {
        console.error(error);
        alert('Erro ao enviar dados');
    } finally {
        LoadingOverlay.hide();
    }
}
```

## 📝 Exemplos Práticos

### Formulário de Agendamento

```html
<form action="{{ url_for('nova_reserva') }}" 
      method="POST"
      data-loading="true"
      data-loading-text="Confirmando agendamento..."
      data-loading-subtext="Verificando disponibilidade">
    
    <input type="date" name="data" required>
    <input type="time" name="hora" required>
    <button type="submit">Agendar</button>
</form>
```

### Exportação de Relatório

```html
<a href="{{ url_for('exportar_clientes_csv') }}"
   class="btn-primary"
   data-loading="true"
   data-loading-text="Exportando dados..."
   data-loading-subtext="Preparando arquivo CSV">
    📊 Exportar Clientes
</a>
```

### Processamento Complexo

```html
<button onclick="processarLote()" 
        class="btn-primary"
        data-loading="true"
        data-loading-text="Processando lote..."
        data-loading-subtext="Isso pode levar alguns minutos">
    Processar 1000+ registros
</button>

<script>
function processarLote() {
    // O loading já foi ativado pelo data-loading="true"
    fetch('/api/processar-lote', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            LoadingOverlay.hide();
            alert('Processamento concluído!');
        })
        .catch(error => {
            LoadingOverlay.hide();
            alert('Erro no processamento');
        });
}
</script>
```

## 🎨 Personalização

### CSS do Loading

O loading está no arquivo `templates/base.html` e pode ser customizado:

```css
#loading-overlay {
    background: rgba(0, 0, 0, 0.7); /* Cor de fundo */
    backdrop-filter: blur(5px);      /* Efeito de desfoque */
}

.loading-spinner {
    border-top: 5px solid #8B5CF6;  /* Cor do spinner */
}
```

### Alterar Cores por Barbearia

```html
<style>
    .loading-spinner {
        border-top: 5px solid {{ barbearia.cor_primaria or '#8B5CF6' }};
    }
</style>
```

## ⚠️ Boas Práticas

### ✅ Use loading em:
- Operações que levam mais de 1 segundo
- Envio de formulários complexos
- Processamento de pagamentos
- Geração de relatórios
- Upload de arquivos
- Exportação de dados
- Operações em lote

### ❌ Evite loading em:
- Navegação simples entre páginas
- Operações instantâneas
- Validações de formulário
- Busca rápida

### 🔧 Desativar loading em caso de erro de validação

```javascript
form.addEventListener('submit', function(e) {
    // Validação
    if (!campoValido) {
        e.preventDefault();
        LoadingOverlay.hide(); // Remove o loading
        alert('Preencha todos os campos');
        return false;
    }
    // Loading continua para envio
});
```

## 🐛 Troubleshooting

### Loading não desaparece
```javascript
// Force ocultar em caso de erro
window.addEventListener('error', function() {
    LoadingOverlay.hide();
});
```

### Loading aparece mas página não carrega
```javascript
// Timeout de segurança
setTimeout(() => {
    LoadingOverlay.hide();
}, 30000); // 30 segundos
```

## 📱 Compatibilidade

- ✅ Chrome, Firefox, Safari, Edge (versões recentes)
- ✅ Dispositivos móveis (iOS e Android)
- ✅ Tablets
- ✅ Navegação com cache (pageshow event)

## 🔄 Atualizações

- **v1.0** (11/01/2026): Implementação inicial
  - Loading overlay global
  - Ativação automática
  - Ativação manual via HTML e JavaScript
  - Suporte a mensagens customizadas
