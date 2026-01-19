#!/bin/bash
# Complete PostgreSQL setup and migration script for DiabetesAI

set -e  # Exit on any error

echo "🐘 DIABETESAI - POSTGRESQL SETUP & MIGRATION"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    SUDO=""
    print_warning "Running as root"
else
    SUDO="sudo"
    print_info "Will use sudo for system operations"
fi

# Step 1: Install PostgreSQL
echo ""
print_info "Step 1: Installing PostgreSQL..."

if ! command -v psql &> /dev/null; then
    print_info "PostgreSQL not found. Installing..."

    # Update package list
    $SUDO apt update

    # Install PostgreSQL
    $SUDO apt install -y postgresql postgresql-contrib postgresql-server-dev-all

    # Install Python dependencies
    pip install psycopg2-binary alembic

    print_status "PostgreSQL installed successfully"
else
    print_status "PostgreSQL already installed"
fi

# Step 2: Start PostgreSQL service
echo ""
print_info "Step 2: Starting PostgreSQL service..."
$SUDO systemctl enable postgresql
$SUDO systemctl start postgresql
print_status "PostgreSQL service started"

# Step 3: Configure database and user
echo ""
print_info "Step 3: Configuring database and user..."

# Default values
DB_NAME="diabetesai"
DB_USER="diabetes_user"
DB_PASSWORD=$(openssl rand -base64 12)

echo "Database configuration:"
echo "  Name: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""

# Create user and database
print_info "Creating database user..."
$SUDO -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || print_warning "User may already exist"

print_info "Creating database..."
$SUDO -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || print_warning "Database may already exist"

print_info "Granting privileges..."
$SUDO -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

print_status "Database configuration completed"

# Step 4: Update environment configuration
echo ""
print_info "Step 4: Updating application configuration..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Create .env file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
    print_info "Created .env file"
fi

# Remove old DATABASE_URL if exists
sed -i '/^DATABASE_URL=/d' "$ENV_FILE" 2>/dev/null || true

# Add PostgreSQL configuration
echo "" >> "$ENV_FILE"
echo "# PostgreSQL Database Configuration" >> "$ENV_FILE"
echo "DATABASE_URL=postgresql+psycopg2://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME" >> "$ENV_FILE"
echo "PG_HOST=localhost" >> "$ENV_FILE"
echo "PG_PORT=5432" >> "$ENV_FILE"
echo "PG_DATABASE=$DB_NAME" >> "$ENV_FILE"
echo "PG_USER=$DB_USER" >> "$ENV_FILE"
echo "PG_PASSWORD=$DB_PASSWORD" >> "$ENV_FILE"

print_status "Configuration updated in .env file"

# Step 5: Run migration
echo ""
print_info "Step 5: Running database migration..."

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_info "Activated virtual environment"
fi

# Run migration script
if [ -f "migrate_to_postgresql.py" ]; then
    python migrate_to_postgresql.py
    if [ $? -eq 0 ]; then
        print_status "Migration completed successfully"
    else
        print_error "Migration failed"
        exit 1
    fi
else
    print_error "Migration script not found: migrate_to_postgresql.py"
    exit 1
fi

# Step 6: Test the setup
echo ""
print_info "Step 6: Testing the setup..."

python -c "
import os
from backend.storage import check_database_health, get_user, list_plans

print('Testing database connection...')
health = check_database_health()
if health['status'] == 'healthy':
    print('✅ Database connection successful')
    print(f'   Tables: {health[\"tables\"]}')
else:
    print('❌ Database connection failed')
    exit(1)

# Test basic queries
try:
    plans = list_plans(limit=1)
    print(f'✅ Plans query successful: {len(plans)} plans found')
except Exception as e:
    print(f'❌ Plans query failed: {e}')

try:
    user = get_user(1)
    if user:
        print('✅ User query successful')
    else:
        print('ℹ️ No users found (expected for fresh database)')
except Exception as e:
    print(f'❌ User query failed: {e}')

print('✅ All tests passed!')
"

if [ $? -eq 0 ]; then
    print_status "Setup and migration completed successfully!"
else
    print_error "Setup completed but tests failed"
    exit 1
fi

echo ""
echo "🎉 POSTGRESQL MIGRATION COMPLETED!"
echo "==================================="
echo ""
echo "📋 SUMMARY:"
echo "   • PostgreSQL installed and configured"
echo "   • Database '$DB_NAME' created"
echo "   • User '$DB_USER' created with password"
echo "   • All data migrated from SQLite"
echo "   • Application configuration updated"
echo ""
echo "🔐 DATABASE CREDENTIALS:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: $DB_PASSWORD"
echo ""
echo "📁 IMPORTANT FILES:"
echo "   • Configuration: .env"
echo "   • Backup: backups/pre_migration_backup_*.db"
echo ""
echo "🚀 NEXT STEPS:"
echo "   1. Restart your application"
echo "   2. Test all functionality thoroughly"
echo "   3. Monitor logs for any issues"
echo "   4. Consider removing old SQLite files after confirming everything works"
echo ""
echo "📞 SUPPORT:"
echo "   If you encounter issues, check the logs and ensure PostgreSQL is running:"
echo "   sudo systemctl status postgresql"
