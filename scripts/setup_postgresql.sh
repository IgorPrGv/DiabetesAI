#!/bin/bash
# Script de configuração do PostgreSQL

echo "🐘 Configurando PostgreSQL para Diabetes AI"
echo ""

# Verificar se PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL não encontrado. Instalando..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
fi

# Solicitar informações
read -p "Nome do banco de dados [diabetesai]: " DB_NAME
DB_NAME=${DB_NAME:-diabetesai}

read -p "Nome do usuário [diabetes_user]: " DB_USER
DB_USER=${DB_USER:-diabetes_user}

read -sp "Senha do usuário: " DB_PASSWORD
echo ""

read -p "Usar usuário postgres padrão? (s/n) [n]: " USE_POSTGRES
USE_POSTGRES=${USE_POSTGRES:-n}

# Criar banco e usuário
if [ "$USE_POSTGRES" = "s" ]; then
    echo "📝 Criando banco de dados '$DB_NAME'..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "⚠️  Banco já existe ou erro ao criar"
    
    read -sp "Senha do usuário postgres: " POSTGRES_PASSWORD
    echo ""
    
    DB_USER="postgres"
    DB_PASSWORD="$POSTGRES_PASSWORD"
    DB_URL="postgresql+psycopg2://postgres:$DB_PASSWORD@localhost:5432/$DB_NAME"
else
    echo "📝 Criando usuário e banco de dados..."
    sudo -u postgres psql << EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF
    
    DB_URL="postgresql+psycopg2://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
fi

# Atualizar .env
echo ""
echo "📝 Atualizando arquivo .env..."

# Remover linha antiga se existir
sed -i '/^DATABASE_URL=/d' .env 2>/dev/null || true

# Adicionar nova configuração
echo "" >> .env
echo "# PostgreSQL" >> .env
echo "DATABASE_URL=$DB_URL" >> .env

echo "✅ PostgreSQL configurado!"
echo ""
echo "📋 Configuração adicionada ao .env:"
echo "   DATABASE_URL=$DB_URL"
echo ""
echo "🔄 Reinicie o servidor para aplicar as mudanças."



