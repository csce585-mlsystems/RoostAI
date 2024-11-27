import logging
from typing import List

from .types import Document, QueryResult


class QualityChecker:
    def __init__(self, min_score: float, min_docs: int):
        """Initialize quality checker with threshold parameters."""
        self.min_score = min_score  # Minimum score to pass quality check
        self.min_docs = (
            min_docs  # Minimum number of documents required for quality check
        )
        self.logger = logging.getLogger(__name__)

    async def check_quality(self, query: str, documents: List[Document]) -> QueryResult:
        """Check quality of retrieved documents."""
        try:
            if not documents:
                self.logger.warning("No documents provided for quality check")
                return QueryResult(documents=[], quality_score=0.0)

            # Calculate average score of top documents
            top_docs = documents[: self.min_docs]
            if len(top_docs) < self.min_docs:
                self.logger.warning(
                    f"Insufficient number of documents: {len(top_docs)} < {self.min_docs}"
                )
                return QueryResult(documents=documents, quality_score=0.0)

            scores = [doc.score for doc in top_docs if doc.score is not None]
            if not scores:
                self.logger.warning("No valid scores found in documents")
                return QueryResult(documents=documents, quality_score=0.0)

            avg_score = sum(scores) / len(scores)
            quality_score = avg_score if len(top_docs) >= self.min_docs else 0.0

            self.logger.info(f"Quality check completed. Score: {quality_score:.2f}")
            self.logger.debug(f"Number of documents: {len(documents)}")
            self.logger.debug(f"Top document scores: {scores}")

            return QueryResult(documents=documents, quality_score=quality_score)

        except Exception as e:
            self.logger.error(f"Error during quality check: {e}")
            raise
