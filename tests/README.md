# Tests - Testes do Sistema DiabetesAI

Suite completa de testes para validar funcionalidades do sistema DiabetesAI Care.

## 📊 Visão Geral dos Testes

### Cobertura de Testes

- **Backend API**: Endpoints FastAPI, validações, autenticação
- **Serviços IA**: Agentes CrewAI, RAG, causal inference
- **Banco de Dados**: CRUD operations, migração PostgreSQL
- **Frontend**: Integração AngularJS, templates, funcionalidades
- **Integração**: Fluxos completos usuário-sistema

## 🚀 Como Executar

### Todos os Testes

```bash
# Testes completos
python -m pytest tests/ -v

# Com coverage
python -m pytest tests/ --cov=src --cov-report=html

# Testes específicos
python -m pytest tests/test_api.py -v
python -m pytest tests/test_services.py -v
```

### Testes Rápidos por Categoria

```bash
# Backend/API
./scripts/test_api.sh

# Frontend
python tests/test_frontend_integration.py

# Banco de dados
python tests/test_postgresql_migration.py

# Agentes IA
python tests/test_crewai_active.py
```

## 📋 Testes Disponíveis

### Core API (`test_api.py`)

| Teste | Descrição | Status |
|-------|-----------|--------|
| `test_health_check` | Verificação saúde da API | ✅ |
| `test_user_crud` | CRUD usuários | ✅ |
| `test_meal_plan_generation` | Geração de planos | ✅ |
| `test_adherence_tracking` | Rastreamento adesão | ✅ |

### Serviços IA (`test_services/`)

| Teste | Descrição | Status |
|-------|-----------|--------|
| `test_nutrition_service.py` | Validação planos nutricionais | ✅ |
| `test_diabetic_service.py` | Cálculos TIR/TAR/TBR | ✅ |
| `test_causal_service.py` | Análise causal | ✅ |
| `test_chat_service.py` | RAG e conversação | ✅ |

### Frontend (`test_frontend_*.py`)

| Teste | Descrição | Status |
|-------|-----------|--------|
| `test_frontend_display.py` | Renderização templates | ✅ |
| `test_frontend_integration.py` | Integração API | ✅ |
| `test_pages_functionality.py` | Funcionalidades páginas | ✅ |

### Banco de Dados (`test_database/`)

| Teste | Descrição | Status |
|-------|-----------|--------|
| `test_postgresql_migration.py` | Migração SQLite→PostgreSQL | ✅ |
| `test_crud_operations.py` | Operações básicas | ✅ |

## 🔧 Configuração dos Testes

### Dependências

```bash
pip install pytest pytest-cov pytest-asyncio requests
```

### Variáveis de Ambiente

```bash
# Para testes
export TEST_DATABASE_URL="sqlite:///test.db"
export TEST_GEMINI_API_KEY="test_key"

# Para testes de integração
export INTEGRATION_TEST=1
```

### Fixtures

```python
# Exemplo de fixture
@pytest.fixture
def test_user():
    return {
        "full_name": "Test User",
        "health_metrics": {"diabetes_type": "Type 2"},
        "preferences": {"cuisine": "Brazilian"}
    }
```

## 📊 Relatórios de Coverage

```bash
# Gerar relatório HTML
pytest --cov=. --cov-report=html
# Abrir em navegador: htmlcov/index.html

# Relatório terminal
pytest --cov=. --cov-report=term-missing
```

## 🐛 Debugging de Testes

### Testes Falhando

```bash
# Ver logs detalhados
pytest tests/test_api.py -v -s

# Debug específico
pytest tests/test_api.py::test_meal_plan_generation -xvs

# PDB para debug
pytest tests/test_api.py --pdb
```

### Problemas Comuns

**API não responde:**
```bash
# Verificar se servidor está rodando
curl http://localhost:8000/health

# Iniciar servidor de teste
./scripts/start_server.sh
```

**Banco de dados:**
```bash
# Resetar banco de teste
rm test.db
pytest tests/test_database.py::test_setup
```

**Frontend:**
```bash
# Verificar arquivos estáticos
ls -la frontend/
python tests/test_frontend_display.py
```

## 📈 CI/CD Integration

### GitHub Actions

```yaml
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=. --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit Hooks

```bash
# Instalar hooks
pre-commit install

# Rodar testes antes de commit
pre-commit run --all-files
```

## 📋 Boas Práticas

### Escrevendo Novos Testes

```python
def test_nova_funcionalidade():
    # Arrange
    setup_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
    assert result.status_code == 200
```

### Nomenclatura

- Arquivos: `test_*.py`
- Funções: `test_*`
- Classes: `Test*`

### Cobertura Mínima

- **Backend**: 80% coverage mínimo
- **API**: Todos os endpoints testados
- **Serviços**: Casos de erro e sucesso

