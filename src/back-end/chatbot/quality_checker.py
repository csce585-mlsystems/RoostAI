import logging
from typing import List

from .types import Document, QueryResult


class QualityChecker:
    def __init__(self, min_score: float, min_docs: int):
        """Initialize quality checker with threshold parameters."""
        self.min_score = min_score
        self.min_docs = min_docs
        self.logger = logging.getLogger(__name__)

    async def check_quality(
            self,
            query: str,
            documents: List[Document]
    ) -> QueryResult:
        """Check quality of retrieved documents."""
        try:
            if not documents:
                self.logger.warning("No documents provided for quality check")
                return QueryResult(documents=[], quality_score=0.0)

            # Calculate average score of top documents
            top_docs = documents[:self.min_docs]
            scores = [doc.score for doc in top_docs]
            avg_score = sum(scores) / len(scores)

            # Calculate overall quality score
            quality_score = avg_score if len(top_docs) >= self.min_docs else 0.0

            self.logger.info(f"Quality check completed. Score: {quality_score:.2f}")
            self.logger.info(f"Number of documents: {len(documents)}")
            self.logger.info(f"Top document scores: {scores}")

            # Log document contents for debugging
            for i, doc in enumerate(top_docs):
                self.logger.debug(f"Document {i} content: {doc.content[:100]}...")

            return QueryResult(
                documents=documents,
                quality_score=quality_score
            )

        except Exception as e:
            self.logger.error(f"Error during quality check: {e}")
            raise
