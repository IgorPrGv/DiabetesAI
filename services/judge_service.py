import os
from typing import Any, Dict
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from backend.llm_providers import get_llm

load_dotenv()


class JudgeService:
    def __init__(self):
        self._llm = self._init_llm()
        self._agent = Agent(
            role="Agente Julgador",
            goal="Consolidar recomendações e resolver conflitos clínicos/nutricionais.",
            backstory="Você valida segurança e clareza do plano para DM2.",
            tools=[],
            verbose=True,
            allow_delegation=False,
            llm=self._llm,
            max_iter=2,
        )

    def _init_llm(self) -> LLM:
        return get_llm(provider=None, temperature=0.4)

    def consolidate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        task = Task(
            description=f"""Consolide o plano final:

            Recomendações nutricionais:
            {payload.get('nutrition_plan', '')}

            Métricas glicêmicas:
            {payload.get('diabetic_analysis', {})}

            Restrições: {payload.get('restrictions', [])}
            Metas: {payload.get('goals', [])}
            Inventário: {payload.get('inventory', [])}

            Retorne um plano diário claro e acionável com notas de segurança.
            """,
            agent=self._agent,
            expected_output="Plano final consolidado com notas de segurança",
        )

        crew = Crew(
            agents=[self._agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()
        return {"final_plan": str(result)}


