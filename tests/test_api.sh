#!/bin/bash
# Test script for the Meal Planning RAG API

API_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Meal Planning RAG API"
echo "=========================================="
echo ""

# Test 1: Root endpoint
echo "1. Testing root endpoint (GET /)..."
curl -s -X GET "$API_URL/" | python3 -m json.tool
echo -e "\n"

# Test 2: Health check
echo "2. Testing health check (GET /health)..."
curl -s -X GET "$API_URL/health" | python3 -m json.tool
echo -e "\n"

# Test 3: Example request
echo "3. Testing example request (GET /meal-plan/example)..."
curl -s -X GET "$API_URL/meal-plan/example" | python3 -m json.tool
echo -e "\n"

# Test 4: Generate meal plan (if example_request.json exists)
if [ -f "example_request.json" ]; then
    echo "4. Testing meal plan generation (POST /meal-plan/generate)..."
    echo "   This may take a while (collaborative agents + LLM)..."
    curl -s -X POST "$API_URL/meal-plan/generate" \
        -H "Content-Type: application/json" \
        -d @example_request.json | python3 -m json.tool
    echo -e "\n"
else
    echo "4. Skipping meal plan generation (example_request.json not found)"
fi

echo "=========================================="
echo "API Testing Complete"
echo "=========================================="

