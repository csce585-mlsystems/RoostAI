import logging
import os
from typing import Optional

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from .types import QueryResult
from .config import LLMConfig


class LLMManager:
    def __init__(self, model_name: str, config: LLMConfig):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.config = config

        load_dotenv()
        self.api_token = os.getenv("HF_API_KEY")
        if not self.api_token:
            raise ValueError("HF_API_KEY environment variable not set")

        self.client = InferenceClient(token=self.api_token)
        # self.model = "mistralai/Mixtral-8x7B-v0.1"
        self.model = "Qwen/Qwen2.5-1.5B"

        self.system_prompt: str = ("You are a chatbot specifically designed to provide information about the "
                                   "University of South Carolina (USC). Your knowledge encompasses USC's "
                                   "history, academics, campus life, athletics, notable alumni, and current events "
                                   "related to the university. When answering questions, always assume they are in "
                                   "the context of USC unless explicitly stated otherwise. Provide accurate and "
                                   "up-to-date information about USC, maintaining a friendly and enthusiastic tone "
                                   "that reflects the spirit of the community. If you're unsure about any "
                                   "USC-specific information, state that you don't have that particular detail rather "
                                   "than guessing. Your purpose is to assist students, faculty, alumni, and anyone "
                                   "interested in learning more about USC.")

    def generate_prompt(self, query: str, result: QueryResult) -> str:
        """Generate prompt for LLM using query and retrieved documents."""
        context = "\n".join(f"- {doc.content}" for doc in result.documents)

        return f"""
{self.system_prompt}

Context information:

{context}

User question: {query}

Please provide a helpful response based on the context above.
"""

    async def generate_response(
            self,
            query: str,
            result: QueryResult
    ) -> Optional[str]:
        try:
            if result.quality_score < self.config.quality_min_score:
                self.logger.warning(f"Low quality score: {result.quality_score}")
                return "I apologize, but I don't have enough relevant information to provide a good answer."

            prompt = self.generate_prompt(query, result)

            response = self.client.text_generation(
                prompt,
                model=self.model_name,
                max_new_tokens=self.config.max_length,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                repetition_penalty=self.config.repetition_penalty
            )

            return response

        except Exception as e:
            self.logger.error(f"LLM response generation failed: {e}")
            return None
