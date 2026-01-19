# Data - Bases de Dados e Recursos

Diretório contendo todas as bases de dados nutricionais, backups e recursos estáticos do projeto DiabetesAI.

## 📊 Bases de Dados Disponíveis

### Banco Principal

| Arquivo | Descrição | Formato | Tamanho |
|---------|-----------|---------|---------|
| `diabetesai.db` | Banco SQLite principal | SQLite3 | ~2MB |
| `diabetesai.db` (PostgreSQL) | Migração para produção | PostgreSQL | Dinâmico |

### Bases Nutricionais

| Arquivo | Descrição | Origem | Registros |
|---------|-----------|--------|-----------|
| `taco_unified.jsonl` | Tabela Brasileira de Composição de Alimentos | TACO/UFV | 600+ alimentos |
| `tbca_unified.jsonl` | Tabela Brasileira Complementar | TBCA | 200+ alimentos |
| `all_bases_unified_schema.zip` | Bases unificadas + schema | Processado | 800+ alimentos |

### Documentação

| Arquivo | Descrição | Uso |
|---------|-----------|-----|
| `taco_4.pdf` | Manual TACO 4ª edição | Referência nutricional |

## 🔧 Estrutura das Bases

### Schema Unificado

```json
{
  "food_name": "Arroz cozido",
  "category": "Cereais",
  "nutrition": {
    "calories_kcal": 130,
    "carbohydrate_g": 28.1,
    "protein_g": 2.5,
    "fat_g": 0.3,
    "fiber_g": 1.6,
    "sodium_mg": 1.0,
    "glycemic_index": 55
  },
  "source": "TACO",
  "processed_at": "2024-01-19"
}
```

### Categorias Principais

- **Cereais e derivados** (Arroz, trigo, milho)
- **Leguminosas** (Feijão, lentilha, grão-de-bico)
- **Carnes e derivados** (Frango, boi, peixe)
- **Leite e derivados** (Iogurte, queijo)
- **Frutas** (Maçã, banana, laranja)
- **Verduras** (Alface, espinafre, brócolis)
- **Óleos e gorduras** (Azeite, óleo de soja)

## 🚀 Como Usar

### Carregar Base Nutricional

```python
import json

# Carregar TACO
with open('data/taco_unified.jsonl', 'r') as f:
    for line in f:
        food = json.loads(line)
        print(f"{food['food_name']}: {food['nutrition']['calories_kcal']} kcal")
```

### API de Consulta

```python
from services.nutrition_service import NutritionService

service = NutritionService()
nutrition = service.get_food_nutrition("Arroz integral cozido")
print(f"IG: {nutrition['glycemic_index']}")
```

## 🔄 Backups

### Estrutura de Backup

```
backups/
├── pre_migration_backup_20240119_020155.db  # SQLite antes migração
├── pre_migration_backup_20240119_020715.db  # Backup incremental
└── README.md                                 # Descrição dos backups
```

### Como Fazer Backup

```bash
# Backup automático (via scripts)
./scripts/start_server.sh  # Cria backup automático

# Backup manual
python backup_database.py
```

### Restauração

```bash
# Restaurar SQLite
cp backups/backup_file.db data/diabetesai.db

# Para PostgreSQL
pg_restore -d diabetesai backups/postgres_backup.sql
```

## 📊 Estatísticas das Bases

### Cobertura Nutricional

- **Calorias**: 100% dos alimentos
- **Macronutrientes**: Carboidratos, proteínas, gorduras (95%)
- **Micronutrientes**: Sódio, fibras, vitaminas (70%)
- **Índice Glicêmico**: Alimentos básicos (60%)

### Distribuição por Categoria

```
Cereais:     25%
Leguminosas: 15%
Carnes:      20%
Frutas:      15%
Verduras:    15%
Outros:      10%
```

## 🔍 Validação e Qualidade

### Critérios de Qualidade

- ✅ **Dados validados** contra literatura nutricional
- ✅ **Unidade padronizada** (100g por porção)
- ✅ **Fontes confiáveis** (TACO, TBCA, USDA)
- ✅ **Atualização regular** (anual)

### Scripts de Validação

```bash
# Verificar integridade
python -c "
import json
count = 0
with open('data/taco_unified.jsonl') as f:
    for line in f:
        food = json.loads(line)
        assert 'nutrition' in food
        count += 1
print(f'✅ {count} alimentos validados')
"
```

## 📝 Manutenção

### Atualização de Bases

```bash
# 1. Baixar nova versão TACO
wget https://www.nutricao.ufv.br/taco/ -O data/taco_novo.pdf

# 2. Processar dados
python scripts/process_nutrition_data.py

# 3. Validar
python tests/test_nutrition_data.py

# 4. Deploy
mv data/taco_unified.jsonl.backup data/taco_unified.jsonl.old
mv data/taco_new.jsonl data/taco_unified.jsonl
```

### Limpeza

```bash
# Arquivos temporários
find data/ -name "*.tmp" -delete

# Backups antigos (>30 dias)
find backups/ -name "*.db" -mtime +30 -delete
```

## ⚠️ Avisos Importantes

- **Backup obrigatório** antes de qualquer modificação
- **Testes completos** após atualização de bases
- **Versionamento** de mudanças nas bases nutricionais
- **Documentação** de fontes e metodologias
