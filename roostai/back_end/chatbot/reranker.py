import logging
from typing import List
import numpy as np
from sentence_transformers import CrossEncoder

from .types import Document


class Reranker:
    def __init__(self, model_name: str):
        """Initialize reranker with specified cross-encoder model."""
        self.logger = logging.getLogger(__name__)
        self.model = CrossEncoder(model_name)

    async def rerank(
        self, query: str, documents: List[Document], threshold: float
    ) -> List[Document]:
        """Rerank documents using cross-encoder and filter by threshold."""
        try:
            if not documents:
                self.logger.warning("No documents to rerank")
                return []

            # Prepare pairs for cross-encoder
            pairs = [[query, doc.content] for doc in documents]

            # Get cross-encoder scores
            cross_encoder_scores = self.model.predict(pairs)

            # Convert scores to float if they're numpy arrays
            scores = [
                float(score)
                if isinstance(score, (np.ndarray, np.float32, np.float64))
                else score
                for score in cross_encoder_scores
            ]

            # Log both vector similarity and cross-encoder scores for comparison
            self.logger.info("\nScore comparison for top documents:")
            for i, (doc, cross_score) in enumerate(zip(documents[:3], scores[:3])):
                self.logger.info(
                    f"Doc {i + 1}:"
                    f"\n  - Vector similarity score: {doc.score:.3f}"
                    f"\n  - Cross-encoder score: {cross_score:.3f}"
                    f"\n  - Content preview: {doc.content[:100]}..."
                )

            # Update document scores and filter
            scored_docs = []
            for doc, cross_score in zip(documents, scores):
                # Store both scores for transparency
                doc.vector_score = doc.score  # Save original vector similarity score
                doc.score = cross_score  # Update main score to cross-encoder score

                if cross_score >= threshold:
                    scored_docs.append(doc)

            # Sort by cross-encoder score descending
            scored_docs.sort(key=lambda x: x.score, reverse=True)

            self.logger.info(
                f"Reranking results:"
                f"\n - Input documents: {len(documents)}"
                f"\n - Passed threshold ({threshold}): {len(scored_docs)}"
                f"\n - Best cross-encoder score: {max(scores) if scores else 'N/A'}"
                f"\n - Best vector similarity: {max(doc.vector_score for doc in documents) if documents else 'N/A'}"
            )

            return scored_docs

        except Exception as e:
            self.logger.error(f"Reranking failed: {e}")
            raise
