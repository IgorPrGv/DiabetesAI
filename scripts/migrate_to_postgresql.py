#!/usr/bin/env python3
"""
Complete migration script from SQLite to PostgreSQL for DiabetesAI.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sqlite3
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database paths
PROJECT_ROOT = Path(__file__).parent
SQLITE_DB = PROJECT_ROOT / "data" / "diabetesai.db"
BACKUP_DIR = PROJECT_ROOT / "backups"

# PostgreSQL configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DATABASE = os.getenv("PG_DATABASE", "diabetesai")
PG_USER = os.getenv("PG_USER", "diabetes_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

def create_backup():
    """Create backup of current SQLite database."""
    logger.info("📦 Creating backup of SQLite database...")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"pre_migration_backup_{timestamp}.db"

    if SQLITE_DB.exists():
        import shutil
        shutil.copy2(SQLITE_DB, backup_file)
        logger.info(f"✅ Backup created: {backup_file}")
        return backup_file
    else:
        logger.error(f"❌ SQLite database not found: {SQLITE_DB}")
        return None

def check_postgresql_connection():
    """Check if PostgreSQL is accessible."""
    logger.info("🔍 Checking PostgreSQL connection...")

    try:
        import psycopg2
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        conn.close()
        logger.info("✅ PostgreSQL connection successful")
        return True
    except ImportError:
        logger.error("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        logger.info("💡 Make sure PostgreSQL is running and credentials are correct")
        return False

def extract_sqlite_data() -> Dict[str, List[Dict[str, Any]]]:
    """Extract all data from SQLite database."""
    logger.info("📤 Extracting data from SQLite...")

    data = {}

    if not SQLITE_DB.exists():
        logger.error(f"SQLite database not found: {SQLITE_DB}")
        return data

    try:
        conn = sqlite3.connect(str(SQLITE_DB))
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            logger.info(f"   Extracting table: {table}")
            cursor.execute(f"SELECT * FROM {table}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # Convert to dict format
            table_data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]

                    # Handle JSON fields that might be stored as strings
                    if col in ['request_payload', 'response_payload', 'profile_payload'] and isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except:
                            pass  # Keep as string if not valid JSON

                    row_dict[col] = value
                table_data.append(row_dict)

            data[table] = table_data
            logger.info(f"   ✅ {table}: {len(table_data)} records extracted")

        conn.close()
        return data

    except Exception as e:
        logger.error(f"❌ Failed to extract SQLite data: {e}")
        return {}

def create_postgresql_tables():
    """Create tables in PostgreSQL with proper types."""
    logger.info("🏗️ Creating PostgreSQL tables...")

    try:
        import psycopg2
        from psycopg2.extras import Json

        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()

        # Drop existing tables if they exist
        cursor.execute("""
            DROP TABLE IF EXISTS consumed_meals CASCADE;
            DROP TABLE IF EXISTS plans CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
            DROP TABLE IF EXISTS auth_users CASCADE;
        """)

        # Create auth_users table
        cursor.execute("""
            CREATE TABLE auth_users (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL
            );
        """)

        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                auth_user_id INTEGER NOT NULL UNIQUE REFERENCES auth_users(id),
                profile_payload JSONB
            );
        """)

        # Create plans table
        cursor.execute("""
            CREATE TABLE plans (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                request_payload JSONB NOT NULL,
                response_payload JSONB NOT NULL
            );
        """)

        # Create consumed_meals table
        cursor.execute("""
            CREATE TABLE consumed_meals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                plan_id INTEGER REFERENCES plans(id) ON DELETE SET NULL,
                meal_type VARCHAR(100) NOT NULL,
                meal_name TEXT,
                consumed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );
        """)

        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_plans_created_at ON plans(created_at);")
        cursor.execute("CREATE INDEX idx_users_auth_user_id ON users(auth_user_id);")
        cursor.execute("CREATE INDEX idx_consumed_meals_user_id ON consumed_meals(user_id);")
        cursor.execute("CREATE INDEX idx_consumed_meals_plan_id ON consumed_meals(plan_id);")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("✅ PostgreSQL tables created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create PostgreSQL tables: {e}")
        return False

def migrate_data(sqlite_data: Dict[str, List[Dict[str, Any]]]):
    """Migrate data from SQLite to PostgreSQL."""
    logger.info("🚀 Starting data migration...")

    try:
        import psycopg2
        from psycopg2.extras import Json

        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()

        # Migration order matters due to foreign keys
        migration_order = ['auth_users', 'users', 'plans', 'consumed_meals']

        for table in migration_order:
            if table not in sqlite_data:
                logger.warning(f"⚠️ Table {table} not found in SQLite data, skipping")
                continue

            records = sqlite_data[table]
            if not records:
                logger.info(f"ℹ️ Table {table} is empty, skipping")
                continue

            logger.info(f"   Migrating {len(records)} records to {table}...")

            for record in records:
                try:
                    if table == 'auth_users':
                        cursor.execute("""
                            INSERT INTO auth_users (id, created_at, email, password_hash)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            record['id'],
                            record['created_at'],
                            record['email'],
                            record['password_hash']
                        ))

                    elif table == 'users':
                        cursor.execute("""
                            INSERT INTO users (id, created_at, auth_user_id, profile_payload)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            record['id'],
                            record['created_at'],
                            record['auth_user_id'],
                            Json(record.get('profile_payload'))
                        ))

                    elif table == 'plans':
                        cursor.execute("""
                            INSERT INTO plans (id, created_at, request_payload, response_payload)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            record['id'],
                            record['created_at'],
                            Json(record['request_payload']),
                            Json(record['response_payload'])
                        ))

                    elif table == 'consumed_meals':
                        cursor.execute("""
                            INSERT INTO consumed_meals (id, user_id, plan_id, meal_type, meal_name, consumed_at, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            record['id'],
                            record['user_id'],
                            record.get('plan_id'),
                            record['meal_type'],
                            record.get('meal_name'),
                            record.get('consumed_at', record.get('created_at')),
                            record.get('notes')
                        ))

                except Exception as e:
                    logger.error(f"❌ Failed to migrate record {record.get('id', 'unknown')} in {table}: {e}")
                    continue

            logger.info(f"   ✅ {table}: {len(records)} records migrated")

        # Reset sequences to correct values
        cursor.execute("SELECT setval('auth_users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM auth_users));")
        cursor.execute("SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));")
        cursor.execute("SELECT setval('plans_id_seq', (SELECT COALESCE(MAX(id), 1) FROM plans));")
        cursor.execute("SELECT setval('consumed_meals_id_seq', (SELECT COALESCE(MAX(id), 1) FROM consumed_meals));")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("✅ Data migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Data migration failed: {e}")
        return False

def update_application_config():
    """Update application configuration to use PostgreSQL."""
    logger.info("⚙️ Updating application configuration...")

    # Create DATABASE_URL for PostgreSQL
    pg_url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

    # Update environment if .env file exists
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()

        # Remove old DATABASE_URL
        lines = [line for line in lines if not line.startswith('DATABASE_URL=')]

        # Add new DATABASE_URL
        lines.append(f'\n# PostgreSQL Database\n')
        lines.append(f'DATABASE_URL={pg_url}\n')

        # Write back
        with open(env_file, 'w') as f:
            f.writelines(lines)

        logger.info(f"✅ Updated .env file with PostgreSQL URL")
    else:
        logger.warning("⚠️ .env file not found, please set DATABASE_URL manually")

    # Also create a backup of the old configuration
    config_backup = PROJECT_ROOT / ".env.sqlite_backup"
    if env_file.exists() and not config_backup.exists():
        import shutil
        shutil.copy2(env_file, config_backup)
        logger.info(f"✅ Created backup of old configuration: {config_backup}")

def test_migration():
    """Test that the migration was successful."""
    logger.info("🧪 Testing migration...")

    try:
        import psycopg2
        from psycopg2.extras import Json

        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()

        # Test counts
        cursor.execute("SELECT COUNT(*) FROM auth_users")
        auth_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM plans")
        plans_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM consumed_meals")
        meals_count = cursor.fetchone()[0]

        conn.close()

        logger.info("✅ Migration test results:")
        logger.info(f"   auth_users: {auth_count} records")
        logger.info(f"   users: {users_count} records")
        logger.info(f"   plans: {plans_count} records")
        logger.info(f"   consumed_meals: {meals_count} records")

        # Compare with SQLite data
        sqlite_data = extract_sqlite_data()
        sqlite_counts = {table: len(records) for table, records in sqlite_data.items()}

        success = True
        for table in ['auth_users', 'users', 'plans', 'consumed_meals']:
            pg_count = locals()[f"{table.replace('_', '')}_count"]
            sqlite_count = sqlite_counts.get(table, 0)
            if pg_count != sqlite_count:
                logger.error(f"❌ Count mismatch for {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                success = False
            else:
                logger.info(f"✅ {table} count matches: {pg_count} records")

        return success

    except Exception as e:
        logger.error(f"❌ Migration test failed: {e}")
        return False

def main():
    """Main migration function."""
    print("🚀 DIABETESAI DATABASE MIGRATION: SQLite → PostgreSQL")
    print("=" * 60)

    # Step 1: Create backup
    backup_file = create_backup()
    if not backup_file:
        logger.error("❌ Backup failed, aborting migration")
        return False

    # Step 2: Check PostgreSQL connection
    if not check_postgresql_connection():
        logger.error("❌ PostgreSQL connection check failed, aborting migration")
        return False

    # Step 3: Extract SQLite data
    sqlite_data = extract_sqlite_data()
    if not sqlite_data:
        logger.error("❌ Failed to extract SQLite data, aborting migration")
        return False

    # Step 4: Create PostgreSQL tables
    if not create_postgresql_tables():
        logger.error("❌ Failed to create PostgreSQL tables, aborting migration")
        return False

    # Step 5: Migrate data
    if not migrate_data(sqlite_data):
        logger.error("❌ Data migration failed, aborting")
        return False

    # Step 6: Test migration
    if not test_migration():
        logger.error("❌ Migration test failed")
        return False

    # Step 7: Update configuration
    update_application_config()

    print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ SQLite data migrated to PostgreSQL")
    print("✅ Application configuration updated")
    print(f"✅ Backup created: {backup_file}")
    print("\n📋 NEXT STEPS:")
    print("   1. Restart your application")
    print("   2. Test all functionality")
    print("   3. Remove old SQLite file if everything works")
    print("   4. Update any hardcoded database references")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
