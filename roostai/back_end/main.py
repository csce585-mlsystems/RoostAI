import asyncio
import logging
import os
from typing import List

from roostai.back_end.chatbot.llm_manager import LLMManager
from roostai.back_end.chatbot.quality_checker import QualityChecker
from roostai.back_end.chatbot.query_processor import QueryProcessor
from roostai.back_end.chatbot.reranker import Reranker
from roostai.back_end.chatbot.types import Document, DocumentMetadata
from roostai.back_end.chatbot.vector_store import VectorStore
from roostai.back_end.chatbot.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniversityChatbot:
    def __init__(self):
        self.config = Config.load_config()
        self.logger = logging.getLogger(__name__)

        self.query_processor = QueryProcessor(
            model_name=self.config.model.embedding_model
        )

        self.vector_store = VectorStore(
            collection_name=self.config.vector_db.collection_name,
            db_path=self.config.vector_db.db_path
        )

        self.reranker = Reranker(
            model_name=self.config.model.cross_encoder_model
        )

        self.quality_checker = QualityChecker(
            min_score=self.config.thresholds.quality_min_score,
            min_docs=self.config.thresholds.quality_min_docs
        )

        self.llm_manager = LLMManager(
            model_name=self.config.model.llm_model,
            config=self.config.llm,
            llm_model=self.config.model.llm_model
        )

    async def process_query(self, query: str) -> str:
        try:
            if not query.strip():
                return "Please provide a valid question."

            cleaned_query, query_embedding = await self.query_processor.process_query(query)

            documents = await self.vector_store.query(
                query_embedding,
                k=self.config.vector_db.top_k
            )

            if not documents:
                return ("I don't have any relevant information to answer your question. "
                        "Please try asking something about USC.")

            reranked_docs = await self.reranker.rerank(
                cleaned_query,
                documents,
                threshold=self.config.thresholds.reranking_threshold
            )

            result = await self.quality_checker.check_quality(cleaned_query, reranked_docs)

            if result.quality_score < self.config.thresholds.quality_min_score:
                return ("I apologize, but I don't have enough confident information to "
                        "provide a good answer to your question. Please try rephrasing or "
                        "asking about a different topic related to USC.")

            response = await self.llm_manager.generate_response(cleaned_query, result)

            return response or "I apologize, but I couldn't generate a response."

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return ("I apologize, but I encountered an error processing your query. "
                    "Please try again or rephrase your question.")

    async def add_documents(self, documents: List[Document]):
        """Add documents to the vector store."""
        try:
            # Generate embeddings for all documents
            embeddings = [
                self.query_processor.model.encode(doc.content).tolist()
                for doc in documents
            ]
            await self.vector_store.add_documents(documents, embeddings)
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    async def get_document_count(self) -> int:
        """Get the total number of documents in the system."""
        return await self.vector_store.get_document_count()

    async def cleanup(self):
        """Cleanup all resources."""
        pass
        tasks = []
        if hasattr(self, 'vector_store'):
            tasks.append(self.vector_store.close())
        if hasattr(self, 'llm_manager'):
            tasks.append(self.llm_manager.close())
        if hasattr(self, 'query_processor'):
            self.query_processor.clear_cache()

        if tasks:
            await asyncio.gather(*tasks)


async def main():
    if not os.path.exists("data"):
        os.makedirs("data")

    chatbot = UniversityChatbot()

    sample_url = DocumentMetadata(
            url="https://sample_url"
        )

    # More relevant test documents
    test_docs = [
        Document(
            content="The USC Computer Science program requires a minimum GPA of 3.0 for admission. "
                    "Applicants must also complete prerequisite courses in mathematics and programming.",
            metadata=sample_url
        ),
        Document(
            content="Computer Science admission requirements include: SAT/ACT scores, "
                    "letters of recommendation, and a strong background in mathematics.",
            metadata=sample_url
        ),
        Document(
            content="Transfer students applying to the Computer Science program must have "
                    "completed calculus I and have a minimum GPA of 3.0 in all prior coursework.",
            metadata=sample_url
        )
    ]

    # Add documents
    success = await chatbot.add_documents(test_docs)
    logger.info(f"Documents added successfully: {success}")

    # Verify document count
    doc_count = await chatbot.get_document_count()
    logger.info(f"Total documents in database: {doc_count}")

    # Test query
    query = "What are the admission requirements for the Computer Science program?"
    query = "Who is the student body president at USC?"

    logger.info(f"Processing query: {query}")
    response = await chatbot.process_query(query)
    print("\nResponse:", response)

    await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
