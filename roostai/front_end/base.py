from abc import ABC, abstractmethod

from roostai.back_end.chatbot.types import Document


class ChatbotInterface(ABC):
    """Base class for all chatbot interfaces."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the interface."""
        pass

    @abstractmethod
    async def handle_query(self, query: str) -> None:
        """Handle a user query."""
        pass

    @abstractmethod
    async def handle_document_addition(self, documents: list[Document]) -> None:
        """Handle adding new documents."""
        pass

    @abstractmethod
    async def handle_error(self, error: Exception) -> None:
        """Handle errors."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
