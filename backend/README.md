# Backend - Core da API DiabetesAI Care

Este diretório contém todos os componentes principais do backend da aplicação DiabetesAI Care.

## 📋 Visão Geral dos Componentes

### 🖥️ API Principal

| Componente | Descrição | Arquivo |
|------------|-----------|---------|
| **FastAPI App** | API REST principal com endpoints para usuários, planos e chat | `api.py` |
| **Storage Layer** | Camada de persistência com suporte a SQLite/PostgreSQL | `storage.py` |
| **RAG System** | Sistema de Retrieval-Augmented Generation para planos nutricionais | `meal_plan_rag.py` |

### 🤖 Inteligência Artificial

| Componente | Descrição | Arquivo |
|------------|-----------|---------|
| **LLM Providers** | Interface unificada para múltiplos provedores de LLM (Gemini, OpenAI, etc.) | `llm_providers.py` |
| **Rate Limiter** | Controle de taxa de requisições para APIs de LLM | `llm_with_rate_limit.py` |
| **RAG Core** | Sistema de recuperação e geração aumentada | `rag_system.py` |
| **Rate Limiter** | Implementação de rate limiting | `rate_limiter.py` |

### 🔗 Integrações Externas

| Componente | Descrição | Arquivo |
|------------|-----------|---------|
| **Neo4j Client** | Cliente para integração com grafo de conhecimento nutricional | `neo4j_client.py` |

## 🚀 Como Usar

### Inicialização da API

```bash
# Executar API diretamente
python -m backend.api

# Ou via uvicorn
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload

# Ou via script
./scripts/start_server.sh
```

### Uso Programático

```python
# Importar componentes
from backend.api import app
from backend.storage import init_db, create_user
from backend.meal_plan_rag import generate_meal_plan

# Inicializar banco
init_db()

# Criar usuário
user_id = create_user({
    "full_name": "João Silva",
    "health_metrics": {"diabetes_type": "Type 2"}
})

# Gerar plano
plan = generate_meal_plan(user_id, user_profile)
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# API
API_HOST=0.0.0.0
API_PORT=8000

# Banco de Dados
DATABASE_URL=postgresql://user:pass@localhost:5432/diabetesai

# LLM
GEMINI_API_KEY=your_key_here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-flash-latest

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=10
```

### Dependências

```txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
crewai==0.30.0
langchain==0.1.0
google-generativeai==0.3.2
neo4j==5.17.0
```

## 📊 Arquitetura

```
Frontend (AngularJS)
    ↓ HTTP Requests
API Layer (FastAPI)
├── Storage Layer (SQLAlchemy)
├── RAG System (CrewAI + LangChain)
├── LLM Providers (Gemini/OpenAI)
└── Rate Limiter
    ↓ External APIs
Neo4j Graph DB
```

## 🔍 Debugging

### Logs

```bash
# Ver logs da API
tail -f logs/server.log

# Debug específico
uvicorn backend.api:app --log-level debug
```

### Health Checks

```bash
# Verificar saúde da API
curl http://localhost:8000/health

# Verificar banco de dados
curl http://localhost:8000/health/db
```

## 🧪 Testes

### Testes Unitários

```bash
# Testar componentes backend
python -m pytest tests/test_api.py -v

# Testar storage
python -m pytest tests/test_postgresql_migration.py -v
```

### Cobertura

```bash
# Cobertura específica do backend
python -m pytest backend/ --cov=backend --cov-report=html
```

## 📝 Estrutura dos Módulos

### api.py
- **FastAPI application** com todos os endpoints
- **CORS middleware** para frontend
- **Error handling** unificado
- **Background tasks** para processamento

### storage.py
- **SQLAlchemy models** para usuários, planos, refeições
- **Database connection** com fallback SQLite→PostgreSQL
- **CRUD operations** otimizadas
- **Migration support** automática

### meal_plan_rag.py
- **CrewAI agents** especializados (Nutrition, Diabetic, Judge, Causal)
- **RAG pipeline** para recuperação de conhecimento nutricional
- **Plan generation** com validação de restrições
- **Fallback mechanisms** para falhas de LLM

## ⚠️ Considerações Técnicas

- **Python 3.8+** obrigatório por causa do SQLAlchemy 2.0
- **PostgreSQL recomendado** para produção (SQLite para desenvolvimento)
- **Rate limiting** ativo para evitar custos excessivos de API
- **Background processing** para planos complexos
- **Health monitoring** integrado

## 🔄 Manutenção

### Atualização de Dependências

```bash
# Verificar vulnerabilidades
pip audit

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Testar após atualização
python -m pytest tests/
```

### Backup e Recovery

```bash
# Backup via script
./scripts/backup_database.py

# Restore
python scripts/restore_database.py backup_file.db
```

