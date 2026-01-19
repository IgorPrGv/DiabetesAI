# Testing the API with curl

## Prerequisites

1. **Start the API server:**
   ```bash
   python api.py
   ```
   The API will run on `http://localhost:8000`

2. **Keep the API running** in one terminal, and use another terminal for testing.

## Quick Test Script

Run the automated test script:
```bash
./test_api.sh
```

## Manual curl Commands

### 1. Root Endpoint (API Information)

```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "name": "Meal Planning RAG API",
  "version": "1.0.0",
  "description": "REST API for generating personalized meal plans",
  "endpoints": {...}
}
```

### 2. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "meal-planning-rag-api"
}
```

### 3. Get Example Request

```bash
curl http://localhost:8000/meal-plan/example
```

**Expected Response:**
```json
{
  "example_request": {
    "meal_history": [...],
    "health_metrics": {...},
    ...
  }
}
```

### 4. Generate Meal Plan (Main Endpoint)

**Using the example file:**
```bash
curl -X POST http://localhost:8000/meal-plan/generate \
  -H "Content-Type: application/json" \
  -d @example_request.json
```

**Or with inline JSON:**
```bash
curl -X POST http://localhost:8000/meal-plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "meal_history": ["Café da manhã: Pão integral"],
    "health_metrics": {
      "diabetes_type": "Type 2",
      "weight": "85 kg",
      "height": "1.75 m"
    },
    "preferences": {
      "cuisine": "Brasileira",
      "region": "Sudeste"
    },
    "goals": ["Controlar glicemia"],
    "restrictions": ["Diabetes tipo 2"],
    "region": "Sudeste brasileiro"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "meal_plan": "Generated meal plan text...",
  "message": "Meal plan generated successfully"
}
```

## Pretty Print JSON Output

To format the JSON output nicely, pipe to `python3 -m json.tool`:

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

Or use `jq` if installed:
```bash
curl http://localhost:8000/health | jq
```

## Testing with Verbose Output

To see request details (headers, status codes):

```bash
curl -v http://localhost:8000/health
```

## Common Issues

**Connection refused:**
- Make sure the API is running: `python api.py`
- Check the port (default is 8000)

**Slow response on meal plan generation:**
- This is normal - the RAG system with collaborative agents takes time
- Can take 1-5 minutes depending on your system

**Error: "RAG system not initialized":**
- Run `python test_rag_system.py` first to initialize the vector database

## Example Full Test Sequence

```bash
# 1. Check if API is running
curl http://localhost:8000/health

# 2. Get example request
curl http://localhost:8000/meal-plan/example > example_response.json

# 3. Generate meal plan (this takes time!)
curl -X POST http://localhost:8000/meal-plan/generate \
  -H "Content-Type: application/json" \
  -d @example_request.json \
  -o meal_plan_response.json

# 4. View the response
cat meal_plan_response.json | python3 -m json.tool
```

