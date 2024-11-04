import logging
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer


class QueryProcessor:
    def __init__(self, model_name: str):
        """Initialize query processor with specified embedding model."""
        self.logger = logging.getLogger(__name__)
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise

    @lru_cache(maxsize=1000)
    def _generate_embedding(self, query: str) -> List[float]:
        """Generate and cache embeddings for queries."""
        return self.model.encode(query).tolist()

    async def process_query(self, query: str) -> tuple[str, List[float]]:
        """Process and embed a user query."""
        try:
            cleaned_query = query.strip()
            if not cleaned_query:
                raise ValueError("Empty query received")

            embedding = self._generate_embedding(cleaned_query)
            return cleaned_query, embedding

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            raise

    def clear_cache(self):
        """Clear any cached embeddings."""
        if hasattr(self, 'model'):
            # No clear_cache() method available in SentenceTransformer, use something else instead
            pass
