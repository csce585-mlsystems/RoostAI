import asyncio
import pandas as pd
from typing import List
import logging
from pathlib import Path

from roostai.back_end.main import UniversityChatbot

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocalRAGTester:
    def __init__(self, data_file: str):
        """Initialize the RAG tester with input data file."""
        self.data_file = data_file
        self.chatbot = None
        self.df = None

    async def initialize(self):
        """Initialize the chatbot and load data."""
        try:
            self.chatbot = UniversityChatbot()

            # Verify database has documents
            doc_count = await self.chatbot.get_document_count()
            logger.info(f"Database contains {doc_count} documents")

            if doc_count == 0:
                raise ValueError("No documents found in the database")

            # Load questions
            logger.info(f"Reading questions from {self.data_file}")
            self.df = pd.read_csv(self.data_file)
            logger.info(f"Loaded {len(self.df)} questions")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def get_responses(self) -> List[str]:
        """Get responses for all questions using the local RAG system."""
        if self.chatbot is None or self.df is None:
            raise ValueError("System not initialized. Call initialize() first")

        responses = []

        for idx, row in self.df.iterrows():
            question = row["question"]
            try:
                logger.info("\n\n")
                logger.info(f"Processing question {idx + 1}/{len(self.df)}")
                logger.debug(f"Question: {question}")

                response = await self.chatbot.process_query(question)
                logger.info(f"Response:\n{response}\n")

                responses.append(response)

                # Add a small delay between queries
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing question {idx + 1}: {e}")
                responses.append(f"Error: {str(e)}")

            # Log progress every 10 questions
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(self.df)} questions")

        return responses

    async def cleanup(self):
        """Cleanup resources."""
        if self.chatbot:
            await self.chatbot.cleanup()


async def main():
    data_file: str = "data/faq_pairs_milestone2.csv"
    out_file: str = "data/faq_responses_local_rag.csv"

    tester = LocalRAGTester(data_file)

    try:
        await tester.initialize()

        # Get responses
        logger.info("Getting responses from local RAG system...")
        responses = await tester.get_responses()

        # Add responses to dataframe
        tester.df["local_rag"] = responses

        # Save results
        logger.info(f"Writing results to {out_file}")
        tester.df.to_csv(out_file, index=False)

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise

    finally:
        await tester.cleanup()
        logger.info("Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())
