#!/bin/bash
# Teste rápido das funcionalidades principais

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    TESTE RÁPIDO - DIABETESAI CARE${NC}"
echo -e "${BLUE}========================================${NC}\n"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd "$SCRIPT_DIR"

# 1. Verificar arquivos essenciais
echo -e "${YELLOW}📁 VERIFICANDO ARQUIVOS...${NC}"

if [ -f "frontend/home.html" ]; then
    echo -e "${GREEN}✅ frontend/home.html encontrado${NC}"
else
    echo -e "${RED}❌ frontend/home.html não encontrado${NC}"
    exit 1
fi

if [ -f "api.py" ]; then
    echo -e "${GREEN}✅ api.py encontrado${NC}"
else
    echo -e "${RED}❌ api.py não encontrado${NC}"
    exit 1
fi

# 2. Verificar estrutura do HTML
echo -e "\n${YELLOW}🔍 VERIFICANDO ESTRUTURA HTML...${NC}"

if grep -q "ng-app" frontend/home.html; then
    echo -e "${GREEN}✅ AngularJS app definido${NC}"
else
    echo -e "${RED}❌ AngularJS app não encontrado${NC}"
fi

if grep -q "MainCtrl" frontend/home.html; then
    echo -e "${GREEN}✅ Controller MainCtrl definido${NC}"
else
    echo -e "${RED}❌ Controller MainCtrl não encontrado${NC}"
fi

if grep -q "loadUser" frontend/home.html; then
    echo -e "${GREEN}✅ Função loadUser definida${NC}"
else
    echo -e "${RED}❌ Função loadUser não encontrada${NC}"
fi

# 3. Verificar estrutura da API
echo -e "\n${YELLOW}🔍 VERIFICANDO ESTRUTURA DA API...${NC}"

if grep -q "FastAPI" api.py; then
    echo -e "${GREEN}✅ FastAPI importado${NC}"
else
    echo -e "${RED}❌ FastAPI não encontrado${NC}"
fi

if grep -q "@api_router.get" api.py; then
    echo -e "${GREEN}✅ Rotas GET definidas${NC}"
else
    echo -e "${RED}❌ Rotas GET não encontradas${NC}"
fi

# 4. Verificar configurações
echo -e "\n${YELLOW}🔍 VERIFICANDO CONFIGURAÇÕES...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Arquivo .env encontrado${NC}"

    if grep -q "GEMINI_API_KEY" .env; then
        echo -e "${GREEN}✅ GEMINI_API_KEY configurada${NC}"
    else
        echo -e "${RED}❌ GEMINI_API_KEY não encontrada no .env${NC}"
    fi
else
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
fi

# 5. Verificar dependências
echo -e "\n${YELLOW}🔍 VERIFICANDO DEPENDÊNCIAS...${NC}"

if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Ambiente virtual encontrado${NC}"

    if [ -f "venv/bin/uvicorn" ]; then
        echo -e "${GREEN}✅ Uvicorn disponível${NC}"
    else
        echo -e "${RED}❌ Uvicorn não encontrado no venv${NC}"
    fi
else
    echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
fi

# 6. Teste de sintaxe Python
echo -e "\n${YELLOW}🐍 TESTANDO SINTAXE PYTHON...${NC}"

if python -m py_compile api.py 2>/dev/null; then
    echo -e "${GREEN}✅ api.py compila sem erros${NC}"
else
    echo -e "${RED}❌ api.py tem erros de sintaxe${NC}"
fi

# 7. Verificar se servidores estão rodando
echo -e "\n${YELLOW}🔌 VERIFICANDO SERVIDORES...${NC}"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Servidor API rodando na porta 8000${NC}"
else
    echo -e "${YELLOW}⚠️  Servidor API não está rodando (porta 8000)${NC}"
fi

if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Servidor frontend rodando na porta 8080${NC}"
else
    echo -e "${YELLOW}⚠️  Servidor frontend não está rodando (porta 8080)${NC}"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}         RESUMO DO TESTE${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}🚀 Para iniciar os servidores:${NC}"
echo -e "   API: ./scripts/start_server.sh background"
echo -e "   Frontend: cd frontend && python -m http.server 8080"

echo -e "\n${YELLOW}🔗 URLs de acesso:${NC}"
echo -e "   Frontend: http://localhost:8080/home.html"
echo -e "   API: http://localhost:8000"
echo -e "   API Docs: http://localhost:8000/docs"

echo -e "\n${GREEN}✅ Teste rápido concluído!${NC}"
echo -e "${BLUE}========================================${NC}"
