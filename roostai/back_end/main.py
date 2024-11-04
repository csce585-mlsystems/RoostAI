import asyncio
import logging
import os
from typing import List

from roostai.back_end.chatbot.llm_manager import LLMManager
from roostai.back_end.chatbot.quality_checker import QualityChecker
from roostai.back_end.chatbot.query_processor import QueryProcessor
from roostai.back_end.chatbot.reranker import Reranker
from roostai.back_end.chatbot.types import Document
from roostai.back_end.chatbot.vector_store import VectorStore
from roostai.back_end.chatbot.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniversityChatbot:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config.load_config(config_path)
        self.logger = logging.getLogger(__name__)

        self.query_processor = QueryProcessor(
            model_name=self.config.model.embedding_model
        )

        self.vector_store = VectorStore(
            collection_name=self.config.vector_db.collection_name
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
            config=self.config.llm
        )

    async def process_query(self, query: str) -> str:
        try:
            cleaned_query, query_embedding = await self.query_processor.process_query(query)

            documents = await self.vector_store.query(
                query_embedding,
                k=self.config.vector_db.top_k
            )

            if not documents:
                return "I apologize, but I don't have any documents in my knowledge base yet."

            reranked_docs = await self.reranker.rerank(
                cleaned_query,
                documents,
                threshold=self.config.thresholds.reranking_threshold
            )

            result = await self.quality_checker.check_quality(cleaned_query, reranked_docs)
            response = await self.llm_manager.generate_response(cleaned_query, result)

            return response or "I apologize, but I couldn't generate a response."

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return "I'm sorry, but I encountered an error processing your query."

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

    # More relevant test documents
    test_docs = [
        Document(
            content="The USC Computer Science program requires a minimum GPA of 3.0 for admission. "
                    "Applicants must also complete prerequisite courses in mathematics and programming.",
            metadata={"department": "Computer Science", "type": "admission_requirements"}
        ),
        Document(
            content="Computer Science admission requirements include: SAT/ACT scores, "
                    "letters of recommendation, and a strong background in mathematics.",
            metadata={"department": "Computer Science", "type": "admission_requirements"}
        ),
        Document(
            content="Transfer students applying to the Computer Science program must have "
                    "completed calculus I and have a minimum GPA of 3.0 in all prior coursework.",
            metadata={"department": "Computer Science", "type": "transfer_requirements"}
        )
    ]

    # Add documents
    await chatbot.add_documents(test_docs)

    # Test query
    response = await chatbot.process_query(
        "What are the admission requirements for the Computer Science program?"
    )
    print("\nResponse:", response)


if __name__ == "__main__":
    asyncio.run(main())
