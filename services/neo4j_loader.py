"""
Carregador de dados nutricionais para Neo4j
Cria grafo de conhecimento nutricional a partir dos dados TACO/TBCA
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from neo4j_client import Neo4jClient

DATA_DIR = Path(__file__).parent.parent / "data"
TACO_FILE = DATA_DIR / "taco_unified.jsonl"
TBCA_FILE = DATA_DIR / "tbca_unified.jsonl"


def load_nutrition_data_to_neo4j(
    neo4j_client: Optional[Neo4jClient] = None,
    limit: Optional[int] = None,
    force_reload: bool = False
) -> int:
    """
    Carrega dados nutricionais TACO/TBCA no Neo4j
    
    Estrutura do grafo:
    - (Food) -[:HAS_NUTRIENT {value}]-> (Nutrient)
    - (Food) -[:SIMILAR_TO {similarity}]-> (Food)
    - (Food) -[:BELONGS_TO]-> (FoodGroup)
    """
    if not neo4j_client:
        neo4j_client = Neo4jClient.from_env()
        if not neo4j_client:
            print("⚠️  Neo4j não configurado. Pulando carregamento.")
            return 0
    
    count = 0
    
    # Carregar TACO
    if TACO_FILE.exists():
        print(f"Carregando dados TACO em Neo4j...")
        try:
            with open(TACO_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if limit and count >= limit:
                        break
                    
                    item = json.loads(line)
                    name = item.get('name_taco_descricao') or item.get('name_full', '')
                    if not name:
                        continue
                    
                    nutrients = item.get('nutrients', {})
                    group = item.get('group') or 'Outros'
                    
                    # Carregar alimento no Neo4j
                    neo4j_client.upsert_food(
                        name=name,
                        group=group,
                        nutrients=nutrients,
                        source='taco'
                    )
                    
                    count += 1
                    if count % 100 == 0:
                        print(f"  Carregados {count} alimentos...")
        except Exception as e:
            print(f"Erro ao carregar TACO: {e}")
    
    # Carregar TBCA (limitado para não sobrecarregar)
    if TBCA_FILE.exists() and (not limit or count < limit):
        print(f"Carregando dados TBCA em Neo4j...")
        try:
            tbca_limit = (limit - count) if limit else 500  # Limitar TBCA
            with open(TBCA_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if count >= (limit or float('inf')):
                        break
                    if tbca_limit <= 0:
                        break
                    
                    item = json.loads(line)
                    name = item.get('name_full') or item.get('name_taco_descricao', '')
                    if not name:
                        continue
                    
                    nutrients = item.get('nutrients', {})
                    group = item.get('group') or 'Outros'
                    
                    neo4j_client.upsert_food(
                        name=name,
                        group=group,
                        nutrients=nutrients,
                        source='tbca'
                    )
                    
                    count += 1
                    tbca_limit -= 1
                    if count % 100 == 0:
                        print(f"  Carregados {count} alimentos...")
        except Exception as e:
            print(f"Erro ao carregar TBCA: {e}")
    
    print(f"✅ {count} alimentos carregados no Neo4j")
    return count


if __name__ == "__main__":
    # Teste de carregamento
    client = Neo4jClient.from_env()
    if client:
        load_nutrition_data_to_neo4j(client, limit=100)
        client.close()
    else:
        print("Neo4j não configurado. Configure NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")

