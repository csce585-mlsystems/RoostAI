import logging
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

    async def process_query(self, query: str) -> tuple[str, List[float]]:
        """Process and embed a user query."""
        try:
            # Basic query cleaning
            cleaned_query = query.strip()
            if not cleaned_query:
                raise ValueError("Empty query received")

            # Generate embedding
            embedding = self.model.encode(cleaned_query)
            return cleaned_query, embedding.tolist()

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            raise
