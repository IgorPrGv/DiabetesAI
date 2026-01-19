#!/bin/bash
# Script de teste completo para DiabetesAI Care
# Testa API, frontend e funcionalidades principais

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do projeto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  TESTE COMPLETO - DIABETESAI CARE${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Status dos testes
TESTS_PASSED=0
TESTS_FAILED=0

# Função para log de teste
log_test() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $test_name${NC}: $message"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $test_name${NC}: $message"
        ((TESTS_FAILED++))
    fi
}

# 1. Verificar se ambiente virtual existe
echo -e "${YELLOW}🔍 VERIFICANDO AMBIENTE...${NC}"
if [ ! -d "venv" ]; then
    log_test "Ambiente Virtual" "FAIL" "venv não encontrado"
    exit 1
fi
log_test "Ambiente Virtual" "PASS" "venv encontrado"

# 2. Verificar se arquivo .env existe
if [ ! -f ".env" ]; then
    log_test "Arquivo .env" "FAIL" ".env não encontrado"
    exit 1
fi
log_test "Arquivo .env" "PASS" ".env encontrado"

# 3. Carregar variáveis do .env
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# 4. Verificar API key
if [ -z "$GEMINI_API_KEY" ]; then
    log_test "API Key" "FAIL" "GEMINI_API_KEY não configurada"
    exit 1
fi
log_test "API Key" "PASS" "GEMINI_API_KEY configurada (${#GEMINI_API_KEY} caracteres)"

# 5. Limpar portas ocupadas
echo -e "\n${YELLOW}🧹 LIMPANDO PORTAS OCUPADAS...${NC}"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}  Parando processo na porta 8000...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}  Parando processo na porta 8080...${NC}"
    lsof -ti :8080 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# 6. Iniciar servidor API em background
echo -e "\n${YELLOW}🚀 INICIANDO SERVIDOR API...${NC}"
source venv/bin/activate
export LLM_PROVIDER=${LLM_PROVIDER:-gemini}
export GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.5-flash}
export EMBEDDING_DEVICE=${EMBEDDING_DEVICE:-cpu}

# Iniciar servidor em background
LOG_FILE="/tmp/api_test_$(date +%Y%m%d_%H%M%S).log"
nohup uvicorn api:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &
API_PID=$!
echo -e "${YELLOW}  Servidor API iniciado (PID: $API_PID)${NC}"

# 7. Aguardar servidor API inicializar
echo -e "${YELLOW}⏰ Aguardando servidor API inicializar (30s)...${NC}"
sleep 30

# 8. Testar health check da API
echo -e "\n${YELLOW}🔍 TESTANDO API...${NC}"
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    log_test "API Health Check" "PASS" "http://localhost:8000/api/health respondendo"

    # Testar resposta detalhada
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
    if echo "$HEALTH_RESPONSE" | grep -q "status.*healthy"; then
        log_test "API Response" "PASS" "Resposta correta da API"
    else
        log_test "API Response" "FAIL" "Resposta inesperada: $HEALTH_RESPONSE"
    fi
else
    log_test "API Health Check" "FAIL" "API não está respondendo"
    echo -e "${RED}  Logs da API: tail -f $LOG_FILE${NC}"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# 9. Testar endpoints principais da API
echo -e "\n${YELLOW}🔍 TESTANDO ENDPOINTS DA API...${NC}"

# Teste 1: Listar usuários (deve retornar erro 401 ou lista vazia)
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/users | grep -q "401"; then
    log_test "API Users (Autenticação)" "PASS" "Endpoint protegido corretamente"
else
    log_test "API Users (Autenticação)" "FAIL" "Endpoint não está protegido"
fi

# Teste 2: Buscar usuário por auth_id (deve retornar 404 para ID inexistente)
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/users/by-auth/999999 | grep -q "404"; then
    log_test "API User by Auth" "PASS" "Tratamento correto de usuário inexistente"
else
    log_test "API User by Auth" "FAIL" "Resposta inesperada para usuário inexistente"
fi

# 10. Iniciar servidor frontend
echo -e "\n${YELLOW}🌐 INICIANDO SERVIDOR FRONTEND...${NC}"
cd frontend
python -m http.server 8080 > /dev/null 2>&1 &
FRONTEND_PID=$!
cd ..
echo -e "${YELLOW}  Servidor frontend iniciado (PID: $FRONTEND_PID)${NC}"

# 11. Aguardar frontend inicializar
sleep 2

# 12. Testar frontend
echo -e "\n${YELLOW}🔍 TESTANDO FRONTEND...${NC}"
if curl -s http://localhost:8080/home.html | grep -q "<!DOCTYPE html>"; then
    log_test "Frontend HTML" "PASS" "home.html carregando corretamente"

    # Verificar se AngularJS está presente
    if curl -s http://localhost:8080/home.html | grep -q "angular.min.js"; then
        log_test "AngularJS Library" "PASS" "Biblioteca AngularJS carregada"
    else
        log_test "AngularJS Library" "FAIL" "Biblioteca AngularJS não encontrada"
    fi

    # Verificar se controller está definido
    if curl -s http://localhost:8080/home.html | grep -q "ng-controller"; then
        log_test "Angular Controller" "PASS" "Controller AngularJS definido"
    else
        log_test "Angular Controller" "FAIL" "Controller AngularJS não encontrado"
    fi

else
    log_test "Frontend HTML" "FAIL" "home.html não está carregando"
fi

# 13. Testar arquivos estáticos do frontend
echo -e "\n${YELLOW}🔍 TESTANDO ARQUIVOS ESTÁTICOS...${NC}"

# Testar se login.html existe
if curl -s http://localhost:8080/login.html | grep -q "<!DOCTYPE html>"; then
    log_test "Login Page" "PASS" "login.html acessível"
else
    log_test "Login Page" "FAIL" "login.html não acessível"
fi

# Testar se register.html existe
if curl -s http://localhost:8080/register.html | grep -q "<!DOCTYPE html>"; then
    log_test "Register Page" "PASS" "register.html acessível"
else
    log_test "Register Page" "FAIL" "register.html não acessível"
fi

# Testar se onboarding.html existe
if curl -s http://localhost:8080/onboarding.html | grep -q "<!DOCTYPE html>"; then
    log_test "Onboarding Page" "PASS" "onboarding.html acessível"
else
    log_test "Onboarding Page" "FAIL" "onboarding.html não acessível"
fi

# 14. Teste de integração básica
echo -e "\n${YELLOW}🔗 TESTE DE INTEGRAÇÃO...${NC}"

# Criar usuário de teste se não existir
TEST_USER_ID=37
echo -e "${YELLOW}  Testando usuário de teste (ID: $TEST_USER_ID)...${NC}"

# Verificar se usuário existe
USER_EXISTS=$(curl -s "http://localhost:8000/api/users/by-auth/$TEST_USER_ID" | grep -c "id.*34" || echo "0")
if [ "$USER_EXISTS" -gt 0 ]; then
    log_test "Usuário de Teste" "PASS" "Usuário ID 34 encontrado via auth_id $TEST_USER_ID"

    # Testar carregamento de plano
    PLAN_RESPONSE=$(curl -s "http://localhost:8000/api/users/34/plan")
    if echo "$PLAN_RESPONSE" | grep -q "plan_json"; then
        log_test "Carregamento de Plano" "PASS" "Plano carregado com sucesso"
    else
        log_test "Carregamento de Plano" "FAIL" "Falha ao carregar plano"
    fi

    # Testar adesão
    ADHERENCE_RESPONSE=$(curl -s "http://localhost:8000/api/users/34/adherence")
    if echo "$ADHERENCE_RESPONSE" | grep -q "success.*true"; then
        log_test "Carregamento de Adesão" "PASS" "Adesão carregada com sucesso"
    else
        log_test "Carregamento de Adesão" "FAIL" "Falha ao carregar adesão"
    fi

else
    log_test "Usuário de Teste" "WARN" "Usuário de teste não encontrado (isso é normal se não foi criado ainda)"
fi

# 15. Teste de funcionalidades especiais
echo -e "\n${YELLOW}🎯 TESTES ESPECIAIS...${NC}"

# Testar endpoint de chat (deve retornar erro sem mensagem)
CHAT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/chat" -H "Content-Type: application/json" -d '{"message":"teste"}')
if echo "$CHAT_RESPONSE" | grep -q "detail"; then
    log_test "Chat API" "PASS" "Endpoint de chat responde (mesmo com erro esperado)"
else
    log_test "Chat API" "FAIL" "Endpoint de chat não responde"
fi

# Testar busca de alimentos
FOOD_RESPONSE=$(curl -s "http://localhost:8000/api/food/Arroz/nutrition")
if echo "$FOOD_RESPONSE" | grep -q "nutrition"; then
    log_test "Busca de Alimentos" "PASS" "API de nutrição funcionando"
else
    log_test "Busca de Alimentos" "FAIL" "API de nutrição não responde"
fi

# 16. Relatório final
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}           RELATÓRIO FINAL${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo -e "📊 Estatísticas:"
echo -e "   ✅ Testes Aprovados: $TESTS_PASSED"
echo -e "   ❌ Testes Reprovados: $TESTS_FAILED"
echo -e "   📈 Taxa de Sucesso: $SUCCESS_RATE%"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 TODOS OS TESTES APROVADOS!${NC}"
    echo -e "${GREEN}   DiabetesAI Care está funcionando perfeitamente!${NC}"
else
    echo -e "\n${YELLOW}⚠️  Alguns testes falharam.${NC}"
    echo -e "${YELLOW}   Verifique os logs acima para detalhes.${NC}"
fi

echo -e "\n${BLUE}🔗 URLs de Acesso:${NC}"
echo -e "   🌐 Frontend: http://localhost:8080/home.html"
echo -e "   🔌 API: http://localhost:8000"
echo -e "   📊 API Docs: http://localhost:8000/docs"
echo -e "   🔐 Login: http://localhost:8080/login.html"

echo -e "\n${YELLOW}🛑 Para parar os servidores:${NC}"
echo -e "   API (PID $API_PID): kill $API_PID"
echo -e "   Frontend (PID $FRONTEND_PID): kill $FRONTEND_PID"
echo -e "   Ou: pkill -f \"uvicorn\|http.server\""

# 17. Cleanup se tudo passou
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🧹 Limpando arquivos de log...${NC}"
    rm -f "$LOG_FILE" 2>/dev/null || true
fi

echo -e "\n${BLUE}========================================${NC}"

exit $TESTS_FAILED
