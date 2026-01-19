import os
from typing import List, Dict
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from backend.llm_providers import get_llm

load_dotenv()


class ChatService:
    def __init__(self):
        self._llm = self._init_llm()
        self._agent = Agent(
            role="Chat Assistant",
            goal="Answer user questions clearly and concisely about diabetes and meal planning.",
            backstory="You are a helpful assistant focused on diabetes type 2 support.",
            tools=[],
            verbose=False,
            allow_delegation=False,
            llm=self._llm,
            max_iter=1,
        )

    def _init_llm(self) -> LLM:
        return get_llm(provider=None, temperature=0.4)

    def respond(self, message: str, history: List[Dict[str, str]]) -> str:
        history_text = ""
        for item in history[-6:]:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
            else:
                role = getattr(item, "role", "user")
                content = getattr(item, "content", "")
            history_text += f"{role}: {content}\n"

        task = Task(
            description=f"""Conversation history:
{history_text}

User: {message}

Reply in Portuguese, short and direct. If you provide advice, add a short safety note.""",
            agent=self._agent,
            expected_output="A concise assistant reply.",
        )

        crew = Crew(agents=[self._agent], tasks=[task], process=Process.sequential, verbose=False)
        result = crew.kickoff()
        return str(result).strip()

