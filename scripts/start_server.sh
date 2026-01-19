#!/bin/bash
# Script para iniciar o servidor API com os parâmetros corretos

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  INICIANDO SERVIDOR API${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Diretório do projeto (pai do diretório scripts)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd "$SCRIPT_DIR"

# Verificar se o venv existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Erro: venv não encontrado!${NC}"
    echo "   Execute: python -m venv venv"
    exit 1
fi

# Ativar venv
echo -e "${YELLOW}🔄 Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Verificar se o .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado${NC}"
else
    echo -e "${YELLOW}✅ Arquivo .env encontrado${NC}"
fi

# Carregar variáveis do .env (se existir)
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Parâmetros padrão (podem ser sobrescritos pelo .env)
export LLM_PROVIDER=${LLM_PROVIDER:-gemini}
export GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.5-flash}
export EMBEDDING_DEVICE=${EMBEDDING_DEVICE:-cpu}

# Verificar se a API key está configurada
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ Erro: GEMINI_API_KEY não configurada!${NC}"
    echo "   Configure no arquivo .env: GEMINI_API_KEY=AIzaSy..."
    exit 1
fi

# Verificar formato da API key
if [[ ! "$GEMINI_API_KEY" =~ ^AIza ]]; then
    echo -e "${YELLOW}⚠️  AVISO: API Key não começa com 'AIza'${NC}"
    echo "   A chave pode não ser válida (formato esperado: AIzaSy...)"
    echo -e "${YELLOW}   Continuando mesmo assim...${NC}\n"
fi

# Verificar e limpar portas ocupadas
echo -e "${YELLOW}🔍 Verificando portas ocupadas...${NC}"

# Porta 8000 (API)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Porta 8000 (API) já está em uso!${NC}"
    echo -e "${YELLOW}🛑 Parando processo na porta 8000...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Porta 8000 liberada${NC}"
fi

# Porta 8080 (Frontend/HTTP)
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Porta 8080 (HTTP) já está em uso!${NC}"
    echo -e "${YELLOW}🛑 Parando processo na porta 8080...${NC}"
    lsof -ti :8080 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Porta 8080 liberada${NC}"
fi

# Mostrar configuração
echo -e "\n${GREEN}📋 CONFIGURAÇÃO:${NC}"
echo -e "   Provider: ${LLM_PROVIDER}"
echo -e "   Modelo: ${GEMINI_MODEL}"
echo -e "   Embedding Device: ${EMBEDDING_DEVICE}"
echo -e "   API Key: ${GEMINI_API_KEY:0:20}... (${#GEMINI_API_KEY} caracteres)"
echo -e "   Porta: 8000"
echo -e "   Host: 0.0.0.0\n"

# Modo de execução
MODE="${1:-foreground}"

if [ "$MODE" = "background" ] || [ "$MODE" = "bg" ]; then
    # Executar em background
    echo -e "${YELLOW}🚀 Iniciando servidor em background...${NC}"
    LOG_FILE="/tmp/api_server_$(date +%Y%m%d_%H%M%S).log"
    nohup uvicorn backend.api:app --host 0.0.0.0 --port 8000 > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    
    echo -e "${GREEN}✅ Servidor iniciado!${NC}"
    echo -e "   PID: $SERVER_PID"
    echo -e "   Log: $LOG_FILE"
    echo -e "   URL: http://localhost:8000"
    echo -e "\n   Para parar o servidor:"
    echo -e "   ${YELLOW}kill $SERVER_PID${NC}"
    echo -e "\n   Para ver os logs:"
    echo -e "   ${YELLOW}tail -f $LOG_FILE${NC}"
    
    # Aguardar um pouco e verificar se iniciou
    sleep 30
    if ps -p $SERVER_PID > /dev/null; then
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            echo -e "\n${GREEN}✅ Servidor está respondendo!${NC}"
        else
            echo -e "\n${YELLOW}⚠️  Servidor iniciado mas ainda não está respondendo${NC}"
            echo -e "   Verifique os logs: tail -f $LOG_FILE"
        fi
    else
        echo -e "\n${RED}❌ Servidor não iniciou corretamente${NC}"
        echo -e "   Verifique os logs: cat $LOG_FILE"
        exit 1
    fi
else
    # Executar em foreground
    echo -e "${YELLOW}🚀 Iniciando servidor em foreground...${NC}"
    echo -e "${GREEN}✅ Servidor rodando em: http://localhost:8000${NC}"
    echo -e "${YELLOW}   Pressione Ctrl+C para parar${NC}\n"
    
    uvicorn backend.api:app --host 0.0.0.0 --port 8000
fi
