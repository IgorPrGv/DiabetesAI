#!/bin/bash

# Test script to verify all changes
# Tests plan generation, loading, and database operations

echo "=========================================="
echo "Testing DiabetesAI Plan System"
echo "=========================================="
echo ""

# Check if server is running
echo "1. Checking if API server is running..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ API server is running"
else
    echo "❌ API server is not running"
    echo "   Start it with: cd /home/davi/topicos && source venv/bin/activate && python -m uvicorn backend.api:app --reload"
    exit 1
fi

# Check database configuration
echo ""
echo "2. Checking database configuration..."
if [ -n "$DATABASE_URL" ]; then
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        echo "✅ Using PostgreSQL: $DATABASE_URL"
    else
        echo "⚠️  DATABASE_URL is set but not PostgreSQL: $DATABASE_URL"
    fi
else
    echo "⚠️  DATABASE_URL not set - using default SQLite"
    echo "   To use PostgreSQL, set: export DATABASE_URL='postgresql://user:pass@localhost/dbname'"
fi

# Run the automated test
echo ""
echo "3. Running automated test suite..."
echo "   This will test:"
echo "   - User registration and login"
echo "   - Profile creation and update"
echo "   - Plan generation (explicit only, no auto-generation)"
echo "   - Plan loading from database"
echo "   - Plan history retrieval"
echo "   - Database health check"
echo "   - Consumed meals tracking"
echo ""

cd /home/davi/topicos

# Activate virtual environment if needed
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install pytest if needed
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing pytest..."
    pip install pytest requests
fi

# Run the test
python tests/test_plan_generation_and_loading.py

TEST_RESULT=$?

echo ""
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    echo ""
    echo "Summary of changes implemented:"
    echo "1. ✅ Removed all automatic plan generation"
    echo "2. ✅ Replaced SQLite calls with PostgreSQL/SQLAlchemy"
    echo "3. ✅ Fixed frontend to only load existing plans"
    echo "4. ✅ Plans now load from PostgreSQL database"
    echo "5. ✅ User must explicitly click 'Gerar novo plano'"
else
    echo "❌ SOME TESTS FAILED"
    echo ""
    echo "Please check the error messages above"
fi
echo "=========================================="

exit $TEST_RESULT
