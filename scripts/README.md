# Scripts - Utilitários e Automação

Scripts utilitários para desenvolvimento, deployment e manutenção do projeto DiabetesAI Care.

## 🚀 Scripts Principais

### Servidor e Deployment

| Script | Descrição | Uso |
|--------|-----------|-----|
| `start_server.sh` | Inicia API FastAPI + Frontend | `./start_server.sh` |
| `setup.sh` | Configuração inicial completa | `./setup.sh` |
| `quick_test.sh` | Teste rápido de todos os componentes | `./quick_test.sh` |

### Banco de Dados

| Script | Descrição | Uso |
|--------|-----------|-----|
| `setup_postgresql_complete.sh` | Instalação completa PostgreSQL + Migração | `./setup_postgresql_complete.sh` |
| `setup_postgresql.sh` | Apenas configuração PostgreSQL | `./setup_postgresql.sh` |
| `setup_neo4j.sh` | Configuração Neo4j para grafos | `./setup_neo4j.sh` |

### Testes e Verificação

| Script | Descrição | Uso |
|--------|-----------|-----|
| `test_diabetes_ai.sh` | Teste completo do sistema | `./test_diabetes_ai.sh` |
| `test_api.sh` | Testes específicos da API | `./test_api.sh` |

## 📋 Como Usar

### Setup Inicial

```bash
# 1. Tornar scripts executáveis
chmod +x scripts/*.sh

# 2. Configuração completa
./scripts/setup.sh

# 3. Ou configuração passo a passo
./scripts/setup_postgresql_complete.sh
./scripts/setup_neo4j.sh
```

### Desenvolvimento Diário

```bash
# Iniciar servidor local
./scripts/start_server.sh

# Teste rápido antes de commit
./scripts/quick_test.sh
```

### Troubleshooting

```bash
# Verificar se portas estão livres
lsof -i :8000  # API
lsof -i :8080  # Frontend

# Kill processos se necessário
pkill -f uvicorn
pkill -f python
```

## ⚙️ Configurações

### Variáveis de Ambiente

```bash
# API Keys
export GEMINI_API_KEY="your_key_here"

# Banco de Dados
export DATABASE_URL="postgresql://user:pass@localhost:5432/diabetesai"

# Neo4j (opcional)
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
```

### Dependências do Sistema

- **Python 3.8+** com virtualenv
- **PostgreSQL 13+** ou SQLite (fallback)
- **Neo4j 4.4+** (opcional, para grafos)
- **Node.js** (para frontend)

## 🔧 Manutenção

### Backup

```bash
# Backup automático (integrado nos scripts)
./scripts/start_server.sh  # Cria backup em data/backups/
```

### Limpeza

```bash
# Limpar logs antigos
find logs/ -name "*.log" -mtime +30 -delete

# Limpar pycache
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 📝 Logs e Debug

Todos os scripts geram logs em `logs/`:

```
logs/
├── server.log          # Servidor principal
├── api.log            # Chamadas da API
├── database.log       # Operações de BD
└── error.log          # Erros críticos
```

Para debug verbose:
```bash
DEBUG=1 ./scripts/start_server.sh
```

