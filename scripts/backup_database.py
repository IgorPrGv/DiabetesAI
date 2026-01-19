#!/usr/bin/env python3
"""
Database backup script for DiabetesAI SQLite database.
"""

import shutil
import os
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_FILE = DATA_DIR / "diabetesai.db"
BACKUP_DIR = PROJECT_ROOT / "backups"

def create_backup():
    """Create a timestamped backup of the database."""
    try:
        # Ensure backup directory exists
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        if not DATABASE_FILE.exists():
            logger.error(f"Database file not found: {DATABASE_FILE}")
            return False

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"diabetesai_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename

        # Create backup
        shutil.copy2(DATABASE_FILE, backup_path)

        # Get file sizes
        original_size = DATABASE_FILE.stat().st_size
        backup_size = backup_path.stat().st_size

        logger.info("✅ Database backup created successfully!"        logger.info(f"   Original: {DATABASE_FILE} ({original_size} bytes)")
        logger.info(f"   Backup: {backup_path} ({backup_size} bytes)")

        # Clean up old backups (keep last 10)
        cleanup_old_backups()

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create database backup: {e}")
        return False

def cleanup_old_backups():
    """Remove old backups, keeping only the most recent 10."""
    try:
        backup_files = sorted(
            BACKUP_DIR.glob("diabetesai_backup_*.db"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if len(backup_files) > 10:
            files_to_remove = backup_files[10:]
            for old_file in files_to_remove:
                old_file.unlink()
                logger.info(f"🗑️ Removed old backup: {old_file.name}")

            logger.info(f"✅ Kept {min(10, len(backup_files))} most recent backups")

    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {e}")

def list_backups():
    """List all available backups."""
    try:
        if not BACKUP_DIR.exists():
            print("No backup directory found.")
            return

        backup_files = list(BACKUP_DIR.glob("diabetesai_backup_*.db"))
        if not backup_files:
            print("No backups found.")
            return

        print(f"📁 Found {len(backup_files)} database backups:")
        print("-" * 60)

        for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            print("25"
    except Exception as e:
        print(f"Error listing backups: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_backups()
    else:
        success = create_backup()
        sys.exit(0 if success else 1)
