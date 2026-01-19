"""
Meal Planning RAG System with CrewAI
Implements collaborative agents for personalized meal planning considering type 2 diabetes
Following the infrastructure schema for meal plan generation
"""

import os
import json
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from .rag_system import initialize_rag_system
from .llm_providers import get_llm
from .llm_with_rate_limit import create_rate_limited_llm

# Load environment variables
load_dotenv()

# Initialize LLM (suporta múltiplos provedores)
base_llm = get_llm(provider=None, temperature=0.7)

# Aplicar rate limiting para Gemini (10 requisições/minuto)
# Apenas se estiver usando Gemini
provider = os.getenv("LLM_PROVIDER", "gemini").lower()
gemini_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
if provider == "gemini":
    print(f"🔒 Aplicando rate limiting para {gemini_model}: máximo 10 requisições/minuto")
    llm = create_rate_limited_llm(base_llm, max_requests=10, time_window=60.0)
else:
    llm = base_llm

# Initialize RAG system (will be done when module loads)
# This is initialized at module level so agents can use the tool
_rag_loader = None
_rag_tool = None

def _init_rag():
    """Initialize RAG system (lazy initialization)"""
    global _rag_loader, _rag_tool
    if _rag_tool is None:
        print("Initializing RAG system...")
        _rag_loader, _rag_tool = initialize_rag_system(force_reload=False)
    return _rag_loader, _rag_tool

# Initialize RAG system
loader, rag_tool = _init_rag()


# ============================================================================
# AGENTS - Following the Infrastructure Schema
# ============================================================================

# Agent 1: Personal Model Analyst
# Analyzes personal data: meal history, health metrics, food preferences
personal_model_agent = Agent(
    role="Personal Model Analyst",
    goal="Analyze the user's personal model: meal history, health metrics, and food preferences for type 2 diabetes.",
    backstory="You are an expert nutritionist specializing in type 2 diabetes. Analyze user data to create a personal model. Use the RAG tool efficiently (limit to 2-3 queries).",
    tools=[rag_tool.tool],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=3,  # Limit iterations
)

# Agent 2: Diabetic Specialist
# Processes glycemic time series, computes TIR/TAR/TBR, and generates alerts
diabetic_specialist_agent = Agent(
    role="Diabetic Specialist",
    goal="Analyze glucose time series, compute TIR/TAR/TBR, and generate risk alerts for type 2 diabetes.",
    backstory="You are a clinical diabetes specialist. Use the provided metrics and readings to summarize glycemic control and provide safety alerts.",
    tools=[],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=2,
)

# Agent 3: Causal Inference Specialist
# Performs causal discovery and inference from meal history and health metrics
causal_inference_agent = Agent(
    role="Causal Inference Specialist",
    goal="Identify causal patterns between meals and health outcomes for type 2 diabetes.",
    backstory="You analyze meal patterns and health metrics to find causal relationships. Use RAG tool efficiently (1-2 queries max).",
    tools=[rag_tool.tool],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=2,  # Limit iterations
)

# Agent 4: Nutritional Information Retriever
# Retrieves relevant nutritional information from the database
nutritional_retriever_agent = Agent(
    role="Nutritional Information Retriever",
    goal="Retrieve relevant nutritional information for type 2 diabetes meal planning.",
    backstory="You retrieve nutritional information from the database. Use RAG tool efficiently (1-2 queries max).",
    tools=[rag_tool.tool],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=2,  # Limit iterations
)

# Agent 5: Prompt Structuring Specialist
# Structures the prompt for the AI model based on retrieved information
prompt_structured_agent = Agent(
    role="Prompt Structuring Specialist",
    goal="Structure prompts for meal plan generation using the provided context.",
    backstory="You combine information into structured prompts. Work efficiently with the context provided.",
    tools=[],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=2,  # Limit iterations
)

# Agent 6: Meal Plan Synthesizer
# Synthesizes all information into a comprehensive meal plan
meal_plan_synthesizer_agent = Agent(
    role="Meal Plan Synthesizer",
    goal="Generate a comprehensive, personalized meal plan considering type 2 diabetes, "
         "personal goals, restrictions, variety, and regional preferences. Create plans "
         "for breakfast, lunch, and dinner.",
    backstory="""You are an expert nutritionist and meal planning specialist with
    extensive experience in creating personalized meal plans for individuals with
    type 2 diabetes. You excel at synthesizing complex information from multiple
    sources to create practical, varied, and regionally appropriate meal plans.
    You ensure that meal plans consider goals, restrictions, nutritional balance,
    and dietary preferences while maintaining variety and cultural relevance.""",
    tools=[],  # Removed RAG tool - all information is already in context from previous tasks
    verbose=False,  # Reduzido para melhorar performance
    allow_delegation=True,  # Habilitado para melhor colaboração
    llm=llm,
    max_iter=2,  # Reduzido para economizar quota
)

# Agent 7: Judge/Orchestrator
# Resolves conflicts and consolidates a final actionable plan
judge_agent = Agent(
    role="Judge Orchestrator",
    goal="Validate and consolidate recommendations into a single actionable daily plan.",
    backstory="You reconcile conflicts between nutrition and diabetes constraints, ensuring safety and clarity.",
    tools=[],
    verbose=False,  # Reduzido para performance
    allow_delegation=True,  # Habilitado para melhor coordenação
    llm=llm,
    max_iter=2,
)

# Agent 8: Plan JSON Formatter
# Converts the final plan into a strict JSON schema for UI/storage
plan_json_agent = Agent(
    role="Plan JSON Formatter",
    goal="Convert the final plan into a strict JSON schema with daily meals and alerts.",
    backstory="You output valid JSON only, following the provided schema exactly.",
    tools=[],
    verbose=True,
    allow_delegation=False,
    llm=llm,
    max_iter=2,
)


# ============================================================================
# TASKS - Following the Infrastructure Schema Workflow
# ============================================================================

def _compute_glycemic_metrics(glucose_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not glucose_readings:
        return {
            "count": 0,
            "tir_pct": None,
            "tar_pct": None,
            "tbr_pct": None,
            "avg_mg_dl": None,
            "min_mg_dl": None,
            "max_mg_dl": None,
        }

    values = [reading.get("value_mg_dl") for reading in glucose_readings if reading.get("value_mg_dl") is not None]
    if not values:
        return {
            "count": 0,
            "tir_pct": None,
            "tar_pct": None,
            "tbr_pct": None,
            "avg_mg_dl": None,
            "min_mg_dl": None,
            "max_mg_dl": None,
        }

    total = len(values)
    tir = sum(1 for v in values if 70 <= v <= 180)
    tar = sum(1 for v in values if v > 180)
    tbr = sum(1 for v in values if v < 70)
    avg = sum(values) / total

    return {
        "count": total,
        "tir_pct": round((tir / total) * 100, 2),
        "tar_pct": round((tar / total) * 100, 2),
        "tbr_pct": round((tbr / total) * 100, 2),
        "avg_mg_dl": round(avg, 2),
        "min_mg_dl": min(values),
        "max_mg_dl": max(values),
    }


def _parse_json_output(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}
    return {}


def create_meal_planning_tasks(user_query: dict):
    """
    Create tasks for meal planning workflow
    
    Args:
        user_query: Dictionary containing:
            - meal_history: List of previous meals
            - health_metrics: Dict with health data (e.g., glucose levels, weight)
            - preferences: Dict with dietary preferences
            - goals: List of goals (e.g., weight loss, glucose control)
            - restrictions: List of restrictions (e.g., allergies, dietary restrictions)
            - region: Regional preferences (e.g., "brasileira", "nordeste")
    """
    
    # Task 1: Analyze Personal Model
    analyze_personal_model_task = Task(
        description=f"""Analyze the user's personal model:
        
        Meal History: {user_query.get('meal_history', 'Not provided')}
        Health Metrics: {user_query.get('health_metrics', 'Not provided')}
        Food Preferences: {user_query.get('preferences', 'Not provided')}
        Inventory: {user_query.get('inventory', 'Not provided')}
        Goals: {user_query.get('goals', 'Not provided')}
        Restrictions: {user_query.get('restrictions', 'Not provided')}
        Region: {user_query.get('region', 'Not specified')}
        
        Create a comprehensive personal model that summarizes:
        1. Patterns in meal history
        2. Key health metrics (especially relevant to type 2 diabetes)
        3. Dietary preferences and cultural/regional preferences
        4. Stated goals and restrictions
        5. Inventory constraints (available foods)
        
        Consider type 2 diabetes management requirements in your analysis.""",
        agent=personal_model_agent,
        expected_output="A comprehensive personal model analysis document",
    )
    
    # Task 2: Diabetic Analysis (TIR/TAR/TBR + alerts)
    glucose_readings = user_query.get("glucose_readings", [])
    glycemic_metrics = _compute_glycemic_metrics(glucose_readings)
    diabetic_analysis_task = Task(
        description=f"""Analyze glycemic data and generate alerts:

        Glucose readings: {glucose_readings if glucose_readings else 'Not provided'}
        Metrics: {glycemic_metrics}

        Produce:
        1. TIR/TAR/TBR interpretation
        2. Risk alerts for hypo/hyperglycemia
        3. Short recommendations to improve glycemic control
        """,
        agent=diabetic_specialist_agent,
        expected_output="Glycemic analysis with TIR/TAR/TBR and alerts",
    )

    # Task 3: Causal Inference Analysis
    causal_inference_task = Task(
        description="""Analyze the relationship between the user's meal history and 
        health metrics to identify causal patterns. Focus on:
        
        1. How different foods/meals correlate with health outcomes
        2. Patterns that suggest beneficial or harmful meal choices for type 2 diabetes
        3. Insights about timing, combinations, and portions
        4. Recommendations based on causal patterns discovered
        
        Use the personal model from the previous task and retrieve relevant nutritional 
        information to inform your analysis. Consider inventory constraints.""",
        agent=causal_inference_agent,
        expected_output="A causal inference analysis with patterns and recommendations",
        context=[analyze_personal_model_task, diabetic_analysis_task],
    )
    
    # Task 4: Retrieve Nutritional Information
    retrieval_task = Task(
        description="""Based on the personal model and causal insights, retrieve 
        relevant nutritional information from the knowledge base:
        
        1. Foods appropriate for type 2 diabetes management
        2. Regional foods matching user preferences
        3. Nutritional information for recommended foods
        4. Meal suggestions for diabetics
        
        Focus on retrieving information that supports the user's goals and respects 
        their restrictions and inventory.""",
        agent=nutritional_retriever_agent,
        expected_output="Retrieved nutritional information relevant to the user's needs",
        context=[analyze_personal_model_task, diabetic_analysis_task, causal_inference_task],
    )
    
    # Task 5: Structure Prompt for Meal Plan Generation
    prompt_structuring_task = Task(
        description="""Structure a comprehensive prompt for meal plan generation that 
        incorporates:
        
        1. Personal model analysis
        2. Causal inference insights
        3. Retrieved nutritional information
        4. System instructions: Consider type 2 diabetes and user goals
        5. Inventory constraints (available foods)
        
        The prompt should guide the meal plan generation to consider:
        - Type 2 diabetes management requirements
        - User goals and restrictions
        - Variety and regional preferences
        - Nutritional balance
        - Use available inventory first
        
        Create a well-structured prompt that combines all this information.""",
        agent=prompt_structured_agent,
        expected_output="A structured prompt ready for meal plan generation",
        context=[analyze_personal_model_task, diabetic_analysis_task, causal_inference_task, retrieval_task],
    )
    
    # Task 6: Generate Meal Plan (uses structured prompt from previous task)
    meal_plan_generation_task = Task(
        description=f"""Generate a 5-day meal plan for a person with type 2 diabetes.
        Use the structured prompt from the previous task as primary context. If there
        is any conflict, follow the structured prompt.
        
        USER PROFILE:
        • Health: {user_query.get('health_metrics', {}).get('diabetes_type', 'Type 2 diabetes')}, glucose {user_query.get('health_metrics', {}).get('glucose_levels', 'elevated')}
        • Goals: {', '.join(user_query.get('goals', ['Controlar glicemia']))}
        • Restrictions: {', '.join(user_query.get('restrictions', ['Limitar carboidratos refinados']))}
        • Likes: {', '.join(user_query.get('preferences', {}).get('likes', ['feijão', 'vegetais']))}
        • Dislikes: {', '.join(user_query.get('preferences', {}).get('dislikes', []))}
        • Region: {user_query.get('region', 'Sudeste brasileiro')}
        
        OUTPUT FORMAT (follow exactly - SEMPRE incluir porções em GRAMAS):
        
        SEGUNDA-FEIRA:
        Café da manhã: Pão integral (60g = 2 fatias), queijo branco (30g), mamão (100g = 1 fatia média) | 250 kcal, 35g carbs, 12g proteína
        Almoço: Arroz integral cozido (120g = 4 colheres de sopa), feijão preto cozido (100g = 1 concha média), frango grelhado (120g), salada verde (50g) | 450 kcal, 55g carbs, 35g proteína
        Jantar: Sopa de legumes (300ml), pão integral (30g = 1 fatia) | 300 kcal, 40g carbs, 15g proteína
        
        REGRAS CRÍTICAS:
        1. SEMPRE especificar porções em GRAMAS (ex: "120g", "100g", "50g")
        2. NÃO repetir os mesmos alimentos em refeições consecutivas
        3. Variar alimentos entre os dias (ex: se segunda tem frango, terça tem peixe)
        4. Calorias totais diárias: 1200-1800 kcal (distribuir entre refeições)
        5. Café da manhã: 250-350 kcal
        6. Almoço: 400-550 kcal
        7. Jantar: 300-450 kcal
        8. Lanches (se houver): 100-200 kcal cada
        9. Cada alimento deve ter porção em gramas claramente especificada
        10. Evitar repetir exatamente os mesmos alimentos no mesmo dia
        
        TERÇA-FEIRA:
        Café da manhã: [similar format]
        Almoço: [similar format]
        Jantar: [similar format]
        
        QUARTA-FEIRA:
        [continue...]
        
        QUINTA-FEIRA:
        [continue...]
        
        SEXTA-FEIRA:
        [continue...]
        
        RULES OBRIGATÓRIAS:
        1. Use Brazilian foods (arroz, feijão, frutas, vegetais, carnes magras)
        2. Low glycemic index foods (<55)
        3. High fiber (>25g/day total)
        4. Limit refined carbs and added sugar
        5. SEMPRE incluir porções em GRAMAS para cada alimento (ex: "120g de arroz", "100g de frango")
        6. Varied foods across days - NÃO repetir os mesmos alimentos em dias consecutivos
        7. NÃO repetir a mesma refeição exata em dias diferentes
        8. Calorias totais diárias: 1200-1800 kcal (distribuir entre refeições)
        9. Cada refeição deve ter alimentos diferentes dos outros dias
        10. Especificar claramente: nome do alimento + quantidade em gramas (ex: "Arroz integral cozido (120g)")
        
        Generate the complete plan NOW.""",
        agent=meal_plan_synthesizer_agent,
        expected_output="Complete 5-day meal plan (Monday-Friday) with breakfast, lunch, dinner for each day, including specific foods, portions, and nutritional information appropriate for type 2 diabetes.",
        context=[prompt_structuring_task],
    )

    # Task 7: Judge/Orchestrate Final Plan
    judge_task = Task(
        description="""Validate and consolidate the final plan:

        1. Check conflicts between glycemic alerts and meal plan
        2. Ensure restrictions, goals, and preferences are respected
        3. Validate nutritional values (macronutrients and micronutrients)
        4. Suggest food substitutions if needed based on inventory
        5. Return a finalized, safe, and actionable plan with validation notes
        
        IMPORTANTE: 
        - Valide se os macronutrientes estão dentro das recomendações para DM2
        - Sugira substituições de alimentos quando necessário
        - Garanta que o plano respeita todas as restrições
        """,
        agent=judge_agent,
        expected_output="Final consolidated plan with validation notes and substitution suggestions",
        context=[
            analyze_personal_model_task,
            diabetic_analysis_task,
            causal_inference_task,
            retrieval_task,
            prompt_structuring_task,
            meal_plan_generation_task,
        ],
    )

    # Task 8: Format Final Plan as JSON (schema for frontend/storage)
    plan_json_task = Task(
        description="""Convert the final plan into JSON only (no extra text).

        IMPORTANT: Include SPECIFIC TIMES for each meal and event.
        
        Schema:
        {
          "summary": {
            "goal": string,
            "region": string,
            "restrictions": [string],
            "glycemic_metrics": {"tir_pct": number|null, "tar_pct": number|null, "tbr_pct": number|null},
            "alerts": [string],
            "meals_planned": number,
            "glucose_checks": number,
            "activities": number
          },
          "meals": [
            {
              "meal_type": "Café da manhã",
              "name": "Nome da refeição",
              "description": "Descrição detalhada com ingredientes e porções",
              "items": ["Item 1 (porção)", "Item 2 (porção)"],
              "food_items": [
                {
                  "name": "Nome do alimento",
                  "portion": "100g",
                  "macros": {
                    "calories": 150,
                    "carbs_g": 20,
                    "protein_g": 10,
                    "fat_g": 5,
                    "fiber_g": 3
                  },
                  "glycemic_index": 55,
                  "glycemic_load": 11
                }
              ],
              "total_nutrition": {
                "calories": 250,
                "carbs_g": 30,
                "protein_g": 15,
                "fat_g": 8,
                "fiber_g": 5
              },
              "nutrition": "250 kcal, 30g carbs, 15g proteína",
              "time": "07:30",
              "time_interval": "07:00-08:00"
            }
          ],
          "timeline": [
            {
              "time": "07:00",
              "time_display": "7:00 AM",
              "event_type": "Alert",
              "event_category": "Glucose Check",
              "label": "Alert",
              "description": "Descrição detalhada",
              "color": "red",
              "level": "alert"
            },
            {
              "time": "07:30",
              "time_display": "7:30 AM",
              "event_type": "Meal",
              "event_category": "Breakfast",
              "label": "7:30 AM • Breakfast",
              "description": "Descrição detalhada da refeição com ingredientes",
              "color": "red",
              "level": "meal",
              "meal_type": "Café da manhã"
            },
            {
              "time": "08:30",
              "time_display": "8:30 AM",
              "event_type": "Activity",
              "event_category": "Exercise",
              "label": "8:30 AM • Activity",
              "description": "Descrição da atividade recomendada",
              "color": "yellow",
              "level": "activity"
            }
          ]
        }

        REQUIREMENTS:
        1. Include specific times (HH:MM format) for all meals
        2. Include time intervals (HH:MM-HH:MM) for customizable meal windows
        3. Add glucose check alerts with times (before each main meal)
        4. Add activity recommendations with times (30-60 min after meals)
        5. Use "red" color for alerts and meals, "yellow" for activities and snacks
        6. Include detailed descriptions with ingredients and portions
        7. Count meals_planned, glucose_checks, and activities in summary
        8. For each meal, include a "food_items" array with detailed information:
           - Each food item must have: name, portion (e.g., "100g"), macros (calories, carbs_g, protein_g, fat_g, fiber_g), glycemic_index, glycemic_load
           - Calculate total_nutrition for the entire meal (sum of all food_items)
        9. If you don't have exact nutritional data, estimate based on typical values for that food type

        Use the judge output as the source of truth.
        """,
        agent=plan_json_agent,
        expected_output="Valid JSON object following the schema with specific times and detailed descriptions.",
        context=[judge_task],
    )
    
    return [
        analyze_personal_model_task,
        diabetic_analysis_task,
        causal_inference_task,
        retrieval_task,
        prompt_structuring_task,
        meal_plan_generation_task,
        judge_task,
        plan_json_task,
    ]


# ============================================================================
# MAIN CREW AND EXECUTION
# ============================================================================

def _safe_task_output(task: Task) -> str:
    output = getattr(task, "output", None)
    if output is None:
        return ""
    return str(getattr(output, "raw", output))


def generate_meal_plan(user_query: dict) -> dict:
    """
    Generate a personalized meal plan using the collaborative agent workflow
    Com rate limiting otimizado (10 req/min) para respeitar quota do Gemini

    Args:
        user_query: Dictionary with user information (see create_meal_planning_tasks)

    Returns:
        The generated meal plan
    """
    # Create tasks
    tasks = create_meal_planning_tasks(user_query)

    # Create crew com melhorias
    crew = Crew(
        agents=[
            personal_model_agent,
            diabetic_specialist_agent,
            causal_inference_agent,
            nutritional_retriever_agent,
            prompt_structured_agent,
            meal_plan_synthesizer_agent,
            judge_agent,
            plan_json_agent,
        ],
        tasks=tasks,
        process=Process.sequential,  # Sequencial mas com delegação habilitada
        verbose=False,  # Reduzido para melhor performance
    )

    # Execute - rate limiting já é aplicado no nível do LLM
    print("\n" + "="*70)
    print("STARTING MEAL PLAN GENERATION WORKFLOW")
    print("🔒 Rate Limiting: Máximo 10 requisições/minuto (otimizado)")
    print("🤝 Delegação: Habilitada entre agentes")
    print("📝 Verbose: Otimizado para performance")
    print("="*70 + "\n")

    result = crew.kickoff()

    plan_json_raw = _safe_task_output(tasks[7])
    steps = {
        "personal_model": _safe_task_output(tasks[0]),
        "diabetic_analysis": _safe_task_output(tasks[1]),
        "causal_inference": _safe_task_output(tasks[2]),
        "retrieval": _safe_task_output(tasks[3]),
        "structured_prompt": _safe_task_output(tasks[4]),
        "meal_plan": _safe_task_output(tasks[5]),
        "judge_output": _safe_task_output(tasks[6]) or str(result),
        "final_plan": _safe_task_output(tasks[6]) or str(result),
        "plan_json_raw": plan_json_raw,
    }

    return {
        "final_plan": steps["final_plan"] or str(result),
        "plan_json": _parse_json_output(plan_json_raw),
        "steps": steps,
    }


if __name__ == "__main__":
    # Example usage
    print("🤖 Meal Planning RAG System with CrewAI")
    print(f"📦 Model: {gemini_model}\n")
    
    # Example user query
    example_query = {
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
        "inventory": ["arroz integral", "feijão preto", "frango", "legumes", "mamão"],
        "glucose_readings": [
            {"timestamp": "2026-01-10T08:00:00", "value_mg_dl": 135},
            {"timestamp": "2026-01-10T12:00:00", "value_mg_dl": 190},
            {"timestamp": "2026-01-10T18:00:00", "value_mg_dl": 160}
        ]
    }
    
    print("Generating meal plan for example user...")
    print("\nUser Profile:")
    print(f"  Goals: {example_query['goals']}")
    print(f"  Restrictions: {example_query['restrictions']}")
    print(f"  Region: {example_query['region']}\n")
    
    result = generate_meal_plan(example_query)
    
    print("\n" + "="*70)
    print("FINAL MEAL PLAN:")
    print("="*70)
    if isinstance(result, dict):
        print(result.get("final_plan", ""))
    else:
        print(result)

