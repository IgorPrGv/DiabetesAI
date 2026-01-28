# Correção: Duplicação de Refeições e Alinhamento Timeline/Meals

## Problema Identificado

1. **Duplicação de Refeições**: O sistema estava gerando 35 refeições corretas e detalhadas, mas também estava gerando refeições redundantes na timeline com formatos genéricos (breakfast, lunch, dinner, snack) e títulos com horários.

2. **Timeline Gerando Refeições**: A timeline estava criando novas refeições ao invés de apenas referenciar as refeições já geradas no array "meals".

3. **Aba Nutrition Misturando Dados**: A aba Nutrition estava mostrando tanto as refeições do array "meals" quanto as da "timeline", causando duplicação.

4. **Aba Daily Plan Não Alinhada**: A aba Daily Plan não mostrava corretamente as refeições detalhadas, apenas as referências genéricas da timeline.

5. **Idioma Misturado**: Partes do prompt e da saída estavam em inglês ao invés de português.

## Solução Implementada

### 1. Ajuste no Prompt (meal_plan_rag.py)

**Arquivo**: `/home/davi/topicos/backend/meal_plan_rag.py`

#### Mudanças na Task 8 (plan_json_task):

- **Tradução Completa**: Todo o prompt e instruções agora estão em português
- **Formato de Hora Brasileiro**: Mudado de "7:30 AM" para "07h30" (formato 24h brasileiro)
- **Timeline como Referência**: A timeline agora apenas REFERENCIA as refeições do array "meals" usando o campo `meal_ref`
- **Descrição Simplificada na Timeline**: Refeições na timeline agora têm descrição "Veja detalhes na aba Nutrição"
- **Novo Campo meal_ref**: Adicionado campo `meal_ref: "DIA-TIPO"` (ex: "SEGUNDA-FEIRA-Café da manhã") para vincular timeline às meals

#### Estrutura da Timeline (novo formato):

```json
{
  "time": "07:30",
  "time_display": "07h30",
  "event_type": "Meal",
  "event_category": "Café da manhã",
  "label": "07h30 • Café da manhã",
  "description": "Veja detalhes na aba Nutrição",
  "color": "red",
  "level": "meal",
  "meal_type": "Café da manhã",
  "day": "SEGUNDA-FEIRA",
  "meal_ref": "SEGUNDA-FEIRA-Café da manhã"
}
```

#### Categorias em Português:

- **Checks de Glicemia**:
  - event_category: "Glicemia" (antes: "Glucose Check")
  - Descrições: "Glicemia em Jejum", "Glicemia Pré-Prandial"

- **Atividades**:
  - event_category: "Exercício" ou "Alongamento" (antes: "Exercise")
  - Descrições: "Caminhada Leve", "Caminhada Moderada", "Alongamento Leve"

### 2. Ajuste no Frontend (home.html)

**Arquivo**: `/home/davi/topicos/frontend/home.html`

#### a) Função `loadNutritionPlan` (Aba Nutrition):

**Antes**: Misturava refeições do array "meals" com refeições da "timeline"

**Depois**: Usa APENAS o array "meals" do plan_json

```javascript
vm.loadNutritionPlan = function() {
  // ...
  if (res.data && res.data.plan_json && res.data.plan_json.meals) {
    const plan = res.data.plan_json;
    
    // APENAS usar o array "meals" do plan_json - NÃO usar timeline
    vm.meals = plan.meals.map(meal => ({
      day: meal.day || 'N/A',
      meal_type: meal.meal_type || 'Refeição',
      name: meal.name || 'Refeição',
      // ... outros campos
      is_detailed: true
    }));
    // ...
  }
}
```

**Benefícios**:
- Elimina duplicação
- Mostra apenas refeições completas e detalhadas
- ~35 refeições (7 dias × 5 refeições por dia)

#### b) Funções `loadExistingPlan` e `loadPlan` (Aba Daily Plan):

**Antes**: Pegava apenas dados da timeline sem enriquecer com detalhes das meals

**Depois**: Cria mapa de refeições e enriquece timeline com detalhes usando meal_ref

```javascript
// Create a map of meals for quick lookup
const mealsMap = {};
if (plan.meals) {
  plan.meals.forEach(meal => {
    const key = `${meal.day}-${meal.meal_type}`;
    mealsMap[key] = meal;
  });
}

// Enrich timeline items with meal details
vm.timeline = plan.timeline.map(item => {
  const baseItem = { /* ... */ };
  
  // Se for uma refeição e tiver meal_ref, buscar detalhes do array meals
  if (item.event_type === 'Meal' && item.meal_ref && mealsMap[item.meal_ref]) {
    const mealDetails = mealsMap[item.meal_ref];
    baseItem.description = mealDetails.description || item.description || '';
    baseItem.text = mealDetails.description || item.description || item.label;
    baseItem.meal_details = mealDetails; // Guardar referência completa
  }
  
  return baseItem;
});
```

**Benefícios**:
- Timeline mostra detalhes completos das refeições
- Não duplica informação
- Mantém sincronização entre Daily Plan e Nutrition

## Fluxo de Dados (Novo)

```
1. Geração do Plano (Backend)
   ├─ Array "meals" (35 refeições detalhadas)
   │  ├─ SEGUNDA-FEIRA - Café da manhã
   │  ├─ SEGUNDA-FEIRA - Almoço
   │  ├─ SEGUNDA-FEIRA - Jantar
   │  └─ ... (7 dias × 5 refeições)
   │
   └─ Array "timeline" (63 eventos = 7 dias × 9 eventos/dia)
      ├─ Checks de Glicemia (21 eventos: 3 por dia × 7 dias)
      ├─ Referências a Refeições (21 eventos: 3 por dia × 7 dias)
      │  └─ Cada uma com meal_ref apontando para "meals"
      └─ Atividades (21 eventos: 3 por dia × 7 dias)

2. Frontend - Aba Nutrition
   └─ Usa APENAS array "meals" → 35 refeições detalhadas

3. Frontend - Aba Daily Plan
   ├─ Usa array "timeline" filtrado por dia
   ├─ Enriquece eventos de refeição com dados de "meals" via meal_ref
   └─ Mostra: glicemia + refeições (detalhadas) + atividades
```

## Exemplo de Dados

### Array "meals" (detalhado):
```json
{
  "day": "SEGUNDA-FEIRA",
  "meal_type": "Café da manhã",
  "name": "Pão Integral com Queijo e Mamão",
  "description": "Pão integral (60g = 2 fatias), queijo branco (30g), mamão (100g = 1 fatia média)",
  "items": ["Pão integral (60g)", "Queijo branco (30g)", "Mamão (100g)"],
  "food_items": [
    {
      "name": "Pão integral",
      "portion": "60g",
      "macros": { "calories": 150, "carbs_g": 28, "protein_g": 6, "fat_g": 2, "fiber_g": 4 }
    }
  ],
  "total_nutrition": { "calories": 250, "carbs_g": 35, "protein_g": 12, "fat_g": 5, "fiber_g": 6 },
  "nutrition": "250 kcal, 35g carbs, 12g proteína",
  "time": "07:30",
  "time_interval": "07:00-08:00"
}
```

### Array "timeline" (referência):
```json
{
  "time": "07:30",
  "time_display": "07h30",
  "event_type": "Meal",
  "event_category": "Café da manhã",
  "label": "07h30 • Café da manhã",
  "description": "Veja detalhes na aba Nutrição",
  "color": "red",
  "level": "meal",
  "meal_type": "Café da manhã",
  "day": "SEGUNDA-FEIRA",
  "meal_ref": "SEGUNDA-FEIRA-Café da manhã"
}
```

## Arquivos Modificados

1. **`/home/davi/topicos/backend/meal_plan_rag.py`**
   - Linha ~437-570: Task 8 (plan_json_task) completamente reescrita
   - Tradução completa para português
   - Formato de hora brasileiro (24h)
   - Timeline como referência (meal_ref)

2. **`/home/davi/topicos/frontend/home.html`**
   - Linha ~2198: Função `loadNutritionPlan` simplificada
   - Linha ~1657: Função `loadExistingPlan` com enriquecimento
   - Linha ~1744: Função `loadPlan` com enriquecimento

## Como Testar

1. **Gerar Novo Plano**:
   ```bash
   # Certifique-se de que o servidor está rodando
   cd /home/davi/topicos
   source venv/bin/activate
   # Se não estiver rodando:
   ./scripts/start_server.sh
   ```

2. **Acessar Frontend**:
   - Abra http://localhost:8000/home.html
   - Faça login
   - Vá para Profile e preencha os dados
   - Clique em "Gerar novo plano"

3. **Verificar Aba Daily Plan**:
   - Deve mostrar timeline com:
     - ✅ Checks de glicemia em português
     - ✅ Refeições com descrições detalhadas
     - ✅ Atividades em português
     - ✅ Horários em formato brasileiro (07h30, 12h00, etc.)

4. **Verificar Aba Nutrition**:
   - Deve mostrar ~35 refeições detalhadas
   - ❌ NÃO deve mostrar duplicatas
   - ✅ Cada refeição tem food_items, macros, etc.

5. **Verificar Console**:
   ```javascript
   // Deve aparecer:
   "📊 Carregadas 35 refeições detalhadas do array meals"
   ```

6. **Verificar JSON Gerado**:
   - Inspecionar response da API `/api/users/{user_id}/plan`
   - Verificar que timeline tem `meal_ref`
   - Verificar que meals tem todas as 35 refeições

## Benefícios da Solução

✅ **Elimina Duplicação**: Não há mais refeições redundantes
✅ **Clareza de Dados**: Timeline = referências, Meals = detalhes
✅ **Português Completo**: Todo o sistema em PT-BR
✅ **Formato Brasileiro**: Horários em 24h (07h30, 12h00, 19h00)
✅ **Performance**: Frontend não precisa deduplicate ou filtrar
✅ **Manutenibilidade**: Separação clara de responsabilidades
✅ **UX Melhorada**: Usuário vê informações corretas em cada aba

## Próximos Passos (Opcional)

- [ ] Adicionar botão para ver detalhes da refeição na timeline
- [ ] Implementar modal com informações nutricionais ao clicar na refeição
- [ ] Adicionar gráfico de macros por dia
- [ ] Implementar filtro de refeições por tipo na aba Nutrition
