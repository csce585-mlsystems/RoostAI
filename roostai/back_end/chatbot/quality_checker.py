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
        """Enhanced quality checking with more flexible criteria."""
        try:
            if not documents:
                self.logger.warning("No documents provided for quality check")
                return QueryResult(documents=[], quality_score=0.0)

            # Calculate weighted quality score
            scores = []
            weights = []

            # Consider more documents but with decreasing weights
            for i, doc in enumerate(documents[:5]):  # Consider top 5 docs
                if doc.score is not None:
                    weight = 1.0 / (i + 1)  # Decreasing weights
                    scores.append(doc.score * weight)
                    weights.append(weight)

            if not scores:
                self.logger.warning("No valid scores found in documents")
                return QueryResult(documents=documents, quality_score=0.0)

            # Weighted average score
            quality_score = sum(scores) / sum(weights)

            # Bonus for having multiple relevant documents
            if len(scores) >= 2:
                quality_score *= 1 + 0.1 * len(scores)  # Bonus for more docs

            self.logger.info(f"Quality check completed. Score: {quality_score:.2f}")
            self.logger.debug(f"Number of documents: {len(documents)}")
            self.logger.debug(f"Top document scores: {scores}")

            return QueryResult(documents=documents, quality_score=quality_score)

        except Exception as e:
            self.logger.error(f"Error during quality check: {e}")
            raise
