# Frontend - Interface DiabetesAI Care

Interface web responsiva desenvolvida em AngularJS 1.x para o sistema DiabetesAI Care.

## 🎨 Visão Geral

### Tecnologias

- **Framework**: AngularJS 1.8.2
- **Styling**: CSS3 + Bootstrap components
- **Arquitetura**: SPA (Single Page Application)
- **Responsividade**: Mobile-first design

### Páginas Principais

| Página | Descrição | Arquivo |
|--------|-----------|---------|
| **Login** | Autenticação OAuth2 | `login.html` |
| **Onboarding** | Cadastro inicial | `onboarding.html` |
| **Home/Dashboard** | Interface principal | `home.html` |
| **Register** | Registro de usuários | `register.html` |

## 🚀 Estrutura do Projeto

```
frontend/
├── home.html              # Dashboard principal
├── login.html            # Página de login
├── onboarding.html       # Onboarding usuário
├── register.html         # Registro
├── index.html           # Entry point
├── css/
│   ├── styles.css       # Estilos principais
│   └── components.css   # Componentes reutilizáveis
├── js/
│   ├── app.js          # Configuração Angular
│   ├── controllers.js  # Controllers
│   ├── services.js     # Serviços Angular
│   └── utils.js        # Utilitários
├── components/          # Componentes modulares
│   ├── modal.html      # Modal reutilizável
│   ├── chart.html      # Gráficos
│   └── form.html       # Formulários
└── src/                # TypeScript (futuro)
```

## 📱 Funcionalidades

### Dashboard Principal (`home.html`)

#### Abas Disponíveis

| Aba | Descrição | Funcionalidades |
|-----|-----------|----------------|
| **Daily Plan** | Plano diário personalizado | ✅ Timeline interativo<br>✅ Marcar/desmarcar refeições<br>✅ Alertas glicêmicos |
| **Nutrition** | Plano nutricional semanal | ✅ Lista completa 5 dias<br>✅ Detalhes por refeição<br>✅ Substituições alimentares |
| **Glucose Monitor** | Monitoramento glicêmico | ✅ Leituras em tempo real<br>✅ TIR/TAR/TBR<br>✅ Gráficos históricos |
| **Profile** | Perfil do usuário | ✅ Dados pessoais<br>✅ Preferências<br>✅ Histórico médico |

#### Recursos de Acessibilidade

- 🎤 **Voz**: Síntese de fala para chat
- 🎨 **Contraste**: Cores semânticas
- 🔍 **Fonte**: Tamanho ampliado disponível
- ⌨️ **Teclado**: Navegação completa

### Componentes Reutilizáveis

#### Modal de Detalhes da Refeição

```html
<!-- Estrutura do modal -->
<div class="meal-modal">
  <h3>{{selectedMeal.name}}</h3>
  <div class="food-items">
    <div ng-repeat="food in selectedMeal.food_items">
      <span>{{food.name}}</span>
      <span>{{food.macros.calories}} kcal</span>
    </div>
  </div>
  <div class="total-nutrition">
    <strong>Total: {{selectedMeal.total_nutrition.calories}} kcal</strong>
  </div>
</div>
```

#### Timeline Interativo

```html
<!-- Timeline do Daily Plan -->
<div class="timeline">
  <div ng-repeat="item in timeline" class="timeline-item">
    <div class="time">{{item.time_display}}</div>
    <div class="content">
      <h4>{{item.label}}</h4>
      <p>{{item.description}}</p>
      <button ng-click="vm.markMealConsumed(item)">
        {{item.consumed ? '✓ Consumido' : 'Marcar'}}
      </button>
    </div>
  </div>
</div>
```

## 🔧 Desenvolvimento

### Como Executar

```bash
# 1. Instalar dependências
npm install

# 2. Servir arquivos estáticos
python -m http.server 8080

# 3. Ou via script
./scripts/start_server.sh  # Inicia API + Frontend
```

### Arquivos de Desenvolvimento

```bash
# Estrutura recomendada
frontend/
├── dist/          # Build otimizado
├── src/          # Source TypeScript
├── test/         # Testes unitários
└── docs/         # Documentação componentes
```

## 🎨 Styling e UI/UX

### Tema e Cores

```css
/* Variáveis CSS */
:root {
  --primary-color: #4CAF50;
  --secondary-color: #FF9800;
  --danger-color: #F44336;
  --success-color: #4CAF50;
  --background: #F5F5F5;
  --text-primary: #212121;
}

/* Componentes */
.btn-primary { background: var(--primary-color); }
.btn-danger { background: var(--danger-color); }
.meal-card { border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
```

### Responsividade

```css
/* Mobile-first */
@media (max-width: 768px) {
  .timeline-item { flex-direction: column; }
  .meal-modal { width: 95%; max-width: none; }
}

@media (min-width: 769px) {
  .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; }
}
```

## 🔗 Integração com Backend

### Endpoints Utilizados

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/users/{id}/plan` | GET | Buscar plano do usuário |
| `/api/users/{id}/consumed-meals` | POST/DELETE | Marcar/desmarcar refeições |
| `/api/users/{id}/adherence` | GET | Calcular adesão |
| `/api/chat` | POST | Chat com assistente |

### Estado da Aplicação

```javascript
// Estrutura do controller principal
angular.module('diabetesApp')
.controller('MainCtrl', function($http, $scope) {
  var vm = this;

  // Estado global
  vm.user = { /* dados do usuário */ };
  vm.timeline = [ /* plano diário */ ];
  vm.meals = [ /* plano nutricional */ ];
  vm.adherence = { /* estatísticas */ };

  // Ações principais
  vm.loadPlan = function() { /* carregar plano */ };
  vm.markMealConsumed = function(meal) { /* marcar refeição */ };
  vm.sendChat = function() { /* enviar mensagem */ };
});
```

## 🧪 Testes

### Testes de Frontend

```bash
# Testes unitários
npm test

# Testes de integração
python tests/test_frontend_integration.py

# Testes visuais
python tests/test_frontend_display.py
```

### Cobertura

- ✅ **Templates**: Renderização correta
- ✅ **Controllers**: Lógica de negócio
- ✅ **Services**: Integração API
- ✅ **Acessibilidade**: Funcionalidades especiais

## 📱 Compatibilidade

### Navegadores Suportados

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

### Dispositivos

- ✅ Desktop (1920x1080+)
- ✅ Tablet (768x1024+)
- ✅ Mobile (375x667+)

## 🚀 Deploy

### Build de Produção

```bash
# Minificar e otimizar
npm run build

# Deploy para produção
scp dist/* user@server:/var/www/html/
```

### CDN e Otimizações

```html
<!-- CDN para performance -->
<script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.8.2/angular.min.js"></script>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
```

## 📝 Manutenção

### Atualizações

```bash
# Atualizar dependências
npm update

# Verificar vulnerabilidades
npm audit

# Limpar cache
npm cache clean --force
```

### Debug

```javascript
// Debug Angular
angular.element(document.body).injector().get('$rootScope').$apply();

// Verificar controllers
console.log('Controllers loaded:', angular.element(document.body).controller());
```

