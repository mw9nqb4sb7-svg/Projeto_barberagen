// script.js - Funcionalidades JavaScript para o Sistema de Agendamentos

document.addEventListener('DOMContentLoaded', function() {
    // Configurações gerais
    console.log('Sistema de Agendamentos carregado');
    
    // Funcionalidade para melhorar a experiência do usuário
    
    // Auto-focus no primeiro campo de formulário
    const firstInput = document.querySelector('input[type="text"], input[type="email"], input[type="password"], select');
    if (firstInput) {
        firstInput.focus();
    }
    
    // Confirmação antes de deletar
    const deleteLinks = document.querySelectorAll('a[href*="deletar"]');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja deletar este item?')) {
                e.preventDefault();
            }
        });
    });
    
    // Auto-hide de mensagens flash após 5 segundos
    const alerts = document.querySelectorAll('.custom-alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });
    
    // Validação básica de formulários
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = '#e74c3c';
                    isValid = false;
                } else {
                    field.style.borderColor = '#bdc3c7';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Por favor, preencha todos os campos obrigatórios.');
            }
        });
    });
});

// Função utilitária para formatar datas
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Função utilitária para formatar valores monetários
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}