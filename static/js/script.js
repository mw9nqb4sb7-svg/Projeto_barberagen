// script.js - Funcionalidades JavaScript para o Sistema de Agendamentos

// ========== LOADING OVERLAY ==========
window.LoadingOverlay = {
    show: function(text = 'Por favor, aguarde...', subtext = 'Processando sua solicitação') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            const textElement = overlay.querySelector('.loading-text');
            const subtextElement = overlay.querySelector('.loading-subtext');
            if (textElement) textElement.textContent = text;
            if (subtextElement) subtextElement.textContent = subtext;
            overlay.classList.add('active');
        }
    },
    
    hide: function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // ========== MENU HAMBÚRGUER ==========
    const navToggle = document.querySelector('.nav-toggle');
    const navList = document.querySelector('.nav-list');
    
    if (navToggle && navList) {
        navToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            this.classList.toggle('active');
            navList.classList.toggle('active');
            document.body.style.overflow = navList.classList.contains('active') ? 'hidden' : '';
        });
        
        // Fechar menu ao clicar fora
        document.addEventListener('click', function(e) {
            if (navList.classList.contains('active') && 
                !navList.contains(e.target) && 
                !navToggle.contains(e.target)) {
                navToggle.classList.remove('active');
                navList.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
        
        // Fechar menu ao clicar em um link
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navToggle.classList.remove('active');
                navList.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }
    
    // ========== CONFIGURAÇÕES GERAIS ==========
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
    
    // ========== AUTO LOADING EM FORMULÁRIOS ==========
    // Adiciona loading automático em formulários com data-loading
    const loadingForms = document.querySelectorAll('form[data-loading="true"]');
    loadingForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const text = form.getAttribute('data-loading-text') || 'Processando...';
            const subtext = form.getAttribute('data-loading-subtext') || 'Por favor, aguarde';
            LoadingOverlay.show(text, subtext);
        });
    });
    
    // Adiciona loading automático em links com data-loading
    const loadingLinks = document.querySelectorAll('a[data-loading="true"]');
    loadingLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const text = link.getAttribute('data-loading-text') || 'Carregando...';
            const subtext = link.getAttribute('data-loading-subtext') || 'Por favor, aguarde';
            LoadingOverlay.show(text, subtext);
        });
    });
    
    // Auto-loading em operações específicas (agendamentos, pagamentos, relatórios)
    const autoLoadingSelectors = [
        'form[action*="agendar"]',
        'form[action*="pagamento"]',
        'form[action*="relatorio"]',
        'form[action*="processar"]',
        'a[href*="exportar"]',
        'a[href*="gerar_relatorio"]',
        'button[data-action="process"]'
    ];
    
    autoLoadingSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(element => {
            const eventType = element.tagName === 'FORM' ? 'submit' : 'click';
            element.addEventListener(eventType, function() {
                LoadingOverlay.show('Processando...', 'Esta operação pode levar alguns segundos');
            });
        });
    });
    
    // Desativa o loading se houver erros de validação
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            LoadingOverlay.hide();
        }
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