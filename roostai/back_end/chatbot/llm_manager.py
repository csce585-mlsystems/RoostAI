import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from .config import Config
from .types import QueryResult


class LLMManager:
    def __init__(self, model_name: str, config: Config, llm_model: str):
        """Initialize the Hugging Face Inference API client for LLM."""

        self.logger = logging.getLogger(__name__)
        self.model_name = model_name

        self.config = config
        self.quality_min_score = (
            config.thresholds.quality_min_score
        )  # Get from main config

        load_dotenv()
        self.api_token = os.getenv("HF_API_KEY")
        if not self.api_token:
            raise ValueError("HF_API_KEY environment variable not set")

        self.client = InferenceClient(token=self.api_token)
        self.model = llm_model

        self.system_prompt: str = (
            "You are a chatbot specifically designed to provide information about the "
            "University of South Carolina (USC). Your knowledge encompasses USC's "
            "history, academics, campus life, athletics, notable alumni, and current events "
            "related to the university. When answering questions, always assume they are in "
            "the context of USC unless explicitly stated otherwise. Provide accurate and "
            "up-to-date information about USC, maintaining a friendly and enthusiastic tone "
            "that reflects the spirit of the community. If you're unsure about any "
            "USC-specific information, state that you don't have that particular detail rather "
            "than guessing. Your purpose is to assist students, faculty, alumni, and anyone "
            "interested in learning more about USC."
        )

    def generate_prompt(self, query: str, result: QueryResult) -> str:
        """Generate prompt for LLM using query and retrieved documents."""

        context = "\n".join(f"- {doc.content}" for doc in result.documents)

        return f"""
{self.system_prompt}

Context information:
{context}

User question: {query}

Please provide a helpful response based on the context above. If the context doesn't contain relevant information to answer the question, please state that clearly.
Additionally, please enclose your response in <response> tags.
"""

    async def generate_response(self, query: str, result: QueryResult) -> Optional[str]:
        try:
            if result.quality_score < self.quality_min_score:
                self.logger.warning(
                    f"Query failed quality check:\n"
                    f"- Quality score: {result.quality_score}\n"
                    f"- Minimum required: {self.quality_min_score}\n"
                    f"- Number of documents: {len(result.documents)}\n"
                    f"- Top document score: {result.documents[0].score if result.documents else 'N/A'}"
                )
                return (
                    "I apologize, but I don't have enough confident information to "
                    "provide a good answer to your question. Please try rephrasing or "
                    "asking about a different topic related to USC."
                )

            if not result.documents:
                self.logger.warning(
                    "No documents retrieved for LLM response generation"
                )
                return (
                    "I apologize, but I don't have any relevant information to answer your question. "
                    "Please try asking something about USC."
                )

            prompt = self.generate_prompt(query, result)
            # print(f"Prompt:\n{prompt}")

            # Use asyncio.wait_for to add timeout
            response = await asyncio.wait_for(
                self._generate_response(prompt), timeout=5.0  # 5 seconds timeout
            )

            # Get the response within the <response> tags
            return response.split("<response>")[1].split("</response>")[0].strip()

        except asyncio.TimeoutError:
            self.logger.error("LLM response generation timed out")
            return "I apologize, but the response is taking too long. Please try again."
        except Exception as e:
            self.logger.error(f"LLM response generation failed: {e}")
            return "I apologize, but I encountered an error generating the response."

    async def _generate_response(self, prompt: str) -> str:
        """Separate method for actual response generation to allow for timeout."""
        return self.client.text_generation(
            prompt,
            model=self.model_name,
            max_new_tokens=self.config.llm.max_length,
            temperature=self.config.llm.temperature,
            top_p=self.config.llm.top_p,
            repetition_penalty=self.config.llm.repetition_penalty,
        )

    async def close(self):
        """Close LLM connections and clean up resources."""
        try:
            if hasattr(self, "client"):
                self.client = None
            self.logger.info("LLM manager cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during LLM cleanup: {e}")
            raise
