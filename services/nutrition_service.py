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
            description=f"""Crie recomendações alimentares e substituições:

            Dados do usuário:
            - Histórico: {payload.get('meal_history', [])}
            - Métricas: {payload.get('health_metrics', {})}
            - Preferências: {payload.get('preferences', {})}
            - Metas: {payload.get('goals', [])}
            - Restrições: {payload.get('restrictions', [])}
            - Inventário: {payload.get('inventory', [])}
            - Região: {payload.get('region')}

            Contexto recuperado:
            {retrieval}

            Gere:
            1) Recomendações alimentares diárias
            2) Substituições com base no inventário
            3) Observações sobre macro/micro (fibras, carboidratos, sódio)
            """,
            agent=self._agent,
            expected_output="Recomendações nutricionais e substituições",
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


