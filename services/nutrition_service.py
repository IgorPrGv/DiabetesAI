import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from backend.rag_system import initialize_rag_system
from backend.llm_providers import get_llm
from services.nutrition_validation_service import NutritionValidationService
from services.food_substitution_service import FoodSubstitutionService

load_dotenv()


class NutritionService:
    def __init__(self):
        self._loader, self._rag_tool = initialize_rag_system(force_reload=False)
        self._llm = self._init_llm()
        self._validation_service = NutritionValidationService()
        self._substitution_service = FoodSubstitutionService()
        self._agent = Agent(
            role="Agente Nutricional",
            goal="Gerar recomendações alimentares personalizadas e substituições considerando DM2.",
            backstory="Você é um nutricionista especializado em diabetes tipo 2. Use o contexto e o inventário.",
            tools=[self._rag_tool.tool],
            verbose=True,
            allow_delegation=False,
            llm=self._llm,
            max_iter=3,
        )

    def _init_llm(self) -> LLM:
        return get_llm(provider=None, temperature=0.5)

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query_parts = [
            "alimentos para diabetes tipo 2",
            payload.get("preferences", {}).get("cuisine"),
            payload.get("region"),
            " ".join(payload.get("preferences", {}).get("likes", [])),
            " ".join(payload.get("restrictions", [])),
            " ".join(payload.get("inventory", [])),
        ]
        query = " | ".join([part for part in query_parts if part])
        retrieval = self._rag_tool._run(query)

        task = Task(
            description=f"""Crie um PLANO ALIMENTAR SEMANAL COMPLETO (7 dias) com VARIEDADE OBRIGATÓRIA:

**REGRAS CRÍTICAS DE VARIEDADE:**
1. Cada tipo de refeição (Café da Manhã, Almoço, Jantar) DEVE ter MÍNIMO 3 VARIAÇÕES diferentes durante a semana
2. MÁXIMO 3 repetições da mesma refeição por semana
3. Exemplo correto:
   - Segunda: Ovos com pão integral
   - Terça: Tapioca com queijo cottage
   - Quarta: Mingau de quinoa
   - Quinta: Iogurte com granola
   - Sexta: Ovos com pão integral (1ª repetição)
   - Sábado: Tapioca com queijo cottage (1ª repetição)
   - Domingo: Panqueca de banana com aveia

**ESTRUTURA OBRIGATÓRIA POR DIA:**
Para cada dia da semana (Segunda a Domingo), forneça:

1. **Café da Manhã (07:00-08:00)**
   - Nome descritivo da refeição
   - Lista de alimentos com porções EM GRAMAS (ex: "Ovos (100g)", "Pão Integral (50g)")
   - Macronutrientes DETALHADOS de cada alimento:
     * Calorias, Carboidratos (g), Proteínas (g), Gorduras (g), Fibras (g)
     * Índice Glicêmico e Carga Glicêmica
   - Total nutricional da refeição
   - 2-3 substituições possíveis para cada alimento principal

2. **Lanche da Manhã (10:00-10:30)**
   - Mesma estrutura acima

3. **Almoço (12:00-13:00)**
   - Mesma estrutura acima

4. **Lanche da Tarde (15:30-16:00)**
   - Mesma estrutura acima

5. **Jantar (19:00-20:00)**
   - Mesma estrutura acima

**DADOS DO USUÁRIO:**
- Histórico de refeições: {payload.get('meal_history', [])}
- Métricas de saúde: {payload.get('health_metrics', {})}
- Preferências alimentares: {payload.get('preferences', {})}
- Metas nutricionais: {payload.get('goals', [])}
- Restrições dietéticas: {payload.get('restrictions', [])}
- Inventário disponível: {payload.get('inventory', [])}
- Região/Culinária: {payload.get('region')}

**CONTEXTO NUTRICIONAL (RAG):**
{retrieval}

**FORMATO DE SAÍDA OBRIGATÓRIO:**
Organize por dia da semana em texto estruturado:

SEGUNDA-FEIRA:
Café da manhã (07:30): [Nome da Refeição]
- Alimento 1 (XXXg): Y kcal, Zg carbs, Wg proteína, Vg gordura, Ug fibra | IG: XX, CG: YY
- Alimento 2 (XXXg): Y kcal, Zg carbs, Wg proteína, Vg gordura, Ug fibra | IG: XX, CG: YY
Total: XXX kcal, XXg carbs, XXg proteína
Substituições: [Alimento 1] → [Alt 1, Alt 2, Alt 3]

[Repetir para Lanche Manhã, Almoço, Lanche Tarde, Jantar]

TERÇA-FEIRA:
[Mesma estrutura, mas COM REFEIÇÕES DIFERENTES]

**VALIDAÇÕES:**
- Total diário: 1400-1800 kcal
- Carboidratos: 40-50% das calorias
- Proteínas: 20-30% das calorias
- Gorduras: 25-35% das calorias
- Fibras: mínimo 25g/dia
- Priorizar alimentos com IG < 55
""",
            agent=self._agent,
            expected_output="Plano alimentar semanal completo com 7 dias, 5 refeições/dia, macronutrientes detalhados e substituições",
        )

        crew = Crew(
            agents=[self._agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        nutrition_plan = crew.kickoff()

        # Gerar substituições baseadas no inventário
        substitutions = []
        inventory = payload.get("inventory", [])
        restrictions = payload.get("restrictions", [])
        
        for food in inventory[:5]:  # Limitar a 5 para não sobrecarregar
            subs = self._substitution_service.find_substitutions(
                food,
                max_results=3,
                restrictions=restrictions
            )
            if subs:
                substitutions.append({
                    "original": food,
                    "alternatives": subs
                })

        return {
            "retrieval": retrieval,
            "nutrition_plan": str(nutrition_plan),
            "substitutions": substitutions,
        }


