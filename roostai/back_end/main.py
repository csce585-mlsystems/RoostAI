# back_end/main.py
import os
from typing import Optional, Dict, Any

__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import asyncio
import logging
import time
from pathlib import Path
import json
from datetime import datetime

from roostai.back_end.chatbot.config import Config
from roostai.back_end.chatbot.llm_manager import LLMManager
from roostai.back_end.chatbot.quality_checker import QualityChecker
from roostai.back_end.chatbot.query_processor import QueryProcessor
from roostai.back_end.chatbot.reranker import Reranker
from roostai.back_end.chatbot.vector_store import VectorStore

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("chatbot.log")],
)
logger = logging.getLogger(__name__)


class QueryLogger:
    """Helper class to log query results for analysis."""

    def __init__(self, log_dir: str = "query_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def log_query(self, results: Dict[str, Any]):
        """Log query results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.log_dir / f"query_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2)


def verify_db_path(db_path: str) -> bool:
    """Verify that the database path exists and contains the expected files."""
    if not os.path.exists(db_path):
        logger.error(f"Database directory does not exist: {db_path}")
        return False

    sqlite_path = os.path.join(db_path, "chroma.sqlite3")
    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database file not found at: {sqlite_path}")
        return False

    logger.info(f"Found database at: {sqlite_path}")
    return True


class UniversityChatbot:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the chatbot with optional custom database path."""
        self.config = Config.load_config()
        if db_path:
            self.config.vector_db.db_path = db_path

        if not verify_db_path(self.config.vector_db.db_path):
            raise ValueError(f"Invalid database path: {self.config.vector_db.db_path}")

        self.logger = logging.getLogger(__name__)
        self.query_logger = QueryLogger()

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all chatbot components."""
        try:
            self.query_processor = QueryProcessor(
                model_name=self.config.model.embedding_model
            )

            self.vector_store = VectorStore(
                collection_name=self.config.vector_db.collection_name,
                db_path=self.config.vector_db.db_path,
            )

            self.reranker = Reranker(model_name=self.config.model.cross_encoder_model)

            self.quality_checker = QualityChecker(
                min_score=self.config.thresholds.quality_min_score,
                min_docs=self.config.thresholds.quality_min_docs,
            )

            self.llm_manager = LLMManager(
                model_name=self.config.model.llm_model,
                config=self.config,
                llm_model=self.config.model.llm_model,
            )

            # Verify database access
            asyncio.create_task(self._verify_db_access())

        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise

    async def _verify_db_access(self):
        """Verify database access and log statistics."""
        try:
            count = await self.vector_store.get_document_count()
            self.logger.info(f"Connected to database. Document count: {count}")
        except Exception as e:
            self.logger.error(f"Database verification failed: {e}")
            raise

    async def process_query(self, query: str, verbose: bool = False) -> Dict[str, Any]:
        """Process a query and return detailed results dictionary."""
        try:
            results = {
                "query": query,
                "response": None,
                "stage": None,
                "error": None,
                "metrics": {
                    "initial_docs_count": 0,
                    "reranked_docs_count": 0,
                    "quality_score": 0.0,
                    "top_doc_score": None,
                },
            }

            if not query.strip():
                results["error"] = "Empty query"
                results["stage"] = "input_validation"
                return results

            # 1. Query Processing
            try:
                (
                    cleaned_query,
                    query_embedding,
                ) = await self.query_processor.process_query(query)
                results["metrics"]["cleaned_query"] = cleaned_query
            except Exception as e:
                results["error"] = f"Query processing failed: {str(e)}"
                results["stage"] = "query_processing"
                return results

            # 2. Vector Search
            documents = await self.vector_store.query(
                query_embedding, k=self.config.vector_db.top_k
            )
            results["metrics"]["initial_docs_count"] = len(documents)

            if documents:
                results["metrics"]["top_doc_score"] = documents[0].score
                if verbose:
                    results["metrics"]["initial_docs"] = [
                        {"content": doc.content[:200], "score": doc.score}
                        for doc in documents[:3]
                    ]

            if not documents:
                results["error"] = "No initial documents retrieved"
                results["stage"] = "vector_search"
                results["response"] = (
                    "I don't have any relevant information to answer your question. "
                    "Please try asking something else about USC."
                )
                return results

            # 3. Reranking
            reranked_docs = await self.reranker.rerank(
                cleaned_query,
                documents,
                threshold=self.config.thresholds.reranking_threshold,
            )
            results["metrics"]["reranked_docs_count"] = len(reranked_docs)

            if reranked_docs:
                results["metrics"]["top_reranked_score"] = reranked_docs[0].score
                if verbose:
                    results["metrics"]["reranked_docs"] = [
                        {"content": doc.content[:200], "score": doc.score}
                        for doc in reranked_docs[:3]
                    ]

            # 4. Quality Check
            quality_result = await self.quality_checker.check_quality(
                cleaned_query, reranked_docs
            )
            results["metrics"]["quality_score"] = quality_result.quality_score

            if quality_result.quality_score < self.config.thresholds.quality_min_score:
                results["error"] = "Failed quality check"
                results["stage"] = "quality_check"
                results["response"] = (
                    "I don't have enough confident information to provide a good answer. "
                    "Please try rephrasing your question."
                )
                return results

            # 5. LLM Response Generation
            response = await self.llm_manager.generate_response(
                cleaned_query, quality_result
            )
            results["response"] = response
            results["stage"] = "complete"

            return results

        except Exception as e:
            results["error"] = str(e)
            results["stage"] = "unknown"
            results["response"] = "An error occurred processing your query."
            return results

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


async def interactive_session(chatbot: UniversityChatbot):
    """Run an interactive session with the chatbot."""
    print("\nUSC Chatbot Interactive Session")
    print("Type 'quit' to exit, 'debug' to toggle verbose mode")
    print("-" * 50)

    verbose = False

    while True:
        try:
            query = input("\nYour question: ").strip()

            if query.lower() == "quit":
                break
            elif query.lower() == "debug":
                verbose = not verbose
                print(f"Debug mode: {'enabled' if verbose else 'disabled'}")
                continue

            if not query:
                print("Please enter a question.")
                continue

            start_time = time.time()
            results = await chatbot.process_query(query, verbose=verbose)
            end_time = time.time()

            # Print response
            print("\nResponse:", results["response"])

            # Print debug information if verbose mode is enabled
            if verbose:
                print("\nDebug Information:")
                print(f"Processing stage: {results['stage']}")
                print(f"Time taken: {end_time - start_time:.2f} seconds")

                if results.get("metrics"):
                    print("\nMetrics:")
                    for key, value in results["metrics"].items():
                        print(f"- {key}: {value}")

                if results.get("error"):
                    print(f"\nError: {results['error']}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error in interactive session: {e}")
            print("\nAn error occurred. Please try again.")


async def main():
    """Main function to run the chatbot."""
    chatbot = None
    try:
        chatbot = UniversityChatbot()

        # Check document count
        doc_count = await chatbot.get_document_count()
        logger.info(f"Total documents in database: {doc_count}")

        if doc_count == 0:
            logger.error("No documents found in the database. Exiting.")
            return

        # Run interactive session
        await interactive_session(chatbot)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if chatbot:
            await chatbot.cleanup()
        logger.info("Session ended")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
