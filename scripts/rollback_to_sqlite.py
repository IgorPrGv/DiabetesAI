#!/usr/bin/env python3
"""
Rollback script to restore SQLite database from PostgreSQL migration.
"""

import os
import logging
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent
BACKUP_DIR = PROJECT_ROOT / "backups"
SQLITE_DB = PROJECT_ROOT / "data" / "diabetesai.db"
ENV_FILE = PROJECT_ROOT / ".env"

def find_latest_backup():
    """Find the most recent backup file."""
    if not BACKUP_DIR.exists():
        return None

    backup_files = list(BACKUP_DIR.glob("pre_migration_backup_*.db"))
    if not backup_files:
        return None

    # Return the most recent backup
    return max(backup_files, key=lambda x: x.stat().st_mtime)

def rollback_database():
    """Rollback to SQLite by restoring from backup."""
    logger.info("🔄 Starting rollback to SQLite...")

    # Find latest backup
    backup_file = find_latest_backup()
    if not backup_file:
        logger.error("❌ No backup file found for rollback")
        return False

    logger.info(f"📦 Found backup: {backup_file}")

    try:
        # Ensure data directory exists
        SQLITE_DB.parent.mkdir(parents=True, exist_ok=True)

        # Restore backup
        shutil.copy2(backup_file, SQLITE_DB)
        logger.info(f"✅ Database restored from backup: {SQLITE_DB}")

        # Verify restoration
        if SQLITE_DB.exists():
            size_mb = SQLITE_DB.stat().st_size / (1024 * 1024)
            logger.info(".2f"        else:
            logger.error("❌ Database file not found after restoration")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Failed to rollback database: {e}")
        return False

def rollback_configuration():
    """Rollback application configuration to use SQLite."""
    logger.info("⚙️ Rolling back application configuration...")

    if not ENV_FILE.exists():
        logger.warning("⚠️ .env file not found, nothing to rollback")
        return True

    try:
        # Read current configuration
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()

        # Remove PostgreSQL configuration
        new_lines = []
        skip_block = False

        for line in lines:
            if line.strip() == "# PostgreSQL Database Configuration":
                skip_block = True
                continue
            elif skip_block and line.strip().startswith("#"):
                continue
            elif skip_block and line.strip() == "":
                skip_block = False
                continue
            elif skip_block and any(key in line for key in ["DATABASE_URL=", "PG_HOST=", "PG_PORT=", "PG_DATABASE=", "PG_USER=", "PG_PASSWORD="]):
                continue
            else:
                skip_block = False
                new_lines.append(line)

        # Add SQLite configuration
        if not any("DATABASE_URL=" in line for line in new_lines):
            new_lines.append(f"\n# SQLite Database (rolled back)\n")
            new_lines.append(f"DATABASE_URL=sqlite:///{SQLITE_DB}\n")

        # Write back
        with open(ENV_FILE, 'w') as f:
            f.writelines(new_lines)

        logger.info("✅ Configuration rolled back to SQLite")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to rollback configuration: {e}")
        return False

def test_rollback():
    """Test that the rollback was successful."""
    logger.info("🧪 Testing rollback...")

    try:
        # Import here to use updated configuration
        import sys
        import importlib

        # Remove storage from cache to reload with new config
        if 'storage' in sys.modules:
            del sys.modules['storage']

        from backend.storage import check_database_health, get_user, list_plans

        # Test database health
        health = check_database_health()
        if health['status'] == 'healthy':
            logger.info("✅ SQLite database connection successful")
            logger.info(f"   Tables: {health['tables']}")
        else:
            logger.error(f"❌ Database health check failed: {health.get('error', 'Unknown error')}")
            return False

        # Test basic queries
        try:
            plans = list_plans(limit=1)
            logger.info(f"✅ Plans query successful: {len(plans)} plans found")
        except Exception as e:
            logger.error(f"❌ Plans query failed: {e}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Rollback test failed: {e}")
        return False

def main():
    """Main rollback function."""
    print("🔄 DIABETESAI DATABASE ROLLBACK: PostgreSQL → SQLite")
    print("=" * 55)

    # Step 1: Rollback database
    if not rollback_database():
        logger.error("❌ Database rollback failed")
        return False

    # Step 2: Rollback configuration
    if not rollback_configuration():
        logger.error("❌ Configuration rollback failed")
        return False

    # Step 3: Test rollback
    if not test_rollback():
        logger.error("❌ Rollback test failed")
        return False

    print("\n🎉 ROLLBACK COMPLETED SUCCESSFULLY!")
    print("=" * 55)
    print("✅ SQLite database restored from backup")
    print("✅ Application configuration updated")
    print("\n📋 SUMMARY:")
    print("   • Application is now using SQLite again")
    print("   • All data from the backup is available")
    print("   • PostgreSQL data remains intact for reference")

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
