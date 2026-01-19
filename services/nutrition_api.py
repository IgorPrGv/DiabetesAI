from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from services.nutrition_service import NutritionService

app = FastAPI(title="Nutrition Service", version="1.0.0")
service = NutritionService()


class HealthMetrics(BaseModel):
    diabetes_type: Optional[str] = None
    glucose_levels: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None


class Preferences(BaseModel):
    cuisine: Optional[str] = None
    region: Optional[str] = None
    likes: Optional[List[str]] = Field(default_factory=list)
    dislikes: Optional[List[str]] = Field(default_factory=list)
    dietary_style: Optional[str] = None


class NutritionRequest(BaseModel):
    meal_history: Optional[List[str]] = Field(default_factory=list)
    health_metrics: Optional[HealthMetrics] = None
    preferences: Optional[Preferences] = None
    goals: Optional[List[str]] = Field(default_factory=list)
    restrictions: Optional[List[str]] = Field(default_factory=list)
    region: Optional[str] = None
    inventory: Optional[List[str]] = Field(default_factory=list)


@app.post("/nutrition/analyze")
async def analyze(request: NutritionRequest):
    payload = {
        "meal_history": request.meal_history or [],
        "health_metrics": request.health_metrics.dict() if request.health_metrics else {},
        "preferences": request.preferences.dict() if request.preferences else {},
        "goals": request.goals or [],
        "restrictions": request.restrictions or [],
        "region": request.region,
        "inventory": request.inventory or [],
    }
    return service.analyze(payload)


