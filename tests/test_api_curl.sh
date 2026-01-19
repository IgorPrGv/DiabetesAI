#!/bin/bash
# Quick curl tests for Meal Planning RAG API

API_URL="http://localhost:8000"

echo "=========================================="
echo "Testing Meal Planning RAG API with curl"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1. Health Check (GET /health)"
echo "Command: curl $API_URL/health"
echo "Response:"
curl -s "$API_URL/health" | python3 -m json.tool
echo -e "\n"

# Test 2: Root Endpoint
echo "2. Root Endpoint (GET /)"
echo "Command: curl $API_URL/"
echo "Response:"
curl -s "$API_URL/" | python3 -m json.tool
echo -e "\n"

# Test 3: Example Request
echo "3. Example Request (GET /meal-plan/example)"
echo "Command: curl $API_URL/meal-plan/example"
echo "Response (first 40 lines):"
curl -s "$API_URL/meal-plan/example" | python3 -m json.tool | head -40
echo -e "\n... (truncated)\n"

# Test 4: Generate Meal Plan (with explanation)
echo "4. Generate Meal Plan (POST /meal-plan/generate)"
echo "Command:"
echo "  curl -X POST $API_URL/meal-plan/generate \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d @example_request.json"
echo ""
echo "⚠️  WARNING: This request takes 5-10+ minutes to complete!"
echo "   The API is processing with collaborative agents + LLM."
echo ""
read -p "Do you want to start the meal plan generation? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting request... (this will take a while)"
    curl -X POST "$API_URL/meal-plan/generate" \
        -H "Content-Type: application/json" \
        -d @example_request.json | python3 -m json.tool
else
    echo "Skipped. You can run it manually with:"
    echo "curl -X POST $API_URL/meal-plan/generate -H \"Content-Type: application/json\" -d @example_request.json"
fi

echo ""
echo "=========================================="
echo "Testing Complete"
echo "=========================================="

