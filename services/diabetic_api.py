from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from services.diabetic_service import DiabeticService

app = FastAPI(title="Diabetic Service", version="1.0.0")
service = DiabeticService()


class GlucoseReading(BaseModel):
    timestamp: str = Field(...)
    value_mg_dl: float = Field(...)


class DiabeticRequest(BaseModel):
    glucose_readings: Optional[List[GlucoseReading]] = Field(default_factory=list)


@app.post("/diabetic/analyze")
async def analyze(request: DiabeticRequest):
    return service.analyze([reading.dict() for reading in (request.glucose_readings or [])])


