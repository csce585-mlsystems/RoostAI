import os

__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import asyncio
import logging
import time

from roostai.back_end.chatbot.config import Config
from roostai.back_end.chatbot.llm_manager import LLMManager
from roostai.back_end.chatbot.quality_checker import QualityChecker
from roostai.back_end.chatbot.query_processor import QueryProcessor
from roostai.back_end.chatbot.reranker import Reranker
from roostai.back_end.chatbot.vector_store import VectorStore

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Add a function to verify database path
def verify_db_path(db_path: str) -> bool:
    """Verify that the database path exists and contains the expected files."""
    if not os.path.exists(db_path):
        logger.error(f"Database directory does not exist: {db_path}")
        return False

    # Check for chroma.sqlite3
    sqlite_path = os.path.join(db_path, "chroma.sqlite3")
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database file not found at: {sqlite_path}")
        return False

    logger.info(f"Found database at: {sqlite_path}")
    return True


class UniversityChatbot:
    def __init__(self):
        self.config = Config.load_config()

        # Set the absolute path to the database
        db_path = "/home/cc/RoostAI/roostai/data"

        # Verify database path
        if not verify_db_path(db_path):
            raise ValueError(f"Invalid database path: {db_path}")

        self.config.vector_db.db_path = db_path
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"Initializing with database path: {db_path}")

        self.query_processor = QueryProcessor(
            model_name=self.config.model.embedding_model
        )

        try:
            self.vector_store = VectorStore(
                collection_name=self.config.vector_db.collection_name,
                db_path=self.config.vector_db.db_path,
            )
            # Immediately verify we can access the database
            asyncio.create_task(self._verify_db_access())

        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            raise

        self.reranker = Reranker(model_name=self.config.model.cross_encoder_model)

        self.quality_checker = QualityChecker(
            min_score=self.config.thresholds.quality_min_score,
            min_docs=self.config.thresholds.quality_min_docs,
        )

        self.llm_manager = LLMManager(
            model_name=self.config.model.llm_model,
            config=self.config.llm,
            llm_model=self.config.model.llm_model,
        )

    async def _verify_db_access(self):
        """Verify that we can access the database and log its contents."""
        try:
            count = await self.vector_store.get_document_count()
            self.logger.info(
                f"Successfully connected to database. Document count: {count}"
            )

            # Try to get a sample document if count > 0
            if count > 0:
                query_embedding = self.query_processor.model.encode("test").tolist()
                docs = await self.vector_store.query(query_embedding, k=1)
                if docs:
                    self.logger.info("Successfully retrieved a sample document")
                else:
                    self.logger.warning("No documents retrieved in sample query")
        except Exception as e:
            self.logger.error(f"Database verification failed: {e}")
            raise

    async def process_query(self, query: str, verbose: bool = False) -> str:
        """Process a query with optional verbose output for debugging."""
        try:
            if not query.strip():
                return "Please provide a valid question."

            if verbose:
                logger.info(f"Processing query: {query}")

            cleaned_query, query_embedding = await self.query_processor.process_query(
                query
            )

            documents = await self.vector_store.query(
                query_embedding, k=self.config.vector_db.top_k
            )

            if verbose:
                logger.info(f"Retrieved {len(documents)} initial documents")
                if documents:
                    logger.info("Top 3 initial documents:")
                    for i, doc in enumerate(documents[:3], 1):
                        logger.info(f"\n{i}. Score: {doc.score:.4f}")
                        logger.info(f"URL: {doc.metadata.url}")
                        logger.info(f"Content: {doc.content[:200]}...")

            if not documents:
                return (
                    "I don't have any relevant information to answer your question. "
                    "Please try asking something about USC."
                )

            reranked_docs = await self.reranker.rerank(
                cleaned_query,
                documents,
                threshold=self.config.thresholds.reranking_threshold,
            )

            if verbose:
                logger.info(f"\nReranked documents: {len(reranked_docs)}")
                if reranked_docs:
                    logger.info("Top 3 reranked documents:")
                    for i, doc in enumerate(reranked_docs[:3], 1):
                        logger.info(f"\n{i}. Score: {doc.score:.4f}")
                        logger.info(f"URL: {doc.metadata.url}")
                        logger.info(f"Content: {doc.content[:200]}...")

            result = await self.quality_checker.check_quality(
                cleaned_query, reranked_docs
            )

            if verbose:
                logger.info(f"\nQuality score: {result.quality_score:.4f}")

            if result.quality_score < self.config.thresholds.quality_min_score:
                return (
                    "I apologize, but I don't have enough confident information to "
                    "provide a good answer to your question. Please try rephrasing or "
                    "asking about a different topic related to USC."
                )

            response = await self.llm_manager.generate_response(cleaned_query, result)

            return response or "I apologize, but I couldn't generate a response."

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return (
                "I apologize, but I encountered an error processing your query. "
                "Please try again or rephrase your question."
            )

    async def get_document_count(self) -> int:
        """Get the total number of documents in the system."""
        return await self.vector_store.get_document_count()

    async def cleanup(self):
        """Cleanup all resources."""
        tasks = []
        if hasattr(self, "vector_store"):
            tasks.append(self.vector_store.close())
        if hasattr(self, "llm_manager"):
            tasks.append(self.llm_manager.close())
        if hasattr(self, "query_processor"):
            self.query_processor.clear_cache()

        if tasks:
            await asyncio.gather(*tasks)


async def main():
    chatbot = UniversityChatbot()

    try:
        # First, let's check the document count
        doc_count = await chatbot.get_document_count()
        logger.info(f"\nTotal documents in database: {doc_count}")

        if doc_count == 0:
            logger.error("No documents found in the database. Exiting.")
            return

        # Test queries that cover different aspects of USC
        test_queries = [
            "What are the admission requirements for USC?",
            # "Tell me about the Computer Science department at USC",
            # "What sports teams does USC have?",
            # "What dining options are available on campus?",
            # "What is the history of USC?",
            # "What research centers does USC have?",
            # "What student organizations are available at USC?",
            # "What are the housing options for freshmen at USC?",
            # "Tell me about USC's library system",
            # "What financial aid options are available at USC?",
        ]

        logger.info("\nStarting query tests...")

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n=== Query {i} ===")
            logger.info(f"Q: {query}")

            try:
                start_time = time.time()
                response = await chatbot.process_query(query, verbose=True)
                end_time = time.time()

                logger.info(f"\nA: {response}")
                logger.info(f"Time taken: {end_time - start_time:.2f} seconds")
                logger.info("=" * 80)

            except Exception as e:
                logger.error(f"Error processing query {i}: {e}")
                continue

            # Add a small delay between queries to avoid rate limiting
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")

    finally:
        if "chatbot" in locals():
            await chatbot.cleanup()
            logger.info("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())
