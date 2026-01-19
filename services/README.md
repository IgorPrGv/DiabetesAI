# Services - DiabetesAI Core Services

Este diretório contém todos os serviços de IA especializados para o sistema DiabetesAI Care.

## 📋 Visão Geral dos Serviços

### 🤖 Serviços de IA (Agents)

| Serviço | Descrição | Arquivos |
|---------|-----------|----------|
| **Nutrition Agent** | Gera planos alimentares personalizados baseados em perfil do usuário, restrições e inventário | `nutrition_service.py`, `nutrition_api.py` |
| **Diabetic Agent** | Processa dados glicêmicos, calcula métricas TIR/TAR/TBR e gera alertas | `diabetic_service.py`, `diabetic_api.py` |
| **Judge Agent** | Coordena agentes, resolve conflitos e valida planos finais | `judge_service.py`, `judge_api.py` |
| **Causal Inference** | Analisa padrões causais entre refeições e controle glicêmico | `causal_service.py`, `causal_api.py` |
| **Chat Service** | Interface conversacional com RAG para consultas nutricionais | `chat_service.py` |
| **Food Substitution** | Encontra substituições nutricionalmente equivalentes | `food_substitution_service.py` |

### 🔧 Serviços de Infraestrutura

| Serviço | Descrição | Arquivos |
|---------|-----------|----------|
| **Gateway** | Ponto de entrada unificado para todos os agentes | `gateway_service.py` |
| **Nutrition Validation** | Valida macronutrientes e micronutrientes dos planos | `nutrition_validation_service.py` |
| **Plan JSON** | Estrutura e validação de dados dos planos gerados | `plan_json_service.py` |
| **Neo4j Loader** | Carrega dados para o grafo de conhecimento nutricional | `neo4j_loader.py` |

## 🚀 Como Usar

### Inicialização dos Serviços

```python
from services.nutrition_service import NutritionService
from services.diabetic_service import DiabeticService

# Inicializar agentes
nutrition_agent = NutritionService()
diabetic_agent = DiabeticService()

# Usar via Gateway (recomendado)
from services.gateway_service import GatewayService
gateway = GatewayService()
result = gateway.generate_meal_plan(user_profile)
```

### Dependências

- **CrewAI**: Framework para orquestração de agentes colaborativos
- **LangChain**: Integração com modelos de linguagem
- **Neo4j**: Banco de grafos para conhecimento nutricional
- **Pandas/Scikit-learn**: Análise de dados e causalidade

## 📊 Arquitetura

```
Gateway Service
├── Nutrition Agent ── Validation Service
├── Diabetic Agent ── TIR/TAR/TBR Calculator
├── Judge Agent ────── Conflict Resolution
├── Causal Agent ──── Pattern Analysis
└── Chat Service ──── RAG System
```

## 🔍 Debugging

Cada serviço possui logs detalhados. Para debug:

```bash
# Ver logs de um serviço específico
tail -f logs/nutrition_service.log

# Testar serviço isoladamente
python -c "from services.nutrition_service import NutritionService; svc = NutritionService(); print(svc.validate_plan(test_plan))"
```

## 📝 Notas Técnicas

- Todos os serviços seguem o padrão de arquitetura em microserviços
- Comunicação via FastAPI com validação Pydantic
- Cache Redis para performance (opcional)
- Rate limiting integrado para chamadas LLM

