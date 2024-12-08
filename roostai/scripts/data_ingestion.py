__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import json
import logging
import shutil
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Set
import asyncio
from tqdm import tqdm

from roostai.back_end.chatbot.types import Document, DocumentMetadata
from roostai.back_end.chatbot.query_processor import QueryProcessor
from roostai.back_end.chatbot.vector_store import VectorStore
from roostai.back_end.chatbot.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DuplicateTracker:
    def __init__(self):
        self.content_hashes: Set = set()
        self.duplicate_counts: Dict[str, int] = defaultdict(int)
        self.duplicate_sources: Dict[str, List[str]] = defaultdict(list)
        self.total_chunks = 0
        self.unique_chunks = 0

    def is_duplicate(self, content: str, source_url: str) -> bool:
        """Check if content is duplicate and track statistics."""
        self.total_chunks += 1
        content_hash = hash(content.strip())

        if content_hash in self.content_hashes:
            self.duplicate_counts[source_url] += 1
            return True

        self.content_hashes.add(content_hash)
        self.unique_chunks += 1
        return False

    def print_statistics(self):
        """Print duplicate statistics."""
        logger.info("\n=== Duplicate Statistics ===")
        logger.info(f"Total chunks processed: {self.total_chunks}")
        logger.info(f"Unique chunks: {self.unique_chunks}")
        logger.info(f"Duplicate chunks: {self.total_chunks - self.unique_chunks}")

        if self.duplicate_counts:
            logger.info("\nSources with duplicates:")
            for url, count in sorted(
                self.duplicate_counts.items(), key=lambda x: x[1], reverse=True
            ):
                logger.info(f"  {url}: {count} duplicates")


def _create_documents_from_chunks(
    chunks: List[str], metadata: Dict[str, Any], duplicate_tracker: DuplicateTracker
) -> List[Document]:
    """Create Document objects from chunks and metadata, excluding duplicates."""
    doc_metadata = DocumentMetadata(**metadata)
    unique_documents = []

    for chunk in chunks:
        if not duplicate_tracker.is_duplicate(chunk, metadata.get("url", "unknown")):
            unique_documents.append(
                Document(content=chunk, metadata=doc_metadata, score=None)
            )

    return unique_documents


async def process_file(
    file_path: str, duplicate_tracker: DuplicateTracker
) -> List[Document]:
    """Process a single JSON file and return list of unique Document objects."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chunks = data.get("chunks", [])
        metadata = data.get("metadata", {})

        # Handle URL field
        if "url" not in metadata:
            if "source_url" in metadata:
                metadata["url"] = metadata["source_url"]
                metadata.pop("source_url")
            else:
                logger.warning(f"No URL found in metadata for {file_path}")
                return []

        if not chunks:
            logger.warning(f"No chunks found in {file_path}")
            return []

        documents = _create_documents_from_chunks(chunks, metadata, duplicate_tracker)
        logger.info(f"Processed {len(documents)} unique chunks from {file_path}")
        return documents

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return []


class DataIngestionManager:
    def __init__(self, config: Config):
        """Initialize the data ingestion manager."""
        self.config = config

        self.query_processor = QueryProcessor(
            model_name=self.config.model.embedding_model
        )
        self.vector_store = VectorStore(
            collection_name=self.config.vector_db.collection_name,
            db_path=self.config.vector_db.db_path,
        )
        self.duplicate_tracker = DuplicateTracker()

    async def ingest_documents(self, documents: List[Document]) -> bool:
        """Ingest documents into the vector store."""
        try:
            if not documents:
                return True  # Nothing to ingest

            logger.info(f"Generating embeddings for {len(documents)} documents...")

            # Generate embeddings for all documents
            embeddings = []
            for doc in tqdm(documents, desc="Generating embeddings"):
                embedding = self.query_processor.model.encode(doc.content).tolist()
                embeddings.append(embedding)

            logger.info("Adding documents to vector store...")
            # Add documents to vector store
            await self.vector_store.add_documents(documents, embeddings)
            logger.info(
                f"Successfully added {len(documents)} documents to vector store"
            )
            return True

        except Exception as e:
            logger.error(f"Error ingesting documents: {e}")
            return False

    async def process_directory(
        self, directory_path: str, batch_size: int = 100
    ) -> None:
        """Process all JSON files in a directory and ingest them into the vector store."""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")

            # Get all JSON files
            json_files = list(directory.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files to process")

            # Process files in batches
            current_batch: List[Document] = []
            total_documents = 0

            # Use tqdm for progress bar
            for file_path in tqdm(json_files, desc="Processing files"):
                documents = await process_file(str(file_path), self.duplicate_tracker)
                current_batch.extend(documents)

                # If batch is full, process it
                if len(current_batch) >= batch_size:
                    success = await self.ingest_documents(current_batch)
                    if success:
                        total_documents += len(current_batch)
                        logger.info(
                            f"Successfully ingested batch. Total documents: {total_documents}"
                        )
                    current_batch = []

            # Process remaining documents
            if current_batch:
                success = await self.ingest_documents(current_batch)
                if success:
                    total_documents += len(current_batch)

            # Print final statistics
            self.duplicate_tracker.print_statistics()
            logger.info(
                f"Completed ingestion. Total unique documents processed: {total_documents}"
            )

        except Exception as e:
            logger.error(f"Error processing directory: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources."""
        await self.vector_store.close()
        self.query_processor.clear_cache()


async def main():
    """Main function to run the data ingestion process."""
    config = Config.load_config()
    ingestion_manager = DataIngestionManager(config)
    # data_directory = "/home/cc/chunks_and_metadata"

    
    
    data_directories = [("/home/cc/chunks_and_metadata_fixed_size_token_chunking/", "/home/cc/v3_token_chunking"),
                        ("/home/cc/chunks_and_metadata_semantic_chunking_95_threshold/", "/home/cc/v3_95_thresh"),
                        ("/home/cc/chunks_and_metadata_semantic_chunking_50_threshold/", "home/cc/v3_50_thresh"),
                        ("/home/cc/chunks_and_metadata_sentence_splitting_chunking/", "/home/cc/v3_sentence_chunking")] 
    for data_directory, output_path in data_directories:
      ingestion_manager.config.vector_db.db_path = output_path
      try:
          logger.info(f"Starting ingestion from directory: {data_directory}")
          logger.info(f"Using database path: {config.vector_db.db_path}")
          await ingestion_manager.process_directory(data_directory)

          # Verify ingestion
          doc_count = await ingestion_manager.vector_store.get_document_count()
          logger.info(f"Final document count in database: {doc_count}")
      except Exception as e:
          logger.error(f"Fatal error during ingestion: {e}")
          raise
      finally:
          await ingestion_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
