# DiabetesAI Care - Sistema Inteligente de Planejamento Alimentar

Sistema colaborativo de agentes IA especializados em planejamento alimentar personalizado para gestão de Diabetes Tipo 2 e hipertensão.

## 🎯 Visão Geral

O DiabetesAI Care utiliza múltiplos agentes especializados trabalhando em conjunto através de uma arquitetura RAG (Retrieval-Augmented Generation):

### 🤖 Agentes Principais

| Agente | Especialização | Função |
|--------|----------------|--------|
| **Nutrition Agent** | Planejamento nutricional | Gera planos alimentares personalizados |
| **Diabetic Agent** | Controle glicêmico | Calcula TIR/TAR/TBR e alertas |
| **Judge Agent** | Coordenação | Resolve conflitos e valida planos |
| **Causal Inference** | Padrões | Analisa relações causa-efeito |
| **Chat Agent** | Conversação | Assistente nutricional com RAG |

### 🏗️ Arquitetura

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: AngularJS 1.x responsivo
- **IA**: CrewAI + LangChain + Gemini API
- **Banco**: PostgreSQL (produção) / SQLite (desenvolvimento)

## 📋 Pré-requisitos

- **Python 3.8+** com virtualenv
- **PostgreSQL 13+** (recomendado) ou SQLite
- **Node.js** (para desenvolvimento frontend)
- **Gemini API Key** (Google AI Studio)

## 🚀 Instalação Rápida

### 1. Clonagem e Dependências

```bash
# Clonar repositório
git clone <repository-url>
cd diabetes-ai-care

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração da API Key

```bash
# Obter chave no Google AI Studio
# https://makersuite.google.com/app/apikey

# Configurar variável
export GEMINI_API_KEY="sua-chave-aqui"
```

### 3. Banco de Dados

```bash
# PostgreSQL (recomendado)
./scripts/setup_postgresql_complete.sh

# Ou SQLite (desenvolvimento)
# Banco será criado automaticamente
```

### 4. Executar Sistema

```bash
# Setup completo
./scripts/setup.sh

# Iniciar servidor
./scripts/start_server.sh

# Acessar: http://localhost:8080
```

## 📁 Estrutura do Projeto

```
diabetes-ai-care/
├── 📄 README.md                    # Este arquivo
├── 🔧 scripts/                     # Scripts de automação
│   ├── 📄 README.md               # Documentação scripts
│   ├── start_server.sh           # Iniciar servidor
│   ├── setup_postgresql_complete.sh # Setup PostgreSQL
│   └── ...
├── 🤖 services/                    # Serviços de IA
│   ├── 📄 README.md               # Documentação agentes
│   ├── nutrition_service.py       # Agente nutricional
│   ├── diabetic_service.py        # Agente diabético
│   ├── judge_service.py          # Agente juiz
│   └── ...
├── 🎨 frontend/                    # Interface web
│   ├── 📄 README.md               # Documentação frontend
│   ├── home.html                  # Dashboard principal
│   ├── login.html                 # Autenticação
│   └── ...
├── 🧪 tests/                       # Testes automatizados
│   ├── 📄 README.md               # Documentação testes
│   ├── test_api.py               # Testes API
│   ├── test_services.py          # Testes agentes
│   └── ...
├── 💾 data/                        # Bases de dados
│   ├── 📄 README.md               # Documentação dados
│   ├── diabetesai.db             # Banco SQLite
│   ├── taco_unified.jsonl        # Base TACO
│   └── ...
├── 💻 backend/                     # Backend da aplicação
│   ├── 📄 __init__.py             # Pacote backend
│   ├── 📊 api.py                  # API FastAPI principal
│   ├── 🔄 storage.py              # Camada de persistência
│   ├── 🤖 meal_plan_rag.py       # Sistema RAG principal
│   ├── 🧠 llm_providers.py       # Provedores de LLM
│   ├── ⚡ llm_with_rate_limit.py  # LLM com rate limiting
│   ├── 🔍 rag_system.py          # Sistema RAG
│   ├── 🛡️ rate_limiter.py        # Rate limiter
│   └── 🕸️ neo4j_client.py       # Cliente Neo4j
└── 📋 requirements.txt            # Dependências Python
```

### 📖 Documentação Detalhada

- **[`backend/README.md`](backend/README.md)** - Documentação completa do backend
- **[`services/README.md`](services/README.md)** - Documentação completa dos agentes IA
- **[`scripts/README.md`](scripts/README.md)** - Scripts de automação e setup
- **[`frontend/README.md`](frontend/README.md)** - Interface web e componentes
- **[`tests/README.md`](tests/README.md)** - Testes e cobertura
- **[`data/README.md`](data/README.md)** - Bases nutricionais e backups

## ✨ Funcionalidades Principais

### 👤 Gestão de Usuários
- ✅ **Cadastro e autenticação** OAuth2
- ✅ **Perfis personalizados** (métricas de saúde, preferências)
- ✅ **Histórico médico** completo

### 🤖 Planejamento Alimentar Inteligente
- ✅ **Planos personalizados** baseados em perfil individual
- ✅ **5 agentes especializados** trabalhando em conjunto
- ✅ **Controle de restrições** (alergias, preferências, religião)

### 📊 Monitoramento Glicêmico
- ✅ **Cálculo TIR/TAR/TBR** em tempo real
- ✅ **Alertas inteligentes** de hipoglicemia/hiperglicemia
- ✅ **Timeline interativo** com lembretes

### 💬 Assistente Nutricional
- ✅ **Chat conversacional** com IA
- ✅ **Sistema RAG** para respostas precisas
- ✅ **Voz sintetizada** (acessibilidade)

### 📱 Interface Acessível
- ✅ **Design responsivo** (mobile-first)
- ✅ **Cores semânticas** e alto contraste
- ✅ **Fonte ampliada** e navegação por teclado
- ✅ **Leitura em voz alta**

## 🛠️ Desenvolvimento

### Executar Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python -m pytest tests/test_api.py -k "test_health"

# Com coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Debug e Logs

```bash
# Ver logs em tempo real
tail -f logs/server.log

# Debug API
curl -X GET "http://localhost:8000/health"

# Debug agentes
python -c "from services.nutrition_service import NutritionService; svc = NutritionService(); print('OK')"
```

## 🤝 Contribuição

### Processo de Desenvolvimento

1. **Fork** o repositório
2. **Criar branch** para feature: `git checkout -b feature/nova-funcionalidade`
3. **Commit** mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. **Push** para branch: `git push origin feature/nova-funcionalidade`
5. **Pull Request** com descrição detalhada

### Padrões de Código

- **Python**: PEP 8, type hints obrigatórios
- **JavaScript**: ESLint, JSDoc para funções
- **Commits**: Conventional commits
- **Testes**: Mínimo 80% cobertura

## 📄 Licença

Este projeto está sob a licença MIT. Ver [`LICENSE`](LICENSE) para detalhes.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/username/diabetes-ai-care/issues)
- **Documentação**: Ver READMEs das subpastas
- **Wiki**: Em desenvolvimento

---

## 🎯 Roadmap

### Próximas Features
- [ ] **Aplicativo mobile** (React Native)
- [ ] **Integração wearables** (Apple Watch, Fitbit)
- [ ] **Análise preditiva** avançada
- [ ] **Suporte multi-idiomas**
- [ ] **Dashboard médico** para profissionais

### Melhorias Técnicas
- [ ] **API GraphQL** para consultas complexas
- [ ] **Cache Redis** para performance
- [ ] **Containerização** completa (Docker)
- [ ] **CI/CD** automatizado
- [ ] **Monitoramento** com Prometheus

#### Rollback to SQLite (if needed)

```bash
python rollback_to_sqlite.py
```

### 4. Test the RAG System

```bash
python test_rag_system.py
```

This will load nutritional data into the vector database (first run takes a few minutes).

### 5. Generate Meal Plans

```bash
python meal_plan_rag.py
```

For detailed instructions, see `QUICK_START.md` or `MEAL_PLAN_RAG_README.md`.

## Using the System Programmatically

```python
from meal_plan_rag import generate_meal_plan

user_query = {
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
    "region": "Sudeste brasileiro"
}

result = generate_meal_plan(user_query)
print(result)
```

## Project Structure

```
topicos/
├── api.py                   # REST API (FastAPI)
├── meal_plan_rag.py         # Main system - Meal planning RAG with collaborative agents
├── rag_system.py            # RAG infrastructure (vector DB, embeddings, retrieval)
├── test_rag_system.py       # Test script for RAG system
├── test_meal_plan_simple.py # Simple test script
├── API_README.md            # REST API documentation
├── OLLAMA_SETUP.md          # Ollama setup guide
├── TROUBLESHOOTING.md       # Troubleshooting guide
├── requirements.txt         # Python dependencies
├── setup.sh                 # Setup script (optional)
├── example_request.json     # Example API request
├── data/                    # Nutritional databases (TACO, TBCA)
├── chroma_db/               # Vector database (created automatically)
└── README.md                # This file
```

## Features

- **Vector Database**: Semantic search over 6,890+ nutritional items using ChromaDB
- **Multilingual Support**: Works with Portuguese and English queries
- **Type 2 Diabetes Focus**: Built-in considerations for diabetes management
- **Regional Preferences**: Supports regional/cultural food preferences
- **Collaborative Agents**: 5 specialized agents working together
- **Local LLM**: Uses Ollama for free, private, local processing

## Documentation

- **`QUICK_START.md`** - Quick start guide
- **`MEAL_PLAN_RAG_README.md`** - Comprehensive documentation
- **`OLLAMA_SETUP.md`** - Detailed Ollama setup instructions
- **`TROUBLESHOOTING.md`** - Common issues and solutions

## REST API

The system includes a REST API built with FastAPI:

```bash
# Start the API server
python api.py
```

The API will be available at `http://localhost:8000`

**Endpoints:**
- `POST /meal-plan/generate` - Generate a personalized meal plan
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)

See `API_README.md` for detailed API documentation and examples.

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewAI)
- [Ollama Official Site](https://ollama.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

This is a project template. Modify as needed for your use case.
