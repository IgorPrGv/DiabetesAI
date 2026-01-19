#!/bin/bash
# Script de configuração do Neo4j

echo "🕸️  Configurando Neo4j para Diabetes AI"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado."
    read -p "Deseja instalar Docker? (s/n): " INSTALL_DOCKER
    if [ "$INSTALL_DOCKER" = "s" ]; then
        echo "📦 Instalando Docker..."
        sudo apt update
        sudo apt install -y docker.io docker-compose
        sudo systemctl start docker
        sudo systemctl enable docker
        sudo usermod -aG docker $USER
        echo "⚠️  Você precisa fazer logout e login novamente para usar Docker sem sudo"
    else
        echo "❌ Docker é necessário para executar Neo4j. Saindo..."
        exit 1
    fi
fi

# Verificar se container já existe
if docker ps -a | grep -q neo4j-diabetes; then
    echo "⚠️  Container Neo4j já existe"
    read -p "Deseja recriar? (s/n) [n]: " RECREATE
    RECREATE=${RECREATE:-n}
    
    if [ "$RECREATE" = "s" ]; then
        echo "🛑 Parando e removendo container existente..."
        docker stop neo4j-diabetes 2>/dev/null
        docker rm neo4j-diabetes 2>/dev/null
    else
        echo "▶️  Iniciando container existente..."
        docker start neo4j-diabetes
        echo "✅ Neo4j iniciado!"
        echo ""
        echo "🌐 Acesse: http://localhost:7474"
        echo "   Usuário: neo4j"
        read -sp "   Senha: " NEO4J_PASSWORD
        echo ""
        exit 0
    fi
fi

# Solicitar informações
read -sp "Senha do Neo4j: " NEO4J_PASSWORD
echo ""

# Criar container
echo "📦 Criando container Neo4j..."
docker run -d \
    --name neo4j-diabetes \
    -p 7474:7474 \
    -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD \
    -e NEO4J_PLUGINS='["apoc"]' \
    -v neo4j_data:/data \
    -v neo4j_logs:/logs \
    neo4j:latest

# Aguardar inicialização
echo "⏳ Aguardando Neo4j inicializar (30 segundos)..."
sleep 30

# Verificar se está rodando
if docker ps | grep -q neo4j-diabetes; then
    echo "✅ Neo4j iniciado com sucesso!"
else
    echo "❌ Erro ao iniciar Neo4j. Verifique os logs:"
    docker logs neo4j-diabetes
    exit 1
fi

# Atualizar .env
echo ""
echo "📝 Atualizando arquivo .env..."

# Remover linhas antigas se existirem
sed -i '/^NEO4J_URI=/d' .env 2>/dev/null || true
sed -i '/^NEO4J_USER=/d' .env 2>/dev/null || true
sed -i '/^NEO4J_PASSWORD=/d' .env 2>/dev/null || true
sed -i '/^NEO4J_ENABLE_LOAD=/d' .env 2>/dev/null || true

# Adicionar nova configuração
echo "" >> .env
echo "# Neo4j" >> .env
echo "NEO4J_URI=bolt://localhost:7687" >> .env
echo "NEO4J_USER=neo4j" >> .env
echo "NEO4J_PASSWORD=$NEO4J_PASSWORD" >> .env
echo "NEO4J_ENABLE_LOAD=true" >> .env

echo "✅ Neo4j configurado!"
echo ""
echo "📋 Configuração adicionada ao .env:"
echo "   NEO4J_URI=bolt://localhost:7687"
echo "   NEO4J_USER=neo4j"
echo "   NEO4J_PASSWORD=***"
echo "   NEO4J_ENABLE_LOAD=true"
echo ""
echo "🌐 Interface web: http://localhost:7474"
echo "   Usuário: neo4j"
echo "   Senha: $NEO4J_PASSWORD"
echo ""
echo "🔄 Reinicie o servidor para aplicar as mudanças."



