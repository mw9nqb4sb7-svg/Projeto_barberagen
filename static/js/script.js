// script.js - Funcionalidades JavaScript para o Sistema de Agendamentos

// ========== LOADING OVERLAY ==========
window.LoadingOverlay = {
    show: function(text, subtext) {
        text = text || 'Por favor, aguarde...';
        subtext = subtext || 'Processando sua solicitação';
        var overlay = document.getElementById('loading-overlay');
        if (overlay) {
            var textElement = overlay.querySelector('.loading-text');
            var subtextElement = overlay.querySelector('.loading-subtext');
            if (textElement) textElement.textContent = text;
            if (subtextElement) subtextElement.textContent = subtext;
            overlay.style.display = 'flex';
        }
    },
    
    hide: function() {
        var overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    
    // Verificar se LoadingOverlay está disponível
    if (typeof window.LoadingOverlay === 'undefined') {
        console.error('LoadingOverlay não está disponível!');
    } else {
        console.log('LoadingOverlay carregado com sucesso!');
    }
    
    // ========== MENU HAMBÚRGUER ==========
    var navToggle = document.querySelector('.nav-toggle');
    var navList = document.querySelector('.nav-list');
    
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
        var navLinks = document.querySelectorAll('.nav-link');
        for (var i = 0; i < navLinks.length; i++) {
            navLinks[i].addEventListener('click', function() {
                navToggle.classList.remove('active');
                navList.classList.remove('active');
                document.body.style.overflow = '';
            });
        }
    }
    
    // ========== CONFIGURAÇÕES GERAIS ==========
    console.log('Sistema de Agendamentos carregado');
    
    // Auto-focus no primeiro campo de formulário
    var firstInput = document.querySelector('input[type="text"], input[type="email"], input[type="password"], select');
    if (firstInput) {
        firstInput.focus();
    }
    
    // Confirmação antes de deletar
    var deleteLinks = document.querySelectorAll('a[href*="deletar"]');
    for (var i = 0; i < deleteLinks.length; i++) {
        deleteLinks[i].addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja deletar este item?')) {
                e.preventDefault();
            }
        });
    }
    
    // Auto-hide de mensagens flash após 5 segundos
    var alerts = document.querySelectorAll('.custom-alert');
    for (var i = 0; i < alerts.length; i++) {
        (function(alert) {
            setTimeout(function() {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.style.display = 'none';
                }, 300);
            }, 5000);
        })(alerts[i]);
    }
    
    // ========== AUTO LOADING EM FORMULÁRIOS ==========
    // Adiciona loading automático em formulários com data-loading
    var loadingForms = document.querySelectorAll('form[data-loading="true"]');
    console.log('Formulários com data-loading encontrados:', loadingForms.length);
    for (var i = 0; i < loadingForms.length; i++) {
        loadingForms[i].addEventListener('submit', function(e) {
            var text = this.getAttribute('data-loading-text') || 'Processando...';
            var subtext = this.getAttribute('data-loading-subtext') || 'Por favor, aguarde';
            console.log('Ativando loading para formulário:', text);
            window.LoadingOverlay.show(text, subtext);
        });
    }
    
    // Adiciona loading automático em links com data-loading
    var loadingLinks = document.querySelectorAll('a[data-loading="true"]');
    console.log('Links com data-loading encontrados:', loadingLinks.length);
    for (var i = 0; i < loadingLinks.length; i++) {
        loadingLinks[i].addEventListener('click', function(e) {
            var text = this.getAttribute('data-loading-text') || 'Carregando...';
            var subtext = this.getAttribute('data-loading-subtext') || 'Por favor, aguarde';
            console.log('Ativando loading para link:', text);
            window.LoadingOverlay.show(text, subtext);
        });
    }
    
    // Auto-loading em operações específicas (agendamentos, pagamentos, relatórios)
    var autoLoadingSelectors = [
        'form[action*="agendar"]',
        'form[action*="pagamento"]',
        'form[action*="relatorio"]',
        'form[action*="processar"]',
        'a[href*="exportar"]',
        'a[href*="gerar_relatorio"]',
        'button[data-action="process"]'
    ];
    
    for (var i = 0; i < autoLoadingSelectors.length; i++) {
        var elements = document.querySelectorAll(autoLoadingSelectors[i]);
        for (var j = 0; j < elements.length; j++) {
            var element = elements[j];
            var eventType = element.tagName === 'FORM' ? 'submit' : 'click';
            element.addEventListener(eventType, function() {
                window.LoadingOverlay.show('Processando...', 'Esta operação pode levar alguns segundos');
            });
        }
    }
    
    // Desativa o loading se houver erros de validação
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            window.LoadingOverlay.hide();
        }
    });
    
    // Validação básica de formulários
    var forms = document.querySelectorAll('form');
    for (var i = 0; i < forms.length; i++) {
        forms[i].addEventListener('submit', function(e) {
            var requiredFields = this.querySelectorAll('[required]');
            var isValid = true;
            
            for (var j = 0; j < requiredFields.length; j++) {
                var field = requiredFields[j];
                if (!field.value.trim()) {
                    field.style.borderColor = '#e74c3c';
                    isValid = false;
                } else {
                    field.style.borderColor = '#bdc3c7';
                }
            }
            
            if (!isValid) {
                e.preventDefault();
                window.LoadingOverlay.hide();
                alert('Por favor, preencha todos os campos obrigatórios.');
            }
        });
    }
});

// Função utilitária para formatar datas
function formatDate(dateString) {
    var date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Função utilitária para formatar valores monetários
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}