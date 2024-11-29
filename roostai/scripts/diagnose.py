# diagnostic.py
__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import chromadb
import logging
import sqlite3
from chromadb.config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "/home/cc/RoostAI/roostai/data"

def inspect_sqlite_db():
    """Directly inspect the SQLite database."""
    conn = sqlite3.connect(f'{DB_PATH}/chroma.sqlite3')
    cursor = conn.cursor()
    
    # Check collections table
    cursor.execute("SELECT name, id FROM collections;")
    collections = cursor.fetchall()
    logger.info("Collections in SQLite DB:")
    for name, id in collections:
        logger.info(f"Collection Name: {name}, ID: {id}")
        
        # Get segment info for this collection
        cursor.execute("SELECT id, scope FROM segments WHERE collection_id = ?", (id,))
        segments = cursor.fetchall()
        logger.info(f"Segments for collection {name}:")
        for seg_id, scope in segments:
            logger.info(f"  Segment ID: {seg_id}, Scope: {scope}")
            
            # Get embedding count for this segment
            cursor.execute("SELECT COUNT(*) FROM embeddings WHERE segment_id = ?", (seg_id,))
            count = cursor.fetchone()[0]
            logger.info(f"  Embeddings in segment: {count}")

    # Check total embeddings
    cursor.execute("SELECT COUNT(*) FROM embeddings;")
    total_embeddings = cursor.fetchone()[0]
    logger.info(f"\nTotal embeddings in database: {total_embeddings}")

def inspect_chroma_client():
    """Inspect using ChromaDB client."""
    client = chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
        )
    )
    
    collections = client.list_collections()
    logger.info("\nCollections via ChromaDB client:")
    for collection in collections:
        logger.info(f"Collection name: {collection.name}")
        logger.info(f"Collection metadata: {collection.metadata}")
        
        # Try to get some items
        try:
            items = collection.get(limit=1)
            logger.info(f"Sample item from collection: {items}")
        except Exception as e:
            logger.error(f"Error getting items from collection: {e}")

def main():
    logger.info("=== Starting Database Inspection ===")
    
    logger.info("\n=== SQLite Inspection ===")
    inspect_sqlite_db()
    
    logger.info("\n=== ChromaDB Client Inspection ===")
    inspect_chroma_client()

if __name__ == "__main__":
    main()
