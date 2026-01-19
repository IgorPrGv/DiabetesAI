#!/bin/bash
# Quick endpoint tests

API="http://localhost:8000"

echo "=== Testing API Endpoints ==="
echo ""

echo "1. Root endpoint:"
curl -s "$API/" | python3 -m json.tool
echo -e "\n"

echo "2. Health check:"
curl -s "$API/health" | python3 -m json.tool
echo -e "\n"

echo "3. Example request:"
curl -s "$API/meal-plan/example" | python3 -m json.tool | head -30
echo -e "\n"

echo "4. Generate meal plan (this will take a while...):"
curl -s -X POST "$API/meal-plan/generate" \
  -H "Content-Type: application/json" \
  -d @example_request.json | python3 -m json.tool
