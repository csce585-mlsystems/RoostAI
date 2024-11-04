import logging
from typing import List

from sentence_transformers import CrossEncoder

from .types import Document


class Reranker:
    def __init__(self, model_name: str):
        """Initialize reranker with specified cross-encoder model."""
        self.logger = logging.getLogger(__name__)
        self.model = CrossEncoder(model_name)

    async def rerank(
            self,
            query: str,
            documents: List[Document],
            threshold: float
    ) -> List[Document]:
        """Rerank documents using cross-encoder and filter by threshold."""
        try:
            if not documents:
                self.logger.warning("No documents to rerank")
                return []

            # Prepare pairs for cross-encoder
            pairs = [[query, doc.content] for doc in documents]

            # Get cross-encoder scores
            scores = self.model.predict(pairs)

            # Update document scores and filter
            scored_docs = []
            for doc, score in zip(documents, scores):
                doc.score = float(score)
                if score >= threshold:
                    scored_docs.append(doc)

            # Sort by score descending
            scored_docs.sort(key=lambda x: x.score, reverse=True)

            if not scored_docs:
                self.logger.warning(
                    f"No documents passed threshold {threshold}. Best score was {max(scores) if scores else 'N/A'}"
                )

            return scored_docs

        except Exception as e:
            self.logger.error(f"Reranking failed: {e}")
            raise
