from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from services.judge_service import JudgeService

app = FastAPI(title="Judge Service", version="1.0.0")
service = JudgeService()


class JudgeRequest(BaseModel):
    nutrition_plan: str
    diabetic_analysis: Dict[str, Any]
    restrictions: Optional[List[str]] = Field(default_factory=list)
    goals: Optional[List[str]] = Field(default_factory=list)
    inventory: Optional[List[str]] = Field(default_factory=list)


@app.post("/judge/consolidate")
async def consolidate(request: JudgeRequest):
    return service.consolidate(request.dict())


