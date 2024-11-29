# verify_db.py
__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
import sqlite3
import logging
from pathlib import Path
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/home/cc/RoostAI/roostai/data/chroma.sqlite3"

def backup_database():
    """Create a backup of the current database."""
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    logger.info(f"Created backup at: {backup_path}")
    return backup_path

def check_database_integrity():
    """Check the integrity of the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        logger.info("Checking database integrity...")
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        logger.info(f"Integrity check result: {result}")

        # Get detailed table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            logger.info(f"\nAnalyzing table: {table_name}")
            
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            logger.info(f"Columns: {columns}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            logger.info(f"Row count: {count}")
            
            # Get sample data if table has rows
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                sample = cursor.fetchone()
                logger.info(f"Sample row: {sample}")

    except Exception as e:
        logger.error(f"Error during integrity check: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Create backup first
    backup_path = backup_database()
    
    # Check integrity
    check_database_integrity()
