import hashlib
import logging
from typing import List

import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException

from .types import Document, DocumentMetadata


def _generate_document_id(content: str) -> str:
    """Generate a unique ID for a document based on its content."""
    return hashlib.md5(content.encode()).hexdigest()


class VectorStore:
    def __init__(self, collection_name: str, db_path: str):
        self.logger = logging.getLogger(__name__)
        try:
            self.db_path = db_path
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(allow_reset=True, anonymized_telemetry=False),
            )

            try:
                self.collection = self.client.get_collection(collection_name)
                self.logger.info(f"Connected to existing collection: {collection_name}")

            except InvalidCollectionException:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": "cosine",  # Use cosine similarity for distance metric of the HNSW index
                        "hnsw:search_ef": 100,  # Higher value = more accurate search, but slower
                        "hnsw:batch_size": 200,  # Number of vectors to index in a batch, higher = faster indexing
                        "description": "University documents collection",
                    },
                )
                self.logger.info(f"Created new collection: {collection_name}")

        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise

    async def query(self, query_embedding: List[float], k: int) -> List[Document]:
        """Query vector store for similar documents."""
        try:
            count = self.collection.count()
            if count == 0:
                self.logger.warning("Collection is empty")
                return []

            # Query the collection
            results = self.collection.query(
                query_embeddings=query_embedding,  # Pass the embedding directly
                n_results=min(k, count),
                include=[
                    "documents",
                    "metadatas",
                    "distances",
                ],  # Explicitly request all fields
            )

            documents = []
            # Check if we have results and they're not empty
            if (
                results
                and "documents" in results
                and results["documents"]
                and len(results["documents"][0]) > 0
            ):
                for doc, metadata, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    # Convert distance to similarity score (1 - normalized distance)
                    similarity_score = 1.0 - float(distance)

                    # Create DocumentMetadata object from the metadata dictionary based on the fields in `metadata`
                    # The fields might vary based on the metadata provided, so we need to handle this dynamically
                    doc_metadata = DocumentMetadata(**metadata)
                    documents.append(
                        Document(
                            content=doc, metadata=doc_metadata, score=similarity_score
                        )
                    )

                self.logger.info(f"Retrieved {len(documents)} documents")
                if documents:
                    self.logger.debug(f"Top document score: {documents[0].score}")
            else:
                self.logger.info("No matching documents found")
                return []

            return documents

        except Exception as e:
            self.logger.error(f"Vector store query failed: {e}")
            raise

    async def add_documents(
        self, documents: List[Document], embeddings: List[List[float]]
    ):
        """Add documents to the vector store, skipping existing ones."""
        try:
            # Generate unique IDs for documents
            doc_ids = [_generate_document_id(doc.content) for doc in documents]

            # Check which documents already exist
            existing_ids = set()
            try:
                existing_docs = self.collection.get(ids=doc_ids)
                existing_ids = set(existing_docs["ids"])
            except Exception as e:
                self.logger.debug(f"Error checking existing documents: {e}")

            # Filter out existing documents
            new_docs = []
            new_embeddings = []
            new_ids = []
            new_metadata = []

            for doc, embedding, doc_id in zip(documents, embeddings, doc_ids):
                if doc_id not in existing_ids:
                    new_docs.append(doc.content)
                    new_embeddings.append(embedding)
                    new_ids.append(doc_id)

                    # Convert DocumentMetadata to dictionary based on the fields in `doc.metadata`
                    # Append to `new_metadata`
                    new_metadata.append(doc.metadata.__dict__)

            if new_docs:
                self.collection.add(
                    documents=new_docs,
                    embeddings=new_embeddings,
                    metadatas=new_metadata,
                    ids=new_ids,
                )
                self.logger.info(f"Added {len(new_docs)} new documents to collection")
            else:
                self.logger.info("No new documents to add")

        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            raise

    async def get_document_count(self) -> int:
        """Get the total number of documents in the collection."""
        return self.collection.count()

    async def close(self):
        """Close the vector store connection without destroying data."""
        try:
            if hasattr(self, "client"):
                # Don't reset, just remove the references
                self.collection = None
                self.client = None
                self.logger.info("Vector store connection closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing vector store connection: {e}")
            raise
