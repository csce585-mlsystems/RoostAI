import hashlib
import logging
from typing import List

import chromadb
from chromadb import Settings
from chromadb.errors import InvalidCollectionException

from .types import Document


class VectorStore:
    def __init__(self, collection_name: str):
        self.logger = logging.getLogger(__name__)
        try:
            self.client = chromadb.PersistentClient(path="./roostai/front_end/data", settings=Settings(allow_reset=True))
            try:
                self.collection = self.client.get_collection(collection_name)
                self.logger.info(f"Connected to existing collection: {collection_name}")
            except InvalidCollectionException:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "University documents collection"}
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
                query_embeddings=[query_embedding],
                n_results=min(k, count)
            )

            documents = []
            if results and results['documents'] and len(results['documents'][0]):
                for idx, (content, metadata, distance) in enumerate(zip(
                        results['documents'][0],
                        results['metadatas'][0],
                        results['distances'][0]
                )):
                    # Convert distance to similarity score (1 - normalized distance)
                    similarity_score = 1.0 - float(distance)
                    documents.append(Document(
                        content=content,
                        metadata=metadata,
                        score=similarity_score
                    ))

                self.logger.info(f"Retrieved {len(documents)} documents")
                self.logger.debug(f"Top document score: {documents[0].score if documents else 'N/A'}")

            return documents

        except Exception as e:
            self.logger.error(f"Vector store query failed: {e}")
            raise

    def _generate_document_id(self, content: str) -> str:
        """Generate a unique ID for a document based on its content."""
        return hashlib.md5(content.encode()).hexdigest()

    async def add_documents(self, documents: List[Document], embeddings: List[List[float]]):
        """Add documents to the vector store, skipping existing ones."""
        try:
            # Generate unique IDs for documents
            doc_ids = [self._generate_document_id(doc.content) for doc in documents]

            # Check which documents already exist
            existing_ids = set()
            try:
                existing_docs = self.collection.get(ids=doc_ids)
                existing_ids = set(existing_docs['ids'])
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
                    new_metadata.append(doc.metadata)

            if new_docs:
                self.collection.add(
                    documents=new_docs,
                    metadatas=new_metadata,
                    embeddings=new_embeddings,
                    ids=new_ids
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

    def _initialize_store(self):
        """Initialize the vector store connection."""
        try:
            self.client = chromadb.PersistentClient(path="./roostai/front_end/data", settings=Settings(allow_reset=True))
            try:
                self.collection = self.client.get_collection(self.collection_name)
                self.logger.info(f"Connected to existing collection: {self.collection_name}")
            except InvalidCollectionException:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "University documents collection"}
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise

    async def close(self):
        """Close the vector store connection."""
        try:
            if self.client:
                self.client.reset()
                self.client = None
                self.collection = None
                self.logger.info("Vector store connection closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing vector store connection: {e}")
            raise