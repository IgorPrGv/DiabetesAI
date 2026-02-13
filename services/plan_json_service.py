import os
import json
import re
from typing import Any, Dict, List
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from backend.llm_providers import get_llm

load_dotenv()


class PlanJsonService:
    def __init__(self):
        self._llm = self._init_llm()
        self._agent = Agent(
            role="Plan JSON Formatter",
            goal="Converter o plano final em JSON estrito para frontend e persistência.",
            backstory="Você produz apenas JSON válido seguindo o schema informado.",
            tools=[],
            verbose=True,
            allow_delegation=False,
            llm=self._llm,
            max_iter=2,
        )

    def _init_llm(self) -> LLM:
        return get_llm(provider=None, temperature=0.3)

    def format(self, final_plan: str, diabetic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Extract metrics from diabetic analysis
        metrics = diabetic_analysis.get("metrics", {})
        alerts = diabetic_analysis.get("alerts", [])
        
        task = Task(
            description=f"""Você é um formatador JSON especializado. Sua única tarefa é converter o plano de refeições abaixo em um objeto JSON válido.

**INSTRUÇÕES CRÍTICAS:**
1. Retorne APENAS o JSON, sem nenhum texto antes ou depois
2. Não use markdown, não use code blocks, não use explicações
3. O JSON deve ser válido e parseável
4. TODOS os campos do schema são OBRIGATÓRIOS
5. **IMPORTANTE**: Preserve a VARIEDADE do plano - NÃO duplique refeições entre dias diferentes

**VERIFICAÇÃO DE VARIEDADE:**
- Conte quantas vezes cada refeição aparece
- Se uma refeição aparecer mais de 3 vezes na semana, é um ERRO
- Cada tipo de refeição deve ter pelo menos 3 variações diferentes

**SCHEMA EXATO:**
{{
  "summary": {{
    "goal": "Objetivo do plano (ex: Controle glicêmico para DM2)",
    "region": "Região culinária (ex: Brasil/Nordeste)",
    "restrictions": ["lista de restrições"],
    "glycemic_metrics": {{
      "tir_pct": {metrics.get('tir_pct')},
      "tar_pct": {metrics.get('tar_pct')},
      "tbr_pct": {metrics.get('tbr_pct')}
    }},
    "alerts": {alerts},
    "meals_planned": 35,
    "glucose_checks": 21,
    "activities": 21
  }},
  "meals": [
    {{
      "day": "SEGUNDA-FEIRA",
      "meal_type": "Café da manhã",
      "name": "Nome ÚNICO da refeição",
      "description": "Descrição detalhada",
      "items": ["item1 (XXXg)", "item2 (XXXg)"],
      "food_items": [
        {{
          "name": "Nome do alimento",
          "portion": "100g",
          "macros": {{
            "calories": 150,
            "carbs_g": 20,
            "protein_g": 10,
            "fat_g": 5,
            "fiber_g": 3
          }},
          "glycemic_index": 55,
          "glycemic_load": 11
        }}
      ],
      "total_nutrition": {{
        "calories": 250,
        "carbs_g": 30,
        "protein_g": 15,
        "fat_g": 8,
        "fiber_g": 5
      }},
      "nutrition": "250 kcal, 30g carboidratos, 15g proteína",
      "time": "07:30",
      "time_interval": "07:00-08:00"
    }},
    {{
      "day": "TERÇA-FEIRA",
      "meal_type": "Café da manhã",
      "name": "Nome DIFERENTE da refeição de segunda",
      ...
    }}
  ],
  "timeline": [
    {{
      "day": "SEGUNDA-FEIRA",
      "time": "07:00",
      "time_display": "7:00 AM",
      "event_type": "Alert",
      "event_category": "Glucose Check",
      "label": "7:00 AM • Glicemia em Jejum",
      "description": "Medir glicemia antes do café",
      "color": "red",
      "level": "alert"
    }},
    {{
      "day": "SEGUNDA-FEIRA",
      "time": "07:30",
      "time_display": "7:30 AM",
      "event_type": "Meal",
      "event_category": "Breakfast",
      "meal_type": "Café da manhã",
      "label": "7:30 AM • Café da manhã",
      "description": "Descrição com alimentos e calorias",
      "color": "red",
      "level": "meal"
    }},
    {{
      "day": "SEGUNDA-FEIRA",
      "time": "08:30",
      "time_display": "8:30 AM",
      "event_type": "Activity",
      "event_category": "Exercise",
      "label": "8:30 AM • Caminhada Leve",
      "description": "30min após café",
      "color": "yellow",
      "level": "activity"
    }}
  ]
}}

**EXTRAÇÃO DO PLANO:**
Plano completo (primeiros 2000 caracteres):
{final_plan[:2000] if len(final_plan) > 2000 else final_plan}

**VALIDAÇÕES OBRIGATÓRIAS:**
1. 7 dias x 5 refeições = 35 meals total
2. Cada refeição deve ter "day", "meal_type", "name", "food_items" com macros
3. Timeline deve ter ~63 eventos (21 glucose checks + 21 atividades + 21 refeições por 7 dias)
4. NÃO repetir o mesmo "name" mais de 3 vezes
5. total_nutrition deve ser SOMA dos food_items.macros

DADOS DISPONÍVEIS:
- Métricas glicêmicas: {metrics}
- Alertas: {alerts}
- Plano final (texto): {final_plan[:1000] if len(final_plan) > 1000 else final_plan}

EXTRAIA do plano final:
- Pelo menos 3-4 refeições (café da manhã, almoço, lanche, jantar)
- Horários ESPECÍFICOS para cada refeição (ex: 07:30, 12:30, 15:30, 19:00)
- Intervalos de horário customizáveis (ex: "07:00-08:00" para café da manhã)
- Alertas de glicose com horários (ex: "7:00 AM • Glucose Check")
- Atividades recomendadas com horários (ex: "8:30 AM • Activity")
- Informações nutricionais detalhadas quando disponíveis
- Use cores: "red" para alertas e refeições, "yellow" para atividades e lanches

VALIDAÇÕES OBRIGATÓRIAS:
1. Porções SEMPRE em gramas (ex: "120g", "100g", "50g") - NÃO usar "1 fatia", "1 concha" sem converter para gramas
2. Calorias totais diárias: 1200-1800 kcal (validar soma de todas as refeições)
3. Cada alimento em food_items deve ter "portion" em formato "XXXg" (ex: "120g", "100g")
4. total_nutrition deve ser a SOMA dos macros de todos os food_items
5. NÃO incluir refeições duplicadas (mesmos alimentos nas mesmas quantidades)
6. Variar alimentos entre refeições e dias

RETORNE APENAS O JSON, SEM NADA MAIS.
""",
            agent=self._agent,
            expected_output="Um objeto JSON válido, sem texto adicional, seguindo exatamente o schema fornecido.",
        )

        crew = Crew(agents=[self._agent], tasks=[task], process=Process.sequential, verbose=True)
        output = crew.kickoff()
        text = str(output)
        
        # Debug: log first 500 chars of agent output
        print(f"[DEBUG] Agent output (first 500 chars): {text[:500]}")
        
        # Try to extract JSON from output
        parsed = self._parse_json(text)
        
        print(f"[DEBUG] Parsed result: {type(parsed)}, keys: {list(parsed.keys()) if parsed else 'empty'}")
        
        # Check if parsing was successful and has required structure
        # We need at least meals or days with actual content
        has_meals = parsed and (
            (parsed.get("meals") and len(parsed.get("meals", [])) > 0) or 
            (parsed.get("days") and len(parsed.get("days", [])) > 0)
        )
        
        # If parsing failed, returned empty dict, or incomplete structure, use fallback
        if not parsed or len(parsed) == 0 or not has_meals:
            # Create fallback structure from final_plan text
            parsed = self._create_fallback_structure(final_plan, diabetic_analysis)
        else:
            # Normalize existing structure
            parsed = self._normalize_structure(parsed)
            # Ensure alerts are populated from diabetic_analysis if missing
            if not parsed.get("summary", {}).get("alerts") and alerts:
                if "summary" not in parsed:
                    parsed["summary"] = {}
                parsed["summary"]["alerts"] = alerts if isinstance(alerts, list) else [alerts]
        
        # Final validation: ensure we always return a valid structure
        if not parsed or len(parsed) == 0:
            # Last resort: create minimal fallback
            parsed = self._create_fallback_structure(final_plan, diabetic_analysis)
        
        # Double-check: if still empty, force fallback
        if not parsed or len(parsed) == 0 or not parsed.get("summary") or not parsed.get("meals"):
            # Force fallback - something went wrong
            parsed = self._create_fallback_structure(final_plan, diabetic_analysis)
        
        # Ensure we have at least the basic structure
        if not parsed.get("summary"):
            parsed["summary"] = {}
        if not parsed.get("meals"):
            parsed["meals"] = []
        if not parsed.get("timeline"):
            parsed["timeline"] = []
        
        return parsed

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from agent output text"""
        # Try direct JSON parse first
        try:
            parsed = json.loads(text.strip())
            print(f"[DEBUG] Direct JSON parse successful")
            return self._normalize_structure(parsed)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in text (look for {...})
        # Use more aggressive regex to find JSON
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested objects
            r'\{.*?\}',  # Any object
            r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{.*?\})\s*```',  # JSON in code blocks without json tag
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                json_str = match if isinstance(match, str) else match.group(1) if hasattr(match, 'group') else match
                try:
                    parsed = json.loads(json_str)
                    print(f"[DEBUG] JSON found with pattern, length: {len(json_str)}")
                    return self._normalize_structure(parsed)
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, return empty dict
        print(f"[DEBUG] No valid JSON found in text")
        return {}
    
    def _validate_meal_variety(self, meals: List[Dict[str, Any]]) -> None:
        """Validate that meals have sufficient variety across the week"""
        from collections import Counter
        
        # Count meal name occurrences
        meal_names = [meal.get("name", "") for meal in meals]
        meal_counts = Counter(meal_names)
        
        # Check for excessive repetition
        duplicates = {name: count for name, count in meal_counts.items() if count > 3}
        
        if duplicates:
            print(f"⚠️  AVISO: Refeições duplicadas detectadas (>3x na semana):")
            for name, count in duplicates.items():
                print(f"   - '{name}': {count} vezes")
            print("   Recomendação: Gerar novo plano com mais variedade")
        
        # Count variations per meal type
        meal_types = {}
        for meal in meals:
            meal_type = meal.get("meal_type", "")
            meal_name = meal.get("name", "")
            if meal_type not in meal_types:
                meal_types[meal_type] = set()
            meal_types[meal_type].add(meal_name)
        
        # Check if each meal type has at least 3 variations
        for meal_type, variations in meal_types.items():
            if len(variations) < 3:
                print(f"⚠️  AVISO: {meal_type} tem apenas {len(variations)} variações (mínimo: 3)")
                print(f"   Variações: {', '.join(variations)}")
    
    def _normalize_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize plan JSON structure to match frontend expectations"""
        normalized = data.copy()
        
        # If we have "days" structure, convert to "meals" and "timeline"
        if "days" in normalized and isinstance(normalized["days"], list):
            meals = []
            timeline = []
            
            for day_data in normalized["days"]:
                day_name = day_data.get("day", "")
                day_meals = day_data.get("meals", [])
                
                for meal in day_meals:
                    # Convert meal structure to expected format
                    normalized_meal = {
                        "day": day_name,  # Add day field
                        "meal_type": meal.get("meal_type", meal.get("name", "Refeição")),
                        "name": meal.get("name", "Refeição"),
                        "description": meal.get("description", ""),
                        "items": meal.get("items", []),
                        "food_items": meal.get("food_items", []),  # Preserve food_items if present
                        "total_nutrition": meal.get("total_nutrition", None),  # Preserve total_nutrition if present
                        "nutrition": meal.get("nutrition", ""),
                        "glycemic_load": meal.get("glycemic_load", "low GL"),
                        "glycemic_class": meal.get("glycemic_class", "ok"),
                        "availability": meal.get("availability", "Verificar inventário"),
                        "macros": meal.get("nutrition", meal.get("macros", "")),
                        "time": meal.get("time", "08:00"),
                        "time_interval": meal.get("time_interval", None)
                    }
                    meals.append(normalized_meal)
                    
                    # Add to timeline with day
                    timeline.append({
                        "day": day_name,  # Add day field
                        "time": meal.get("time", "08:00"),
                        "time_display": meal.get("time", "08:00"),
                        "event_type": "Meal",
                        "event_category": meal.get("meal_type", "Meal"),
                        "meal_type": meal.get("meal_type", meal.get("name", "Refeição")),
                        "label": f"{meal.get('time', '08:00')} • {meal.get('name', 'Refeição')}",
                        "description": meal.get("description", ""),
                        "level": "meal",
                        "color": "red"
                    })
            
            normalized["meals"] = meals
            normalized["timeline"] = timeline
            
            # Validate meal variety
            self._validate_meal_variety(meals)
            
            # Keep days for reference but frontend uses meals/timeline
            # del normalized["days"]  # Optional: remove days if not needed
        
        # Ensure summary has required fields
        if "summary" not in normalized:
            normalized["summary"] = {}
        
        summary = normalized["summary"]
        
        # Ensure summary has required stats
        if "meals_planned" not in summary:
            summary["meals_planned"] = len(normalized.get("meals", []))
        
        if "glucose_checks" not in summary:
            summary["glucose_checks"] = 3  # Default recommendation
        
        if "activities" not in summary:
            summary["activities"] = 1  # Default recommendation
        
        # Ensure alerts is a list
        if "alerts" not in summary:
            summary["alerts"] = []
        elif not isinstance(summary["alerts"], list):
            summary["alerts"] = [summary["alerts"]]
        
        # Ensure meals and timeline are lists
        if "meals" not in normalized:
            normalized["meals"] = []
        if "timeline" not in normalized:
            normalized["timeline"] = []
        
        # Ensure all meals have food_items and total_nutrition (even if empty)
        # If food_items is missing but items exist, create food_items from items
        # Also validate and fix portions to be in grams
        total_daily_calories = 0
        for meal in normalized.get("meals", []):
            if "food_items" not in meal or not meal.get("food_items"):
                # If no food_items but has items, create empty food_items array
                # The frontend will load them via API
                meal["food_items"] = []
            
            # Validate and fix portions to be in grams
            for food_item in meal.get("food_items", []):
                portion = food_item.get("portion", "")
                # If portion doesn't end with 'g', try to convert common units
                if portion and not portion.endswith('g'):
                    # Try to extract number and convert
                    match = re.search(r'(\d+)', portion)
                    if match:
                        num = int(match.group(1))
                        # Common conversions (approximate)
                        if 'fatia' in portion.lower() or 'slice' in portion.lower():
                            food_item["portion"] = f"{num * 30}g"  # ~30g per slice
                        elif 'colher' in portion.lower() or 'spoon' in portion.lower():
                            food_item["portion"] = f"{num * 15}g"  # ~15g per spoon
                        elif 'concha' in portion.lower():
                            food_item["portion"] = f"{num * 100}g"  # ~100g per ladle
                        else:
                            food_item["portion"] = f"{num * 50}g"  # Default estimate
                    else:
                        food_item["portion"] = "100g"  # Default
            
            # Validate total_nutrition and calculate if missing
            if "total_nutrition" not in meal or not meal.get("total_nutrition"):
                # Calculate from food_items if available
                if meal.get("food_items"):
                    total = {"calories": 0, "carbs_g": 0, "protein_g": 0, "fat_g": 0, "fiber_g": 0}
                    for food_item in meal["food_items"]:
                        macros = food_item.get("macros", {})
                        if macros:
                            total["calories"] += macros.get("calories", 0)
                            total["carbs_g"] += macros.get("carbs_g", 0)
                            total["protein_g"] += macros.get("protein_g", 0)
                            total["fat_g"] += macros.get("fat_g", 0)
                            total["fiber_g"] += macros.get("fiber_g", 0)
                    meal["total_nutrition"] = total
                else:
                    meal["total_nutrition"] = None
            
            # Track daily calories
            if meal.get("total_nutrition") and meal["total_nutrition"].get("calories"):
                total_daily_calories += meal["total_nutrition"]["calories"]
        
        # Validate daily calories (should be 1200-1800 for DM2)
        if total_daily_calories > 0:
            if total_daily_calories < 1200:
                # Add warning to summary
                if "summary" in normalized:
                    if "alerts" not in normalized["summary"]:
                        normalized["summary"]["alerts"] = []
                    normalized["summary"]["alerts"].append(f"⚠️ Calorias diárias muito baixas ({total_daily_calories} kcal). Recomendado: 1200-1800 kcal.")
            elif total_daily_calories > 2000:
                if "summary" in normalized:
                    if "alerts" not in normalized["summary"]:
                        normalized["summary"]["alerts"] = []
                    normalized["summary"]["alerts"].append(f"⚠️ Calorias diárias muito altas ({total_daily_calories} kcal). Recomendado: 1200-1800 kcal.")
        
        return normalized
    
    def _create_fallback_structure(self, final_plan: str, diabetic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback JSON structure if agent fails to produce valid JSON"""
        metrics = diabetic_analysis.get("metrics", {})
        alerts = diabetic_analysis.get("alerts", [])
        
        # Extract basic info from final_plan text
        structure = {
            "summary": {
                "goal": "Controle glicêmico e nutricional personalizado",
                "region": "Brasil",
                "restrictions": [],
                "glycemic_metrics": {
                    "tir_pct": metrics.get("tir", None),
                    "tar_pct": metrics.get("tar", None),
                    "tbr_pct": metrics.get("tbr", None)
                },
                "alerts": alerts if isinstance(alerts, list) else [alerts] if alerts else [],
                "meals_planned": 4,  # Default: breakfast, lunch, snack, dinner
                "glucose_checks": 3,  # Default: before meals
                "activities": 1
            },
            "meals": [
                {
                    "meal_type": "Café da manhã",
                    "name": "Café da manhã balanceado",
                    "description": "Refeição matinal com carboidratos complexos e proteína",
                    "items": ["Pão integral (60g)", "Queijo branco (50g)", "Frutas (100g)"],
                    "food_items": [
                        {
                            "name": "Pão integral",
                            "portion": "60g",
                            "macros": {"calories": 150, "carbs_g": 30, "protein_g": 8, "fat_g": 2, "fiber_g": 4},
                            "glycemic_index": 55,
                            "glycemic_load": 11
                        },
                        {
                            "name": "Queijo branco",
                            "portion": "50g",
                            "macros": {"calories": 80, "carbs_g": 2, "protein_g": 12, "fat_g": 3, "fiber_g": 0},
                            "glycemic_index": None,
                            "glycemic_load": None
                        }
                    ],
                    "total_nutrition": {"calories": 280, "carbs_g": 35, "protein_g": 20, "fat_g": 8, "fiber_g": 5},
                    "nutrition": "250-300 kcal, 30-40g carbs, 15g proteína",
                    "glycemic_load": "low GL",
                    "glycemic_class": "ok",
                    "availability": "Verificar inventário",
                    "macros": "Carbs: 30-40g, Proteína: 15g, Gordura: 8g",
                    "time": "08:00",
                    "time_interval": "07:30-08:30"
                },
                {
                    "meal_type": "Almoço",
                    "name": "Almoço completo",
                    "description": "Refeição principal com proteína, vegetais e carboidrato controlado",
                    "items": ["Proteína magra (150g)", "Vegetais variados (200g)", "Arroz integral (100g)"],
                    "food_items": [
                        {
                            "name": "Frango",
                            "portion": "150g",
                            "macros": {"calories": 200, "carbs_g": 0, "protein_g": 30, "fat_g": 8, "fiber_g": 0},
                            "glycemic_index": None,
                            "glycemic_load": None
                        },
                        {
                            "name": "Arroz integral",
                            "portion": "100g",
                            "macros": {"calories": 120, "carbs_g": 25, "protein_g": 3, "fat_g": 1, "fiber_g": 2},
                            "glycemic_index": 50,
                            "glycemic_load": 12
                        }
                    ],
                    "total_nutrition": {"calories": 450, "carbs_g": 45, "protein_g": 35, "fat_g": 12, "fiber_g": 5},
                    "nutrition": "400-500 kcal, 40-50g carbs, 30g proteína",
                    "glycemic_load": "medium GL",
                    "glycemic_class": "ok",
                    "availability": "Verificar inventário",
                    "macros": "Carbs: 40-50g, Proteína: 30g, Gordura: 12g",
                    "time": "12:30",
                    "time_interval": "12:00-13:00"
                },
                {
                    "meal_type": "Lanche",
                    "name": "Lanche da tarde",
                    "description": "Lanche leve para manter glicemia estável",
                    "items": ["Frutas (100g)", "Oleaginosas (30g)"],
                    "food_items": [
                        {
                            "name": "Maçã",
                            "portion": "100g",
                            "macros": {"calories": 50, "carbs_g": 13, "protein_g": 0, "fat_g": 0, "fiber_g": 2},
                            "glycemic_index": 38,
                            "glycemic_load": 5
                        }
                    ],
                    "total_nutrition": {"calories": 180, "carbs_g": 18, "protein_g": 6, "fat_g": 12, "fiber_g": 3},
                    "nutrition": "150-200 kcal, 15-20g carbs, 5g proteína",
                    "glycemic_load": "low GL",
                    "glycemic_class": "ok",
                    "availability": "Verificar inventário",
                    "macros": "Carbs: 15-20g, Proteína: 5g, Gordura: 10g",
                    "time": "15:30",
                    "time_interval": "15:00-16:00"
                },
                {
                    "meal_type": "Jantar",
                    "name": "Jantar leve",
                    "description": "Jantar com foco em proteína e vegetais, carboidrato reduzido",
                    "items": ["Proteína magra (120g)", "Vegetais (150g)", "Salada (100g)"],
                    "food_items": [
                        {
                            "name": "Peixe",
                            "portion": "120g",
                            "macros": {"calories": 150, "carbs_g": 0, "protein_g": 25, "fat_g": 5, "fiber_g": 0},
                            "glycemic_index": None,
                            "glycemic_load": None
                        }
                    ],
                    "total_nutrition": {"calories": 320, "carbs_g": 25, "protein_g": 28, "fat_g": 10, "fiber_g": 4},
                    "nutrition": "300-400 kcal, 20-30g carbs, 25g proteína",
                    "glycemic_load": "low GL",
                    "glycemic_class": "ok",
                    "availability": "Verificar inventário",
                    "macros": "Carbs: 20-30g, Proteína: 25g, Gordura: 10g",
                    "time": "19:00",
                    "time_interval": "18:30-19:30"
                }
            ],
            "timeline": [
                {"time": "08:00", "event": "Café da manhã", "description": "Refeição matinal"},
                {"time": "07:45", "event": "Verificação de glicose", "description": "Medir glicemia antes do café"},
                {"time": "12:00", "event": "Almoço", "description": "Refeição principal"},
                {"time": "11:45", "event": "Verificação de glicose", "description": "Medir glicemia antes do almoço"},
                {"time": "15:30", "event": "Lanche", "description": "Lanche da tarde"},
                {"time": "19:00", "event": "Jantar", "description": "Jantar leve"},
                {"time": "18:45", "event": "Verificação de glicose", "description": "Medir glicemia antes do jantar"}
            ]
        }
        
        return structure


