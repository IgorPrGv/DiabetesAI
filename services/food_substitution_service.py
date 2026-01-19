"""
Serviço de Substituições de Alimentos
Encontra substituições nutricionalmente equivalentes usando grafo de conhecimento
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import math

# Caminho para os dados
DATA_DIR = Path(__file__).parent.parent / "data"
TACO_FILE = DATA_DIR / "taco_unified.jsonl"
TBCA_FILE = DATA_DIR / "tbca_unified.jsonl"


class FoodSubstitutionService:
    """Encontra substituições nutricionais usando dados TACO/TBCA"""
    
    def __init__(self):
        self._nutrition_db = None
        self._food_index = {}  # Índice para busca rápida
        self._load_nutrition_database()
    
    def _load_nutrition_database(self):
        """Carrega base de dados nutricional"""
        if self._nutrition_db is not None:
            return
        
        self._nutrition_db = {}
        self._food_index = {}
        
        # Carregar TACO
        if TACO_FILE.exists():
            try:
                with open(TACO_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        item = json.loads(line)
                        name = item.get('name_taco_descricao') or item.get('name_full', '')
                        if name:
                            self._nutrition_db[name.lower()] = item
                            # Indexar palavras-chave
                            words = name.lower().split()
                            for word in words:
                                if len(word) > 2:  # Ignorar palavras muito curtas
                                    if word not in self._food_index:
                                        self._food_index[word] = []
                                    self._food_index[word].append(name.lower())
            except Exception as e:
                print(f"Erro ao carregar TACO: {e}")
        
        # Carregar TBCA
        if TBCA_FILE.exists():
            try:
                with open(TBCA_FILE, 'r', encoding='utf-8') as f:
                    count = 0
                    for line in f:
                        if count >= 1000:  # Limitar para não sobrecarregar memória
                            break
                        item = json.loads(line)
                        name = item.get('name_full') or item.get('name_taco_descricao', '')
                        if name and name.lower() not in self._nutrition_db:
                            self._nutrition_db[name.lower()] = item
                            words = name.lower().split()
                            for word in words:
                                if len(word) > 2:
                                    if word not in self._food_index:
                                        self._food_index[word] = []
                                    self._food_index[word].append(name.lower())
                        count += 1
            except Exception as e:
                print(f"Erro ao carregar TBCA: {e}")
        
        print(f"✅ Base de substituições carregada: {len(self._nutrition_db)} alimentos")
    
    def _extract_nutrients(self, food_item: Dict[str, Any]) -> Dict[str, float]:
        """Extrai nutrientes principais de um alimento"""
        nutrients = food_item.get('nutrients', {})
        
        return {
            "carbohydrate_g": nutrients.get("carbohydrate_total_g") or 0,
            "protein_g": nutrients.get("protein_total_g") or 0,
            "fat_g": nutrients.get("lipids_total_g") or 0,
            "fiber_g": nutrients.get("fiber_g") or 0,
            "calcium_mg": nutrients.get("calcium_mg") or 0,
            "iron_mg": nutrients.get("iron_mg") or 0,
            "sodium_mg": nutrients.get("sodium_mg") or 0,
            "magnesium_mg": nutrients.get("magnesium_mg") or 0,
            "potassium_mg": nutrients.get("potassium_mg") or 0,
        }
    
    def _calculate_nutritional_similarity(
        self,
        nutrients1: Dict[str, float],
        nutrients2: Dict[str, float]
    ) -> float:
        """
        Calcula similaridade nutricional entre dois alimentos (0-1)
        Usa distância euclidiana normalizada
        """
        # Peso dos macronutrientes (mais importante)
        macro_weights = {
            "carbohydrate_g": 0.3,
            "protein_g": 0.3,
            "fat_g": 0.2,
            "fiber_g": 0.2,
        }
        
        # Peso dos micronutrientes (menos importante)
        micro_weights = {
            "calcium_mg": 0.05,
            "iron_mg": 0.05,
            "sodium_mg": 0.05,
            "magnesium_mg": 0.05,
            "potassium_mg": 0.05,
        }
        
        total_diff = 0
        total_weight = 0
        
        # Comparar macronutrientes
        for nutrient, weight in macro_weights.items():
            val1 = nutrients1.get(nutrient, 0)
            val2 = nutrients2.get(nutrient, 0)
            
            # Normalizar (assumindo valores típicos)
            max_val = 100 if "g" in nutrient else 1000
            diff = abs(val1 - val2) / max_val if max_val > 0 else 0
            total_diff += diff * weight
            total_weight += weight
        
        # Comparar micronutrientes (normalizados)
        for nutrient, weight in micro_weights.items():
            val1 = nutrients1.get(nutrient, 0)
            val2 = nutrients2.get(nutrient, 0)
            
            # Normalizar (valores em mg variam muito)
            max_val = 1000  # Aproximação
            diff = abs(val1 - val2) / max_val if max_val > 0 else 0
            total_diff += diff * weight
            total_weight += weight
        
        # Similaridade = 1 - diferença normalizada
        similarity = 1 - (total_diff / total_weight if total_weight > 0 else 0)
        return max(0, min(1, similarity))
    
    def find_substitutions(
        self,
        food_name: str,
        max_results: int = 5,
        min_similarity: float = 0.6,
        restrictions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Encontra substituições para um alimento
        
        Args:
            food_name: Nome do alimento a substituir
            max_results: Número máximo de substituições
            min_similarity: Similaridade mínima (0-1)
            restrictions: Lista de restrições (ex: ["sem glúten", "baixo sódio"])
        """
        # Buscar alimento original
        original_food = None
        food_lower = food_name.lower().strip()
        
        # Normalizar nome (remover acentos, espaços extras)
        import unicodedata
        food_normalized = unicodedata.normalize('NFKD', food_lower)
        food_normalized = ''.join(c for c in food_normalized if not unicodedata.combining(c))
        
        # Busca exata
        if food_lower in self._nutrition_db:
            original_food = self._nutrition_db[food_lower]
        elif food_normalized in self._nutrition_db:
            original_food = self._nutrition_db[food_normalized]
        else:
            # Busca parcial (mais flexível)
            best_match = None
            best_score = 0
            
            # Extrair palavras-chave principais (remover palavras comuns)
            common_words = {'cozido', 'cru', 'frito', 'grelhado', 'assado', 'integral', 'branco', 'preto', 'verde', 'cozida', 'frita', 'grelhada'}
            keywords = [w for w in food_lower.split() if len(w) > 2 and w not in common_words]
            
            # Se não encontrou palavras-chave, usar todas as palavras
            if not keywords:
                keywords = [w for w in food_lower.split() if len(w) > 2]
            
            for key, item in self._nutrition_db.items():
                key_normalized = unicodedata.normalize('NFKD', key)
                key_normalized = ''.join(c for c in key_normalized if not unicodedata.combining(c))
                
                # Calcular score de similaridade (mais tolerante)
                score = 0
                matched_keywords = 0
                
                for keyword in keywords:
                    # Busca mais flexível: verifica se a palavra está contida
                    if keyword in key or keyword in key_normalized:
                        matched_keywords += 1
                        # Dar mais peso se a palavra está no início
                        if key.startswith(keyword) or key_normalized.startswith(keyword):
                            score += 2.0
                        else:
                            score += 1.0
                
                # Também verificar se palavras-chave principais estão presentes
                if matched_keywords > 0:
                    # Normalizar pelo número de palavras-chave
                    score = score / max(len(keywords), 1)
                    # Bônus se todas as palavras-chave principais foram encontradas
                    if matched_keywords == len(keywords):
                        score *= 1.5
                    
                    if score > best_score:
                        best_score = score
                        best_match = item
            
            # Threshold mais baixo para encontrar mais alimentos
            if best_match and best_score > 0.2:  # Threshold reduzido de 0.3 para 0.2
                original_food = best_match
            elif not original_food:
                # Última tentativa: buscar por qualquer palavra-chave
                for keyword in keywords:
                    if keyword in self._food_index:
                        for candidate_name in self._food_index[keyword][:10]:  # Limitar a 10 candidatos
                            if candidate_name in self._nutrition_db:
                                original_food = self._nutrition_db[candidate_name]
                                break
                    if original_food:
                        break
        
        if not original_food:
            return []
        
        original_nutrients = self._extract_nutrients(original_food)
        
        # Buscar alimentos similares
        candidates = []
        
        # Buscar por palavras-chave do alimento original
        search_terms = [w for w in food_lower.split() if len(w) > 2]
        candidate_names = set()
        
        for term in search_terms:
            if term in self._food_index:
                candidate_names.update(self._food_index[term])
        
        # Se não encontrou muitos, buscar por similaridade de nome
        if len(candidate_names) < 10:
            # Buscar alimentos que compartilham palavras-chave
            for key in self._nutrition_db.keys():
                key_words = set(key.split())
                food_words = set(search_terms)
                # Se compartilha pelo menos uma palavra relevante
                if key_words.intersection(food_words):
                    candidate_names.add(key)
        
        # Se ainda não encontrou, buscar todos (limitado para performance)
        if len(candidate_names) < 5:
            # Limitar busca a 500 candidatos aleatórios para performance
            import random
            all_keys = list(self._nutrition_db.keys())
            candidate_names = set(random.sample(all_keys, min(500, len(all_keys))))
        
        # Calcular similaridade para cada candidato
        for candidate_name in candidate_names:
            if candidate_name == food_lower:
                continue  # Pular o próprio alimento
            
            candidate_item = self._nutrition_db[candidate_name]
            candidate_nutrients = self._extract_nutrients(candidate_item)
            
            similarity = self._calculate_nutritional_similarity(
                original_nutrients,
                candidate_nutrients
            )
            
            if similarity >= min_similarity:
                # Verificar restrições
                if restrictions:
                    candidate_desc = candidate_name.lower()
                    skip = False
                    for restriction in restrictions:
                        restriction_lower = restriction.lower()
                        # Lógica simples de verificação
                        if "sem glúten" in restriction_lower and "trigo" in candidate_desc:
                            skip = True
                            break
                        if "baixo sódio" in restriction_lower:
                            if candidate_nutrients.get("sodium_mg", 0) > 200:
                                skip = True
                                break
                    if skip:
                        continue
                
                candidates.append({
                    "name": candidate_item.get('name_taco_descricao') or candidate_name,
                    "similarity": similarity,
                    "nutrients": candidate_nutrients,
                    "source": candidate_item.get('source', 'taco')
                })
        
        # Ordenar por similaridade
        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        
        return candidates[:max_results]
    
    def suggest_substitutions_for_meal(
        self,
        meal: Dict[str, Any],
        restrictions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sugere substituições para uma refeição completa
        """
        meal_name = meal.get("name") or meal.get("title", "")
        meal_items = meal.get("items", [])
        
        substitutions = {
            "meal": meal_name,
            "substitutions": []
        }
        
        # Se a refeição tem itens listados, sugerir para cada item
        if meal_items:
            for item in meal_items:
                if isinstance(item, str):
                    # Tentar extrair nome do alimento
                    item_name = item.split(',')[0].strip()  # Primeiro item antes da vírgula
                    subs = self.find_substitutions(
                        item_name,
                        max_results=3,
                        restrictions=restrictions
                    )
                    if subs:
                        substitutions["substitutions"].append({
                            "original": item,
                            "alternatives": subs
                        })
        else:
            # Se não tem itens, tentar substituir a refeição inteira
            subs = self.find_substitutions(
                meal_name,
                max_results=5,
                restrictions=restrictions
            )
            if subs:
                substitutions["substitutions"] = [{
                    "original": meal_name,
                    "alternatives": subs
                }]
        
        return substitutions
    
    def get_food_nutritional_info(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Retorna informações nutricionais completas de um alimento"""
        food_lower = food_name.lower()
        
        if food_lower in self._nutrition_db:
            item = self._nutrition_db[food_lower]
            nutrients = self._extract_nutrients(item)
            
            return {
                "name": item.get('name_taco_descricao') or food_name,
                "nutrients": nutrients,
                "full_nutrients": item.get('nutrients', {}),
                "source": item.get('source', 'taco')
            }
        
        # Busca parcial
        for key, item in self._nutrition_db.items():
            if food_lower in key or key in food_lower:
                nutrients = self._extract_nutrients(item)
                return {
                    "name": item.get('name_taco_descricao') or key,
                    "nutrients": nutrients,
                    "full_nutrients": item.get('nutrients', {}),
                    "source": item.get('source', 'taco')
                }
        
        return None


if __name__ == "__main__":
    # Teste
    service = FoodSubstitutionService()
    
    # Testar substituições
    subs = service.find_substitutions("arroz integral cozido", max_results=5)
    print("Substituições para 'arroz integral cozido':")
    for sub in subs:
        print(f"  - {sub['name']} (similaridade: {sub['similarity']:.2f})")

