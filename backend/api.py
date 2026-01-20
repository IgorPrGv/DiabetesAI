"""
REST API for Meal Planning RAG System
FastAPI-based API to generate personalized meal plans
"""

from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from .storage import init_db, save_plan, list_plans, get_plan, create_user, list_users, get_user, update_user, delete_user, create_auth_user, get_auth_user_by_email, create_user_with_empty_profile, get_user_by_auth_id, save_consumed_meal, get_consumed_meals, calculate_adherence, check_database_health, delete_consumed_meal
import bcrypt
import uvicorn
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from .meal_plan_rag import generate_meal_plan
from services.gateway_service import GatewayService
from services.chat_service import ChatService

# Create FastAPI app
app = FastAPI(
    title="Meal Planning RAG API",
    description="REST API for generating personalized meal plans using RAG and CrewAI",
    version="1.0.0"
)

gateway_service = GatewayService()
chat_service = ChatService()

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Serve minimal frontend scaffold
# app.mount("/static", StaticFiles(directory="/home/davi/topicos/frontend"), name="static")

# Enable CORS (allows frontend to call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models (Pydantic schemas)
# ============================================================================

class HealthMetrics(BaseModel):
    """Health metrics model"""
    diabetes_type: Optional[str] = Field(default=None, description="Type of diabetes (e.g., 'Type 2')")
    glucose_levels: Optional[str] = Field(default=None, description="Glucose levels (e.g., 'Elevated (140-180 mg/dL)')")
    weight: Optional[Any] = Field(default=None, description="Weight (can be string like '85 kg' or number)")
    height: Optional[Any] = Field(default=None, description="Height (can be string like '1.75 m' or number in cm)")
    bmi: Optional[float] = Field(default=None, description="Body Mass Index")
    blood_pressure: Optional[str] = Field(default=None, description="Blood pressure")
    other_conditions: Optional[List[str]] = Field(default_factory=list, description="Other health conditions")
    
    class Config:
        # Allow both string and number for weight/height
        json_encoders = {
            str: str,
            int: int,
            float: float
        }
        # Allow extra fields and None values
        extra = "allow"


class Preferences(BaseModel):
    """Food preferences model"""
    cuisine: Optional[str] = Field(None, description="Preferred cuisine (e.g., 'Brasileira')")
    region: Optional[str] = Field(None, description="Regional preference (e.g., 'Sudeste')")
    likes: Optional[List[str]] = Field(default_factory=list, description="Foods the user likes")
    dislikes: Optional[List[str]] = Field(default_factory=list, description="Foods the user dislikes")
    dietary_style: Optional[str] = Field(None, description="Dietary style (e.g., 'vegetarian', 'vegan')")


class GlucoseReading(BaseModel):
    """Glucose reading model"""
    timestamp: str = Field(..., description="ISO timestamp of the reading")
    value_mg_dl: float = Field(..., description="Glucose value in mg/dL")


class MealPlanRequest(BaseModel):
    """Request model for meal plan generation"""
    meal_history: Optional[List[str]] = Field(
        default_factory=list,
        description="List of previous meals (e.g., ['Café da manhã: Pão integral...'])"
    )
    health_metrics: Optional[HealthMetrics] = Field(
        None,
        description="User's health metrics"
    )
    preferences: Optional[Preferences] = Field(
        None,
        description="Food preferences"
    )
    goals: Optional[List[str]] = Field(
        default_factory=list,
        description="User goals (e.g., ['Controlar glicemia', 'Perder peso'])"
    )
    restrictions: Optional[List[str]] = Field(
        default_factory=list,
        description="Dietary restrictions (e.g., ['Diabetes tipo 2', 'Limitar carboidratos'])"
    )
    region: Optional[str] = Field(None, description="Regional preference for meal planning")
    inventory: Optional[List[str]] = Field(
        default_factory=list,
        description="Available foods in the user's inventory"
    )
    glucose_readings: Optional[List[GlucoseReading]] = Field(
        default_factory=list,
        description="Time-series glucose readings for TIR/TAR/TBR analysis"
    )
    user_id: Optional[int] = Field(None, description="Optional user id to load profile data")


class DiabeticRequest(BaseModel):
    glucose_readings: Optional[List[GlucoseReading]] = Field(default_factory=list)


class JudgeRequest(BaseModel):
    nutrition_plan: str
    diabetic_analysis: Dict[str, Any]
    restrictions: Optional[List[str]] = Field(default_factory=list)
    goals: Optional[List[str]] = Field(default_factory=list)
    inventory: Optional[List[str]] = Field(default_factory=list)


class CausalRequest(BaseModel):
    meal_history: Optional[List[str]] = Field(default_factory=list)
    glucose_readings: Optional[List[GlucoseReading]] = Field(default_factory=list)


class MealPlanArtifacts(BaseModel):
    """Structured artifacts for front-end rendering"""
    personal_model: Optional[str] = Field(None, description="Personal model analysis")
    diabetic_analysis: Optional[str] = Field(None, description="Glycemic analysis and alerts")
    causal_inference: Optional[str] = Field(None, description="Causal inference insights")
    retrieval: Optional[str] = Field(None, description="Retrieved nutritional info")
    structured_prompt: Optional[str] = Field(None, description="Structured prompt used")
    meal_plan: Optional[str] = Field(None, description="Meal plan before judge validation")
    judge_output: Optional[str] = Field(None, description="Judge validation output")
    final_plan: Optional[str] = Field(None, description="Final meal plan output")


class MealPlanResponse(BaseModel):
    """Response model for meal plan"""
    success: bool = Field(..., description="Whether the request was successful")
    meal_plan: Optional[str] = Field(None, description="Generated meal plan")
    artifacts: Optional[MealPlanArtifacts] = Field(None, description="Structured artifacts")
    plan_json: Optional[Dict[str, Any]] = Field(None, description="Structured daily plan JSON")
    message: Optional[str] = Field(None, description="Additional message or error description")
    plan_id: Optional[int] = Field(None, description="ID of the saved plan")


class PlanHistoryItem(BaseModel):
    id: int
    created_at: str
    plan_json: Optional[Dict[str, Any]] = None


class PlanHistoryResponse(BaseModel):
    success: bool
    items: List[PlanHistoryItem]


class UserProfile(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    health_metrics: Optional[HealthMetrics] = None
    preferences: Optional[Preferences] = None
    goals: Optional[List[str]] = Field(default_factory=list)
    restrictions: Optional[List[str]] = Field(default_factory=list)
    region: Optional[str] = None
    inventory: Optional[List[str]] = Field(default_factory=list)
    glucose_readings: Optional[List[GlucoseReading]] = Field(default_factory=list)
    meal_history: Optional[List[str]] = Field(default_factory=list)
    auth_user_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    created_at: str
    auth_user_id: Optional[int] = None
    profile: UserProfile


class AuthRegisterRequest(BaseModel):
    email: str
    password: str


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    user_id: int


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    success: bool
    reply: str


# ============================================================================
# API Endpoints
# ============================================================================
# 
# @app.get("/")
# @app.get("/ui")
# async def serve_ui():
#     """Serve the frontend index page which redirects based on auth status"""
#     return FileResponse("/home/davi/topicos/frontend/index.html")
# 
# 
# @app.get("/login")
# @app.get("/login.html")
# async def serve_login():
#     return FileResponse("/home/davi/topicos/frontend/login.html")
# 
# 
# @app.get("/register")
# @app.get("/register.html")
# async def serve_register():
#     return FileResponse("/home/davi/topicos/frontend/register.html")
# 
# 
# @app.get("/home")
# @app.get("/home.html")
# async def serve_home():
#     return FileResponse("/home/davi/topicos/frontend/home.html")
# 
# 
# @app.get("/onboarding")
# @app.get("/onboarding.html")
# async def serve_onboarding():
#     """Serve onboarding page for first-time users"""
#     return FileResponse("/home/davi/topicos/frontend/onboarding.html")


@app.on_event("startup")
async def startup_event():
    """Initialize database and perform health check on startup."""
    try:
        logger.info("🚀 Starting DiabetesAI API server...")

        # Initialize database
        logger.info("📊 Initializing database...")
        init_db()

        # Perform database health check
        logger.info("🔍 Performing database health check...")
        health = check_database_health()

        if health["status"] == "healthy":
            logger.info("✅ Database health check passed!")
            logger.info(f"   📁 Database: {health['database_path']}")
            logger.info(f"   📏 Size: {health['database_size_mb']} MB")
            logger.info(f"   📊 Tables: {health['tables']}")
        else:
            logger.error("❌ Database health check failed!")
            logger.error(f"   Error: {health.get('error', 'Unknown error')}")
            # Don't raise exception here to allow server to start, but log the issue

        logger.info("🎉 API server startup complete!")

    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise


@api_router.get("/health")
async def health_check():
    """Health check endpoint with database status."""
    try:
        # Check database health
        db_health = check_database_health()

        response = {
            "status": "healthy" if db_health["status"] == "healthy" else "degraded",
            "service": "diabetesai-api",
            "database": db_health,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # If database is unhealthy, return degraded status
        if db_health["status"] != "healthy":
            response["status"] = "unhealthy"

        return response

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "diabetesai-api",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@api_router.post("/meal-plan/generate", response_model=MealPlanResponse)
async def generate_meal_plan_endpoint(request: MealPlanRequest):
    """
    Generate a personalized meal plan based on user information.
    If user_id is provided, loads user profile data and merges with request.
    """
    """
    Generate a personalized meal plan based on user information
    
    This endpoint uses the RAG system with collaborative agents to generate
    a comprehensive meal plan considering:
    - User's meal history
    - Health metrics (especially type 2 diabetes)
    - Food preferences and regional preferences
    - Goals and restrictions
    
    Returns a meal plan with breakfast, lunch, and dinner options.
    
    Note: This operation can take 5-15 minutes due to the collaborative agent workflow.
    """
    try:
        # Convert Pydantic models to dict format expected by generate_meal_plan
        user_query = {
            "meal_history": request.meal_history or [],
            "health_metrics": request.health_metrics.dict() if request.health_metrics else {},
            "preferences": request.preferences.dict() if request.preferences else {},
            "goals": request.goals or [],
            "restrictions": request.restrictions or [],
            "region": request.region,
            "inventory": request.inventory or [],
            "glucose_readings": [reading.dict() for reading in (request.glucose_readings or [])],
        }
        if request.user_id:
            stored_user = get_user(request.user_id)
            if stored_user:
                profile = stored_user.get("profile", {})
                # Merge: use request data if provided, otherwise use profile data
                user_query = {
                    "meal_history": request.meal_history if request.meal_history else (profile.get("meal_history", []) or []),
                    "health_metrics": request.health_metrics.dict() if request.health_metrics else (profile.get("health_metrics", {}) or {}),
                    "preferences": request.preferences.dict() if request.preferences else (profile.get("preferences", {}) or {}),
                    "goals": request.goals if request.goals else (profile.get("goals", []) or []),
                    "restrictions": request.restrictions if request.restrictions else (profile.get("restrictions", []) or []),
                    "region": request.region or profile.get("region"),
                    "inventory": request.inventory if request.inventory else (profile.get("inventory", []) or []),
                    "glucose_readings": [r.dict() for r in request.glucose_readings] if request.glucose_readings else ([r if isinstance(r, dict) else r.dict() for r in profile.get("glucose_readings", [])] if profile.get("glucose_readings") else []),
                }
        
        # Execute in thread pool with timeout (15 minutes max)
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        try:
            # Use the full CrewAI workflow from meal_plan_rag.py (8 collaborative agents)
            # This provides better collaboration and context sharing between agents
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, generate_meal_plan, user_query),
                timeout=1500.0  # 25 minutes timeout
            )
            
            if isinstance(result, dict):
                # meal_plan_rag.py returns different structure
                meal_plan_text = result.get("final_plan", "")
                steps = result.get("steps", {})
                
                artifacts = {
                    "personal_model": steps.get("personal_model", ""),
                    "diabetic_analysis": steps.get("diabetic_analysis", ""),
                    "causal_inference": steps.get("causal_inference", ""),
                    "retrieval": steps.get("retrieval", ""),
                    "structured_prompt": steps.get("structured_prompt", ""),
                    "meal_plan": steps.get("meal_plan", ""),
                    "judge_output": steps.get("judge_output", ""),
                    "final_plan": meal_plan_text,
                }
                plan_json = result.get("plan_json", {})
                
                # Adicionar validação nutricional se plan_json tem meals
                if plan_json and plan_json.get("meals"):
                    try:
                        from services.nutrition_validation_service import NutritionValidationService
                        validation_service = NutritionValidationService()
                        
                        # Calcular calorias alvo
                        target_calories = 2000
                        if request.health_metrics and request.health_metrics.weight:
                            try:
                                weight_str = str(request.health_metrics.weight).replace('kg', '').strip()
                                weight_kg = float(weight_str)
                                target_calories = weight_kg * 25  # 25 kcal/kg para DM2
                            except:
                                pass
                        
                        validation = validation_service.validate_meal_plan(
                            plan_json.get("meals", []),
                            target_calories
                        )
                        
                        # Adicionar validação ao plan_json
                        if "validation" not in plan_json:
                            plan_json["validation"] = {}
                        plan_json["validation"] = {
                            "daily_validation": validation.get("daily_validation", {}),
                            "totals": validation.get("totals", {}),
                            "meal_validations": validation.get("meal_validations", [])
                        }
                    except Exception as e:
                        print(f"Erro ao validar plano nutricional: {e}")
                
                # Ensure plan_json is never None or empty
                if not plan_json or (isinstance(plan_json, dict) and len(plan_json) == 0):
                    # Create minimal fallback
                    from services.plan_json_service import PlanJsonService
                    fallback_service = PlanJsonService()
                    diabetic_for_fallback = result.get("diabetic_analysis", {})
                    if isinstance(diabetic_for_fallback, dict):
                        plan_json = fallback_service._create_fallback_structure(
                            result.get("final_plan", ""), 
                            diabetic_for_fallback
                        )
            else:
                meal_plan_text = str(result) if result else None
                artifacts = None
                plan_json = None
                
                # If result is None or empty, create fallback
                if not plan_json:
                    from services.plan_json_service import PlanJsonService
                    from services.diabetic_service import DiabeticService
                    glucose_readings = user_query.get("glucose_readings", [])
                    diabetic_service = DiabeticService()
                    diabetic_analysis = diabetic_service.analyze(glucose_readings)
                    fallback_service = PlanJsonService()
                    diabetes_type = user_query.get("health_metrics", {}).get("diabetes_type", "Diabetes Tipo 2")
                    fallback_plan = f"Plano nutricional para {diabetes_type}"
                    plan_json = fallback_service._create_fallback_structure(fallback_plan, diabetic_analysis)

            plan_id = save_plan(
                request_payload={**user_query, "user_id": request.user_id} if request.user_id else user_query,
                response_payload={"plan_json": plan_json, "meal_plan": meal_plan_text, "artifacts": artifacts},
            )
            
            response_data = {
                "success": True,
                "meal_plan": meal_plan_text,
                "artifacts": MealPlanArtifacts(**artifacts) if artifacts else None,
                "plan_json": plan_json,
                "message": "Meal plan generated successfully",
                "plan_id": plan_id  # Include plan_id in response
            }
            
            return MealPlanResponse(**response_data)
            
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Meal plan generation timed out after 25 minutes. The process involves 5 collaborative agents and may need optimization."
            )
        except FutureTimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Meal plan generation timed out. Please try again or use a simpler request."
            )
        except Exception as e:
            error_msg = str(e)
            error_str_lower = error_msg.lower()
            # Check if it's a quota error (check in multiple ways)
            is_quota_error = (
                "429" in error_msg or 
                "quota" in error_str_lower or 
                "resource_exhausted" in error_str_lower or
                "exceeded" in error_str_lower
            )
            
            if is_quota_error:
                print("⚠️  Gemini quota exceeded in executor, returning fallback structure")
                from services.plan_json_service import PlanJsonService
                from services.diabetic_service import DiabeticService
                
                # Get user's glucose readings for metrics
                glucose_readings = user_query.get("glucose_readings", [])
                diabetic_service = DiabeticService()
                diabetic_analysis = diabetic_service.analyze(glucose_readings)
                
                # Create fallback plan
                fallback_service = PlanJsonService()
                diabetes_type = user_query.get("health_metrics", {}).get("diabetes_type", "Diabetes Tipo 2")
                fallback_plan = f"Plano nutricional para {diabetes_type}"
                plan_json = fallback_service._create_fallback_structure(fallback_plan, diabetic_analysis)
                
                return MealPlanResponse(
                    success=True,
                    meal_plan="Plano gerado usando estrutura padrão (quota do Gemini excedida)",
                    artifacts=None,
                    plan_json=plan_json,
                    message="Plano gerado com estrutura padrão. A quota do Gemini foi excedida - tente novamente mais tarde."
                )
            # Re-raise if not quota error
            raise
        finally:
            executor.shutdown(wait=False)
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_detail = f"Error generating meal plan: {error_msg}"
        print(error_detail)
        
        # Check for various error types that should trigger fallback
        error_str_lower = error_msg.lower()
        is_quota_error = (
            "429" in error_msg or 
            "quota" in error_str_lower or 
            "resource_exhausted" in error_str_lower or
            "exceeded" in error_str_lower
        )
        is_auth_error = (
            "401" in error_msg or 
            "unauthorized" in error_str_lower or
            "unauthenticated" in error_str_lower or
            "api keys are not supported" in error_str_lower or
            "credentials_missing" in error_str_lower
        )
        is_null_error = (
            "null" in error_str_lower and "not defined" in error_str_lower
        )
        is_llm_invalid_response = (
            "invalid response from llm call" in error_str_lower and
            ("none or empty" in error_str_lower or "none" in error_str_lower)
        )

        # Para quota errors, tentar novamente após espera em vez de fallback imediato
        if is_quota_error and not is_auth_error:
            print("⏳ Quota do Gemini excedida, aguardando 60s para tentar novamente...")
            import time
            time.sleep(60)

            try:
                # Tentar novamente uma vez
                print("🔄 Tentando novamente após espera...")
                result = await asyncio.wait_for(
                    loop.run_in_executor(executor, generate_meal_plan, user_query),
                    timeout=1500.0
                )
                # Se chegou aqui, conseguiu gerar o plano
                if isinstance(result, dict):
                    meal_plan_text = result.get("final_plan", "")
                    steps = result.get("steps", {})

                    artifacts = {
                        "personal_model": steps.get("personal_model", ""),
                        "diabetic_analysis": steps.get("diabetic_analysis", ""),
                        "causal_inference": steps.get("causal_inference", ""),
                        "retrieval": steps.get("retrieval", ""),
                        "structured_prompt": steps.get("structured_prompt", ""),
                        "meal_plan": steps.get("meal_plan", ""),
                        "judge_output": steps.get("judge_output", ""),
                        "final_plan": meal_plan_text,
                    }
                    plan_json = result.get("plan_json", {})

                    return MealPlanResponse(
                        success=True,
                        meal_plan=meal_plan_text,
                        artifacts=artifacts,
                        plan_json=plan_json,
                        message="Plano gerado com sucesso após retry"
                    )
            except Exception as retry_error:
                print(f"❌ Retry também falhou: {str(retry_error)}")
                # Continua para fallback

        # If it's a quota error (após retry), auth error, null error, or LLM invalid response, return fallback structure
        if is_quota_error or is_auth_error or is_null_error or is_llm_invalid_response:
            print("⚠️  Usando fallback após falha definitiva")
            from services.plan_json_service import PlanJsonService
            from services.diabetic_service import DiabeticService

            # Get user's glucose readings for metrics
            glucose_readings = user_query.get("glucose_readings", [])
            diabetic_service = DiabeticService()
            diabetic_analysis = diabetic_service.analyze(glucose_readings)

            # Create fallback plan
            fallback_service = PlanJsonService()
            diabetes_type = user_query.get("health_metrics", {}).get("diabetes_type", "Diabetes Tipo 2")
            fallback_plan = f"Plano nutricional para {diabetes_type}"
            plan_json = fallback_service._create_fallback_structure(fallback_plan, diabetic_analysis)

            if is_auth_error:
                msg = "Plano gerado com estrutura padrão. Erro de autenticação com Gemini - verifique a chave API."
            elif is_quota_error:
                msg = "Plano gerado com estrutura padrão. A quota do Gemini foi excedida mesmo após retry."
            elif is_llm_invalid_response:
                msg = "Plano gerado com estrutura padrão. A resposta do modelo de IA foi inválida - pode ser um problema temporário."
            else:
                msg = "Plano gerado com estrutura padrão devido a um erro no processamento."

            return MealPlanResponse(
                success=True,
                meal_plan="Plano gerado usando estrutura padrão",
                artifacts=None,
                plan_json=plan_json,
                message=msg
            )
        
        raise HTTPException(status_code=500, detail=error_detail)


@api_router.post("/diabetic/analyze")
async def diabetic_analyze(request: DiabeticRequest):
    return gateway_service.diabetic_analyze({"glucose_readings": request.glucose_readings or []})


@api_router.post("/nutrition/analyze")
async def nutrition_analyze(request: MealPlanRequest):
    return gateway_service.nutrition_analyze(request.dict())


@api_router.post("/judge/consolidate")
async def judge_consolidate(request: JudgeRequest):
    return gateway_service.judge_consolidate(request.dict())


@api_router.post("/causal/analyze")
async def causal_analyze(request: CausalRequest):
    payload = {
        "meal_history": request.meal_history or [],
        "glucose_readings": [reading.dict() for reading in (request.glucose_readings or [])],
    }
    return gateway_service.causal_analyze(payload)


@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = chat_service.respond(request.message, request.history or [])
    return ChatResponse(success=True, reply=reply)


@api_router.get("/meal-plan/example")
async def get_example_request():
    """
    Get an example request payload for testing
    
    This endpoint returns an example of the request structure
    that can be used to test the /meal-plan/generate endpoint.
    """
    return {
        "example_request": {
            "meal_history": [
                "Café da manhã: Pão integral com queijo, café sem açúcar",
                "Almoço: Arroz, feijão, frango grelhado, salada",
                "Jantar: Sopa de legumes"
            ],
            "health_metrics": {
                "diabetes_type": "Type 2",
                "glucose_levels": "Elevated (140-180 mg/dL)",
                "weight": "85 kg",
                "height": "1.75 m"
            },
            "preferences": {
                "cuisine": "Brasileira",
                "region": "Sudeste",
                "likes": ["feijão", "frutas", "vegetais", "carne"],
                "dislikes": ["comida muito doce"]
            },
            "goals": [
                "Controlar glicemia",
                "Perder peso moderadamente",
                "Melhorar saúde cardiovascular"
            ],
            "restrictions": [
                "Diabetes tipo 2",
                "Limitar carboidratos refinados",
                "Evitar açúcar adicionado"
            ],
            "region": "Sudeste brasileiro",
            "inventory": ["arroz integral", "feijão", "frango", "legumes"],
            "glucose_readings": [
                {"timestamp": "2026-01-10T08:00:00", "value_mg_dl": 135},
                {"timestamp": "2026-01-10T12:00:00", "value_mg_dl": 190},
                {"timestamp": "2026-01-10T18:00:00", "value_mg_dl": 160}
            ]
        }
    }


@api_router.get("/meal-plan/history", response_model=PlanHistoryResponse)
async def list_saved_plans():
    items = list_plans(limit=20)
    return PlanHistoryResponse(
        success=True,
        items=[
            PlanHistoryItem(id=item["id"], created_at=item["created_at"], plan_json=item["plan_json"])
            for item in items
        ],
    )


@api_router.post("/users", response_model=UserResponse)
async def create_user_endpoint(profile: UserProfile):
    if not profile:
        raise HTTPException(status_code=400, detail="Profile is required")
    if "auth_user_id" in profile.dict():
        auth_user_id = profile.dict().get("auth_user_id")
    else:
        auth_user_id = None
    if not auth_user_id:
        raise HTTPException(status_code=400, detail="auth_user_id is required")
    # Merge with empty profile to ensure all fields exist
    from .storage import create_empty_profile
    empty_profile = create_empty_profile()
    profile_dict = profile.dict()
    # Merge non-None values into empty profile
    for key, value in profile_dict.items():
        if value is not None:
            if isinstance(value, dict) and key in empty_profile and isinstance(empty_profile[key], dict):
                empty_profile[key].update(value)
            else:
                empty_profile[key] = value
    user_id = create_user(empty_profile, auth_user_id=auth_user_id)
    stored = get_user(user_id)
    return UserResponse(**stored)


@api_router.get("/users", response_model=List[UserResponse])
async def list_users_endpoint():
    return [UserResponse(**item) for item in list_users()]


@api_router.get("/users/by-auth/{auth_user_id}", response_model=UserResponse)
async def get_user_by_auth_endpoint(auth_user_id: int):
    """Get user profile by auth_user_id"""
    stored = get_user_by_auth_id(auth_user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**stored)


@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_endpoint(user_id: int):
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**stored)


@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(user_id: int, profile: UserProfile):
    # Get existing profile to merge
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    existing_profile = stored["profile"]
    # Merge new data with existing (new data takes precedence, but preserve existing nested data)
    # Get all fields from the profile model
    profile_dict = profile.dict(exclude_none=False)
    merged_profile = existing_profile.copy() if existing_profile else {}
    
    for key, value in profile_dict.items():
        # Skip None values and empty strings only if they're not being explicitly set
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue  # Skip empty strings
        if isinstance(value, dict) and key in merged_profile and isinstance(merged_profile[key], dict):
            # Deep merge for nested objects (health_metrics, preferences)
            for nested_key, nested_value in value.items():
                # Only update nested values if they're not None or empty
                if nested_value is not None and not (isinstance(nested_value, str) and nested_value.strip() == ""):
                    merged_profile[key][nested_key] = nested_value
        elif isinstance(value, list):
            # For lists (restrictions, allergies, goals, inventory), replace if provided
            merged_profile[key] = value
        else:
            # For simple values, replace if provided
            merged_profile[key] = value
    
    # Ensure required nested structures exist
    if "health_metrics" not in merged_profile:
        merged_profile["health_metrics"] = {}
    if "preferences" not in merged_profile:
        merged_profile["preferences"] = {}
    
    # Log for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Updating user {user_id} with profile: {merged_profile}")
    
    updated = update_user(user_id, merged_profile)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**updated)


@api_router.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: int):
    deleted = delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}


@api_router.post("/auth/register", response_model=AuthResponse)
async def register_user(request: AuthRegisterRequest):
    existing = get_auth_user_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    password_hash = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    auth_user_id = create_auth_user(request.email, password_hash)
    # Create empty user profile automatically
    user_id = create_user_with_empty_profile(auth_user_id)
    return AuthResponse(success=True, user_id=auth_user_id)


@api_router.post("/auth/login", response_model=AuthResponse)
async def login_user(request: AuthLoginRequest):
    existing = get_auth_user_by_email(request.email)
    if not existing:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(request.password.encode("utf-8"), existing["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(success=True, user_id=existing["id"])


@api_router.get("/meal-plan/{plan_id}")
async def get_saved_plan(plan_id: int):
    item = get_plan(plan_id)
    if not item:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {
        "success": True,
        "plan_id": item["id"],
        "created_at": item["created_at"],
        "request": item["request_payload"],
        "response": item["response_payload"],
    }


# ============================================================================
# User Data Management Endpoints
# ============================================================================

@api_router.put("/users/{user_id}/health-metrics")
async def update_health_metrics(user_id: int, health_metrics: HealthMetrics):
    """Update user's health metrics (clinical and anthropometric data)"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    profile = stored["profile"]
    # Convert health_metrics to dict, excluding None values to allow partial updates
    health_dict = health_metrics.dict(exclude_none=True)
    # Merge with existing health_metrics (don't overwrite entire dict)
    if "health_metrics" not in profile:
        profile["health_metrics"] = {}
    profile["health_metrics"].update(health_dict)
    updated = update_user(user_id, profile)
    return UserResponse(**updated)


@api_router.put("/users/{user_id}/preferences")
async def update_preferences(user_id: int, preferences: Preferences):
    """Update user's food preferences and cultural preferences"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    profile = stored["profile"]
    profile["preferences"] = preferences.dict()
    updated = update_user(user_id, profile)
    return UserResponse(**updated)


@api_router.put("/users/{user_id}/restrictions")
async def update_restrictions(user_id: int, restrictions: List[str]):
    """Update user's dietary restrictions"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    profile = stored["profile"]
    profile["restrictions"] = restrictions
    updated = update_user(user_id, profile)
    return UserResponse(**updated)


@api_router.put("/users/{user_id}/inventory")
async def update_inventory(user_id: int, inventory: List[str]):
    """Update user's household inventory"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    profile = stored["profile"]
    profile["inventory"] = inventory
    updated = update_user(user_id, profile)
    return UserResponse(**updated)


@api_router.post("/users/{user_id}/glucose-readings")
async def add_glucose_reading(user_id: int, reading: GlucoseReading):
    """Add a new glucose reading to user's history"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    profile = stored["profile"]
    if "glucose_readings" not in profile:
        profile["glucose_readings"] = []
    profile["glucose_readings"].append(reading.dict())
    updated = update_user(user_id, profile)
    return {"success": True, "reading": reading.dict()}


@api_router.get("/users/{user_id}/glucose-readings")
async def get_glucose_readings(user_id: int, limit: int = 100):
    """Get user's glucose readings history for charts"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    readings = stored["profile"].get("glucose_readings", [])
    # Sort by timestamp descending and limit
    sorted_readings = sorted(readings, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
    return {
        "success": True,
        "readings": sorted_readings,
        "count": len(sorted_readings)
    }


@api_router.get("/users/{user_id}/glucose-stats")
async def get_glucose_stats(user_id: int):
    """Get glucose statistics (TIR/TAR/TBR) for charts"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")
    readings = stored["profile"].get("glucose_readings", [])
    
    if not readings:
        return {
            "success": True,
            "tir": 0,
            "tar": 0,
            "tbr": 0,
            "average": 0,
            "count": 0
        }
    
    # Calculate TIR/TAR/TBR (assuming target range 70-140 mg/dL)
    target_min = 70
    target_max = 140
    in_range = 0
    above_range = 0
    below_range = 0
    total = 0
    
    for reading in readings:
        value = reading.get("value_mg_dl", 0)
        if value > 0:
            total += value
            if target_min <= value <= target_max:
                in_range += 1
            elif value > target_max:
                above_range += 1
            else:
                below_range += 1
    
    count = len(readings)
    return {
        "success": True,
        "tir": round((in_range / count * 100) if count > 0 else 0, 2),
        "tar": round((above_range / count * 100) if count > 0 else 0, 2),
        "tbr": round((below_range / count * 100) if count > 0 else 0, 2),
        "average": round(total / count if count > 0 else 0, 2),
        "count": count
    }


@api_router.get("/users/{user_id}/plan-history")
def get_user_plan_history(user_id: int, limit: int = 20):
    """Get user's meal plan history and adherence"""
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")

    import sqlite3
    import os

    db_path = os.path.join(os.path.dirname(__file__), "data", "diabetesai.db")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query otimizada usando json_extract
        cursor.execute("""
            SELECT id, created_at, request_payload, response_payload
            FROM plans
            WHERE json_extract(request_payload, '$.user_id') = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))

        results = cursor.fetchall()

        user_plans = []
        for row in results:
            plan_id, created_at, request_payload, response_payload = row

            # Parse JSON response
            try:
                if isinstance(response_payload, str):
                    response_payload = json.loads(response_payload)
                plan_json = (response_payload or {}).get("plan_json")
            except Exception as e:
                print(f"Erro ao parsear plano {plan_id}: {e}")
                plan_json = None

            user_plans.append({
                "id": plan_id,
                "created_at": created_at,
                "plan_json": plan_json,
                "summary": (plan_json or {}).get("summary", {})
            })

        conn.close()

        return {
            "success": True,
            "plans": user_plans,
            "count": len(user_plans)
        }

    except Exception as e:
        print(f"Erro na busca de histórico para usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@api_router.get("/test/user/{user_id}")
def test_user_plans(user_id: int):
    """Simple test endpoint"""
    import sqlite3
    import os

    db_path = os.path.join(os.path.dirname(__file__), "data", "diabetesai.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM plans
        WHERE json_extract(request_payload, '$.user_id') = ?
    """, (user_id,))

    count = cursor.fetchone()[0]
    conn.close()

    return {"user_id": user_id, "plan_count": count}


# Cache simples para planos recentes (em memória)
_plan_cache = {}
_CACHE_TIMEOUT = 300  # 5 minutos

def _get_cached_plan(user_id: int):
    """Busca plano em cache se ainda válido"""
    cache_key = f"user_{user_id}_latest"
    if cache_key in _plan_cache:
        cached_data, timestamp = _plan_cache[cache_key]
        if time.time() - timestamp < _CACHE_TIMEOUT:
            return cached_data
        else:
            # Remove cache expirado
            del _plan_cache[cache_key]
    return None

def _set_cached_plan(user_id: int, plan_data: dict):
    """Armazena plano no cache"""
    cache_key = f"user_{user_id}_latest"
    _plan_cache[cache_key] = (plan_data, time.time())

def _get_latest_user_plan(user_id: int) -> Optional[Dict[str, Any]]:
    """Busca o plano mais recente do usuário usando query otimizada"""
    import sqlite3
    import os
    import json

    # Verifica cache primeiro
    cached = _get_cached_plan(user_id)
    if cached:
        return cached

    db_path = os.path.join(os.path.dirname(__file__), "data", "diabetesai.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query otimizada usando json_extract
        cursor.execute("""
            SELECT id, created_at, request_payload, response_payload
            FROM plans
            WHERE json_extract(request_payload, '$.user_id') = ?
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            plan_id, created_at, request_payload, response_payload = row

            # Parse response JSON
            try:
                if isinstance(response_payload, str):
                    response_payload = json.loads(response_payload)
                plan_json = (response_payload or {}).get("plan_json")
                meal_plan = (response_payload or {}).get("meal_plan")
                artifacts = (response_payload or {}).get("artifacts")
            except Exception as e:
                print(f"Erro ao parsear plano {plan_id}: {e}")
                plan_json = None
                meal_plan = None
                artifacts = None

            plan_data = {
                "success": True,
                "plan_id": plan_id,
                "created_at": created_at,
                "meal_plan": meal_plan,
                "plan_json": plan_json,
                "artifacts": artifacts,
                "message": f"Plano existente carregado (ID: {plan_id})",
                "cached": False
            }

            # Armazena em cache
            _set_cached_plan(user_id, plan_data)

            return plan_data

    except Exception as e:
        print(f"Erro ao buscar plano do usuário {user_id}: {e}")

    return None

@api_router.get("/users/{user_id}/plan")
async def get_or_generate_user_plan(user_id: int, force_generate: bool = False):
    """
    Endpoint unificado: busca plano existente ou gera novo
    Query params:
    - force_generate: true para forçar geração de novo plano
    """
    print(f"DEBUG: Endpoint chamado para user_id={user_id}, force_generate={force_generate}")

    # Busca plano existente primeiro (sempre tenta cache/plano salvo)
    existing_plan = _get_latest_user_plan(user_id)
    print(f"DEBUG: existing_plan is None: {existing_plan is None}")

    if existing_plan and not force_generate:
        print(f"DEBUG: existing_plan plan_json: {existing_plan.get('plan_json') is not None}")
        existing_plan["cached"] = True
        return existing_plan

    # Se não encontrou plano existente ou foi forçado, gera novo
    stored = get_user(user_id)
    if not stored:
        raise HTTPException(status_code=404, detail="User not found")

    profile = stored.get("profile", {})

    # Valida dados mínimos
    health_metrics = profile.get("health_metrics", {})
    if not health_metrics or not health_metrics.get("diabetes_type"):
        raise HTTPException(
            status_code=400,
            detail="Perfil incompleto. Por favor, preencha os dados clínicos primeiro."
        )

    # Prepara request
    meal_plan_request = MealPlanRequest(
        meal_history=profile.get("meal_history", []),
        health_metrics=HealthMetrics(**health_metrics) if health_metrics else None,
        preferences=Preferences(**profile.get("preferences", {})) if profile.get("preferences") else None,
        goals=profile.get("goals", []),
        restrictions=profile.get("restrictions", []),
        region=profile.get("region"),
        inventory=profile.get("inventory", []),
        glucose_readings=[GlucoseReading(**r) for r in profile.get("glucose_readings", [])] if profile.get("glucose_readings") else [],
        user_id=user_id
    )

    # Gera plano
    result = await generate_meal_plan_endpoint(meal_plan_request)

    # Invalida cache
    cache_key = f"user_{user_id}_latest"
    if cache_key in _plan_cache:
        del _plan_cache[cache_key]

    return result

@api_router.get("/users/{user_id}/generate-daily-plan")
async def generate_daily_plan_dynamic(user_id: int):
    """Legacy endpoint - redireciona para o novo endpoint unificado"""
    return await get_or_generate_user_plan(user_id, force_generate=True)


class ConsumedMealRequest(BaseModel):
    """Request model for recording a consumed meal"""
    meal_type: str = Field(..., description="Type of meal (e.g., 'Café da manhã', 'Almoço')")
    meal_name: str = Field(..., description="Name of the meal")
    plan_id: Optional[int] = Field(None, description="ID of the related meal plan")
    notes: Optional[str] = Field(None, description="Optional notes about the meal")


class AdherenceResponse(BaseModel):
    """Response model for adherence metrics"""
    total_planned: int
    total_consumed: int
    matched_meals: int
    adherence_percentage: float
    by_meal_type: Dict[str, Dict[str, int]]
    consumed_meals: List[Dict[str, Any]]


@api_router.post("/users/{user_id}/consumed-meals")
async def record_consumed_meal(user_id: int, request: ConsumedMealRequest):
    """Record a consumed meal for adherence tracking"""
    try:
        meal_id = save_consumed_meal(
            user_id=user_id,
            meal_type=request.meal_type,
            meal_name=request.meal_name,
            plan_id=request.plan_id,
            notes=request.notes,
        )
        return {
            "success": True,
            "meal_id": meal_id,
            "message": "Refeição registrada com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar refeição: {str(e)}")


@api_router.get("/users/{user_id}/consumed-meals")
async def get_user_consumed_meals(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """Get consumed meals for a user"""
    from datetime import datetime

    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None

    meals = get_consumed_meals(user_id, start, end, limit)
    return {
        "success": True,
        "meals": meals,
        "count": len(meals)
    }


@api_router.delete("/users/{user_id}/consumed-meals/{consumed_meal_id}")
async def delete_consumed_meal_endpoint(user_id: int, consumed_meal_id: int):
    """Delete a consumed meal record (unmark as consumed)"""
    try:
        success = delete_consumed_meal(consumed_meal_id, user_id)
        if success:
            return {
                "success": True,
                "message": "Refeição removida do registro de consumidas"
            }
        else:
            raise HTTPException(status_code=404, detail="Refeição consumida não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover refeição: {str(e)}")


@api_router.get("/users/{user_id}/adherence")
async def get_user_adherence(
    user_id: int,
    plan_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get adherence metrics for a user's meal plan"""
    from datetime import datetime
    
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    adherence = calculate_adherence(user_id, plan_id, start, end)
    
    if "error" in adherence:
        raise HTTPException(status_code=404, detail=adherence["error"])
    
    return {
        "success": True,
        **adherence
    }


@api_router.post("/meal-plan/validate")
async def validate_meal_plan(request: MealPlanRequest):
    """Validate macronutrients and micronutrients of a meal plan"""
    from services.nutrition_validation_service import NutritionValidationService
    
    validation_service = NutritionValidationService()
    
    # Extract meals from request
    meals = []
    if request.meal_history:
        # Try to parse meal history
        for meal_str in request.meal_history:
            meals.append({"name": meal_str, "macros": meal_str})
    
    # If no meals, create a sample validation
    if not meals:
        meals = [
            {"name": "Refeição exemplo", "macros": "Carbs: 50g, Proteína: 20g, Gordura: 15g"}
        ]
    
    # Get target calories from health metrics
    target_calories = 2000  # Default
    if request.health_metrics:
        weight = request.health_metrics.weight
        if weight:
            try:
                weight_kg = float(str(weight).replace('kg', '').strip())
                # Estimativa: 25-30 kcal/kg para DM2
                target_calories = weight_kg * 25
            except:
                pass
    
    diabetes_type = request.health_metrics.diabetes_type if request.health_metrics else "Type 2"
    
    validation = validation_service.validate_meal_plan(meals, target_calories)
    
    return {
        "success": True,
        "validation": validation,
        "target_calories": target_calories
    }


@api_router.post("/food/substitutions")
async def get_food_substitutions(
    food_name: str,
    max_results: int = 5,
    restrictions: Optional[List[str]] = None
):
    """Get nutritional substitutions for a food item"""
    from services.food_substitution_service import FoodSubstitutionService
    
    substitution_service = FoodSubstitutionService()
    
    substitutions = substitution_service.find_substitutions(
        food_name,
        max_results=max_results,
        restrictions=restrictions or []
    )
    
    return {
        "success": True,
        "original": food_name,
        "substitutions": substitutions
    }


@api_router.get("/food/{food_name}/nutrition")
async def get_food_nutrition(food_name: str):
    """Get detailed nutritional information for a food item"""
    from services.food_substitution_service import FoodSubstitutionService
    import unicodedata
    
    substitution_service = FoodSubstitutionService()
    
    # Buscar alimento na base de dados
    food_lower = food_name.lower().strip()
    
    # Normalizar nome (remover acentos)
    food_normalized = unicodedata.normalize('NFKD', food_lower)
    food_normalized = ''.join(c for c in food_normalized if not unicodedata.combining(c))
    
    food_data = substitution_service._nutrition_db.get(food_lower) or substitution_service._nutrition_db.get(food_normalized)
    
    if not food_data:
        # Tentar busca parcial
        keywords = [w for w in food_lower.split() if len(w) > 2]
        best_match = None
        best_score = 0
        
        for key, item in substitution_service._nutrition_db.items():
            key_normalized = unicodedata.normalize('NFKD', key)
            key_normalized = ''.join(c for c in key_normalized if not unicodedata.combining(c))
            
            score = 0
            matched = 0
            for keyword in keywords:
                if keyword in key or keyword in key_normalized:
                    matched += 1
                    score += len(keyword) / max(len(key), 1)
            
            if matched > 0 and score > best_score:
                best_score = score
                best_match = item
        
        if best_match:
            food_data = best_match
    
    if not food_data:
        raise HTTPException(status_code=404, detail=f"Food '{food_name}' not found in database")
    
    # Extrair informações nutricionais
    nutrients = substitution_service._extract_nutrients(food_data)
    
    return {
        "success": True,
        "food_name": food_data.get('name_taco_descricao') or food_data.get('name_full', food_name),
        "nutrition": nutrients,
        "raw_data": food_data  # Para debug
    }


@api_router.post("/meal-plan/{plan_id}/substitutions")
async def get_meal_plan_substitutions(plan_id: int, restrictions: Optional[List[str]] = None):
    """Get substitutions for all meals in a plan"""
    from services.food_substitution_service import FoodSubstitutionService
    
    plan_data = get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan_json = plan_data.get("response_payload", {}).get("plan_json", {})
    meals = plan_json.get("meals", [])
    
    if not meals:
        raise HTTPException(status_code=400, detail="No meals found in plan")
    
    substitution_service = FoodSubstitutionService()
    all_substitutions = []
    
    for meal in meals:
        meal_name = meal.get("name") or meal.get("meal_type", "")
        items = meal.get("items", [])
        
        meal_subs = {
            "meal": meal_name,
            "substitutions": []
        }
        
        # Get substitutions for each item
        for item in items[:3]:  # Limitar a 3 itens por refeição
            if isinstance(item, str):
                item_name = item.split(',')[0].strip()
                subs = substitution_service.find_substitutions(
                    item_name,
                    max_results=3,
                    restrictions=restrictions or []
                )
                if subs:
                    meal_subs["substitutions"].append({
                        "original": item,
                        "alternatives": subs
                    })
        
        if meal_subs["substitutions"]:
            all_substitutions.append(meal_subs)
    
    return {
        "success": True,
        "plan_id": plan_id,
        "substitutions": all_substitutions
    }


@api_router.post("/meal-plan/{plan_id}/text-to-speech")
async def generate_plan_speech(plan_id: int):
    """Generate text-to-speech audio for a meal plan"""
    item = get_plan(plan_id)
    if not item:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan_json = item.get("response_payload", {}).get("plan_json", {})
    plan_text = item.get("response_payload", {}).get("meal_plan", "")
    
    # For now, return the text. In production, you'd use a TTS service
    # like Google Cloud TTS, AWS Polly, or similar
    return {
        "success": True,
        "text": plan_text,
        "audio_url": None,  # Would be URL to generated audio file
        "message": "TTS not yet implemented. Text available for browser TTS."
    }


# Include API router (after all routes are defined)
app.include_router(api_router)

# ============================================================================
# Run the API
# ============================================================================

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,       # Port 8000
        reload=True      # Auto-reload on code changes (development only)
    )

