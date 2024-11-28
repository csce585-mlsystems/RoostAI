# back_end/chatbot/data_ingestion.py
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import asyncio
from pathlib import Path

from roostai.back_end.chatbot.types import Document, DocumentMetadata
from roostai.back_end.chatbot.query_processor import QueryProcessor
from roostai.back_end.chatbot.vector_store import VectorStore
from roostai.back_end.chatbot.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    def _process_metadata(self, metadata: Dict[str, Any]) -> DocumentMetadata:
        """Convert raw metadata dictionary to DocumentMetadata object."""
        return DocumentMetadata(
            url=metadata.get("url", ""),
            department=metadata.get("department"),
            doc_type=metadata.get("doc_type"),
            date_added=datetime.now().isoformat(),
        )

    def _create_documents_from_chunks(
        self, chunks: List[str], metadata: Dict[str, Any]
    ) -> List[Document]:
        """Create Document objects from chunks and metadata."""
        doc_metadata = self._process_metadata(metadata)
        return [
            Document(content=chunk, metadata=doc_metadata, score=None)
            for chunk in chunks
        ]

    async def process_file(self, file_path: str) -> List[Document]:
        """Process a single JSON file and return list of Document objects."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            chunks = data.get("chunks", [])
            metadata = data.get("metadata", {})

            if not chunks:
                logger.warning(f"No chunks found in {file_path}")
                return []

            documents = self._create_documents_from_chunks(chunks, metadata)
            logger.info(f"Processed {len(documents)} chunks from {file_path}")
            return documents

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return []

    async def ingest_documents(self, documents: List[Document]) -> bool:
        """Ingest documents into the vector store."""
        try:
            # Generate embeddings for all documents
            embeddings = [
                self.query_processor.model.encode(doc.content).tolist()
                for doc in documents
            ]

            # Add documents to vector store
            await self.vector_store.add_documents(documents, embeddings)
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

            for file_path in json_files:
                documents = await self.process_file(str(file_path))
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

            logger.info(
                f"Completed ingestion. Total documents processed: {total_documents}"
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

    # TODO: Directory containing your JSON files
    data_directory = ""

    try:
        await ingestion_manager.process_directory(data_directory)

        # Verify ingestion
        doc_count = await ingestion_manager.vector_store.get_document_count()
        logger.info(f"Final document count in database: {doc_count}")

    finally:
        await ingestion_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
