"""
Serviço de Validação Nutricional
Valida macronutrientes e micronutrientes usando dados TACO/TBCA
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Caminho para os dados
DATA_DIR = Path(__file__).parent.parent / "data"
TACO_FILE = DATA_DIR / "taco_unified.jsonl"
TBCA_FILE = DATA_DIR / "tbca_unified.jsonl"


class NutritionValidationService:
    """Valida valores nutricionais contra recomendações e dados de referência"""
    
    def __init__(self):
        self._nutrition_db = None
        self._load_nutrition_database()
    
    def _load_nutrition_database(self):
        """Carrega base de dados nutricional em memória"""
        if self._nutrition_db is not None:
            return
        
        self._nutrition_db = {}
        
        # Carregar TACO
        if TACO_FILE.exists():
            try:
                with open(TACO_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        item = json.loads(line)
                        name = item.get('name_taco_descricao') or item.get('name_full', '')
                        if name:
                            self._nutrition_db[name.lower()] = item
            except Exception as e:
                print(f"Erro ao carregar TACO: {e}")
        
        # Carregar TBCA (se disponível)
        if TBCA_FILE.exists():
            try:
                with open(TBCA_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        item = json.loads(line)
                        name = item.get('name_full') or item.get('name_taco_descricao', '')
                        if name:
                            # TBCA tem prioridade se já existe TACO
                            if name.lower() not in self._nutrition_db:
                                self._nutrition_db[name.lower()] = item
            except Exception as e:
                print(f"Erro ao carregar TBCA: {e}")
        
        print(f"✅ Base nutricional carregada: {len(self._nutrition_db)} alimentos")
    
    def get_food_nutrients(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Busca nutrientes de um alimento na base de dados"""
        food_lower = food_name.lower()
        
        # Busca exata
        if food_lower in self._nutrition_db:
            return self._nutrition_db[food_lower].get('nutrients', {})
        
        # Busca parcial
        for key, item in self._nutrition_db.items():
            if food_lower in key or key in food_lower:
                return item.get('nutrients', {})
        
        return None
    
    def validate_macronutrients(
        self,
        carbs_g: Optional[float],
        protein_g: Optional[float],
        fat_g: Optional[float],
        fiber_g: Optional[float],
        target_calories: Optional[float] = None,
        diabetes_type: str = "Type 2"
    ) -> Dict[str, Any]:
        """
        Valida macronutrientes contra recomendações para diabetes tipo 2
        
        Recomendações para DM2:
        - Carboidratos: 45-60% das calorias (preferir complexos)
        - Proteínas: 15-20% das calorias
        - Gorduras: 20-35% das calorias (saturadas <10%)
        - Fibras: 25-30g/dia
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Calcular calorias se não fornecidas
        if target_calories is None:
            # Estimativa: 4 kcal/g carb, 4 kcal/g proteína, 9 kcal/g gordura
            estimated_calories = (
                (carbs_g or 0) * 4 +
                (protein_g or 0) * 4 +
                (fat_g or 0) * 9
            )
            target_calories = estimated_calories if estimated_calories > 0 else 2000
        
        total_macros = (carbs_g or 0) + (protein_g or 0) + (fat_g or 0)
        if total_macros == 0:
            validation["warnings"].append("Nenhum macronutriente fornecido")
            return validation
        
        # Validar carboidratos (45-60% das calorias)
        if carbs_g is not None:
            carbs_calories = carbs_g * 4
            carbs_percentage = (carbs_calories / target_calories * 100) if target_calories > 0 else 0
            
            if carbs_percentage < 45:
                validation["warnings"].append(
                    f"Carboidratos abaixo do recomendado ({carbs_percentage:.1f}% < 45%)"
                )
                validation["recommendations"].append(
                    f"Aumentar carboidratos para 45-60% das calorias ({target_calories * 0.45 / 4:.1f}-{target_calories * 0.60 / 4:.1f}g)"
                )
            elif carbs_percentage > 60:
                validation["warnings"].append(
                    f"Carboidratos acima do recomendado ({carbs_percentage:.1f}% > 60%)"
                )
                validation["recommendations"].append(
                    f"Reduzir carboidratos para 45-60% das calorias ({target_calories * 0.45 / 4:.1f}-{target_calories * 0.60 / 4:.1f}g)"
                )
        
        # Validar proteínas (15-20% das calorias)
        if protein_g is not None:
            protein_calories = protein_g * 4
            protein_percentage = (protein_calories / target_calories * 100) if target_calories > 0 else 0
            
            if protein_percentage < 15:
                validation["warnings"].append(
                    f"Proteínas abaixo do recomendado ({protein_percentage:.1f}% < 15%)"
                )
                validation["recommendations"].append(
                    f"Aumentar proteínas para 15-20% das calorias ({target_calories * 0.15 / 4:.1f}-{target_calories * 0.20 / 4:.1f}g)"
                )
            elif protein_percentage > 20:
                validation["warnings"].append(
                    f"Proteínas acima do recomendado ({protein_percentage:.1f}% > 20%)"
                )
        
        # Validar gorduras (20-35% das calorias)
        if fat_g is not None:
            fat_calories = fat_g * 9
            fat_percentage = (fat_calories / target_calories * 100) if target_calories > 0 else 0
            
            if fat_percentage < 20:
                validation["warnings"].append(
                    f"Gorduras abaixo do recomendado ({fat_percentage:.1f}% < 20%)"
                )
            elif fat_percentage > 35:
                validation["warnings"].append(
                    f"Gorduras acima do recomendado ({fat_percentage:.1f}% > 35%)"
                )
        
        # Validar fibras (25-30g/dia)
        if fiber_g is not None:
            if fiber_g < 25:
                validation["warnings"].append(
                    f"Fibras abaixo do recomendado ({fiber_g:.1f}g < 25g/dia)"
                )
                validation["recommendations"].append(
                    "Aumentar consumo de fibras (frutas, legumes, grãos integrais)"
                )
            elif fiber_g > 30:
                validation["warnings"].append(
                    f"Fibras muito altas ({fiber_g:.1f}g > 30g/dia) - pode causar desconforto"
                )
        
        validation["valid"] = len(validation["errors"]) == 0
        
        return validation
    
    def validate_micronutrients(
        self,
        nutrients: Dict[str, float],
        daily_requirements: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Valida micronutrientes contra recomendações diárias
        
        Recomendações diárias padrão (adultos):
        - Cálcio: 1000-1200 mg
        - Ferro: 8-18 mg (mulheres mais)
        - Sódio: <2300 mg
        - Magnésio: 310-420 mg
        - Potássio: 2600-3400 mg
        """
        if daily_requirements is None:
            daily_requirements = {
                "calcium_mg": 1000,
                "iron_mg": 15,
                "sodium_mg": 2300,  # Máximo
                "magnesium_mg": 400,
                "potassium_mg": 2600,
                "zinc_mg": 11,
                "vitamin_b1_mg": 1.2,
                "vitamin_b6_mg": 1.3,
            }
        
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Validar sódio (máximo 2300mg/dia)
        sodium = nutrients.get("sodium_mg") or nutrients.get("sodium")
        if sodium and sodium > daily_requirements["sodium_mg"]:
            validation["warnings"].append(
                f"Sódio acima do recomendado ({sodium:.1f}mg > {daily_requirements['sodium_mg']}mg)"
            )
            validation["recommendations"].append("Reduzir consumo de sódio")
        
        # Validar outros micronutrientes
        for nutrient, requirement in daily_requirements.items():
            if nutrient == "sodium_mg":
                continue  # Já validado
            
            value = nutrients.get(nutrient) or nutrients.get(nutrient.replace("_mg", ""))
            if value is not None and value > 0:
                # Para a maioria, verificar se está muito abaixo
                if value < requirement * 0.5:  # Menos de 50% da recomendação
                    validation["warnings"].append(
                        f"{nutrient.replace('_', ' ').title()} abaixo do recomendado "
                        f"({value:.1f} < {requirement:.1f})"
                    )
        
        validation["valid"] = len(validation["errors"]) == 0
        
        return validation
    
    def validate_meal_plan(self, meals: List[Dict[str, Any]], target_calories: float = 2000) -> Dict[str, Any]:
        """
        Valida um plano de refeições completo
        """
        total_carbs = 0
        total_protein = 0
        total_fat = 0
        total_fiber = 0
        total_nutrients = {}
        
        meal_validations = []
        
        for meal in meals:
            # Extrair macros do meal (pode estar em diferentes formatos)
            macros_str = meal.get("macros") or meal.get("macronutrients", "")
            meal_carbs = meal.get("carbohydrate_g") or meal.get("carbs_g") or 0
            meal_protein = meal.get("protein_g") or 0
            meal_fat = meal.get("fat_g") or meal.get("lipids_g") or 0
            meal_fiber = meal.get("fiber_g") or 0
            
            # Tentar extrair de string se disponível
            if isinstance(macros_str, str):
                # Formato: "Carbs: 30-40g, Proteína: 15g, Gordura: 8g"
                import re
                carbs_match = re.search(r'Carbs?[:\s]+(\d+(?:-\d+)?)', macros_str, re.I)
                protein_match = re.search(r'Prote[íi]na[:\s]+(\d+(?:-\d+)?)', macros_str, re.I)
                fat_match = re.search(r'Gordura[:\s]+(\d+(?:-\d+)?)', macros_str, re.I)
                
                if carbs_match and meal_carbs == 0:
                    meal_carbs = float(carbs_match.group(1).split('-')[0])
                if protein_match and meal_protein == 0:
                    meal_protein = float(protein_match.group(1).split('-')[0])
                if fat_match and meal_fat == 0:
                    meal_fat = float(fat_match.group(1).split('-')[0])
            
            total_carbs += meal_carbs
            total_protein += meal_protein
            total_fat += meal_fat
            total_fiber += meal_fiber
            
            # Validar refeição individual
            meal_validation = self.validate_macronutrients(
                meal_carbs, meal_protein, meal_fat, meal_fiber,
                target_calories / len(meals) if len(meals) > 0 else target_calories
            )
            meal_validations.append({
                "meal": meal.get("name") or meal.get("meal_type", "Refeição"),
                "validation": meal_validation
            })
        
        # Validar totais diários
        daily_validation = self.validate_macronutrients(
            total_carbs, total_protein, total_fat, total_fiber, target_calories
        )
        
        return {
            "daily_validation": daily_validation,
            "meal_validations": meal_validations,
            "totals": {
                "carbohydrates_g": total_carbs,
                "protein_g": total_protein,
                "fat_g": total_fat,
                "fiber_g": total_fiber,
                "estimated_calories": total_carbs * 4 + total_protein * 4 + total_fat * 9
            }
        }


if __name__ == "__main__":
    # Teste
    service = NutritionValidationService()
    
    # Testar validação
    validation = service.validate_macronutrients(
        carbs_g=150,
        protein_g=80,
        fat_g=60,
        fiber_g=20,
        target_calories=2000
    )
    print("Validação de macronutrientes:")
    print(json.dumps(validation, indent=2, ensure_ascii=False))






