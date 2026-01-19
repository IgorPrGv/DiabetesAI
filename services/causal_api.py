from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from services.causal_service import CausalService

app = FastAPI(title="Causal Service", version="1.0.0")
service = CausalService()


class GlucoseReading(BaseModel):
    timestamp: str = Field(...)
    value_mg_dl: float = Field(...)


class CausalRequest(BaseModel):
    meal_history: Optional[List[str]] = Field(default_factory=list)
    glucose_readings: Optional[List[GlucoseReading]] = Field(default_factory=list)


@app.post("/causal/analyze")
async def analyze(request: CausalRequest):
    payload = {
        "meal_history": request.meal_history or [],
        "glucose_readings": [reading.dict() for reading in (request.glucose_readings or [])],
    }
    return service.analyze(payload)

