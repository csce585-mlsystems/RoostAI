import asyncio
import json
import pandas as pd
from typing import List, Dict, Any
import logging
from pathlib import Path
from datetime import datetime

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
        self.results: List[Dict[str, Any]] = []

        # Create timestamp for unique run identification
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def initialize(self, db_path: str):
        """Initialize the chatbot and load data."""
        try:
            self.chatbot = UniversityChatbot(db_path)

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

    async def get_responses(self, verbose: bool = True) -> List[Dict[str, Any]]:
        """Get responses for all questions using the local RAG system."""
        if self.chatbot is None or self.df is None:
            raise ValueError("System not initialized. Call initialize() first")

        for idx, row in self.df.iterrows():
            question = row["question"]
            try:
                logger.info("\n" + "=" * 80)
                logger.info(f"Processing question {idx + 1}/{len(self.df)}")
                logger.debug(f"Question: {question}")

                # Get detailed results from chatbot
                result = await self.chatbot.process_query(question, verbose=verbose)

                # Add question metadata
                result["question_id"] = idx + 1
                result["ground_truth"] = row.get("answer", None)

                # Store result
                self.results.append(result)

                # Log detailed information if verbose
                if verbose:
                    logger.info("\nQuery Results:")
                    logger.info(f"Stage completed: {result['stage']}")
                    logger.info(f"Error (if any): {result['error']}")
                    logger.info("\nMetrics:")
                    for key, value in result["metrics"].items():
                        logger.info(f"{key}: {value}")
                    logger.info(f"\nResponse: {result['response']}\n")

                # Add a small delay between queries
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing question {idx + 1}: {e}")
                self.results.append(
                    {
                        "question_id": idx + 1,
                        "query": question,
                        "response": f"Error: {str(e)}",
                        "stage": "error",
                        "error": str(e),
                        "metrics": {},
                        "ground_truth": row.get("answer", None),
                    }
                )

            # Log progress every 10 questions
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(self.df)} questions")

        return self.results

    def save_results(self, base_output_dir: str = "data/results"):
        """Save results in multiple formats for analysis."""
        # Create output directory with timestamp
        output_dir = Path(base_output_dir) / self.run_timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save detailed JSON results
        json_path = output_dir / "detailed_results.json"
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)

        # 2. Save CSV with main results
        csv_data = []
        for result in self.results:
            csv_data.append(
                {
                    "question_id": result["question_id"],
                    "question": result["query"],
                    "response": result["response"],
                    "stage": result["stage"],
                    "error": result["error"],
                    "quality_score": result["metrics"].get("quality_score", None),
                    "initial_docs_count": result["metrics"].get(
                        "initial_docs_count", 0
                    ),
                    "reranked_docs_count": result["metrics"].get(
                        "reranked_docs_count", 0
                    ),
                    "ground_truth": result["ground_truth"],
                }
            )

        csv_path = output_dir / "results.csv"
        pd.DataFrame(csv_data).to_csv(csv_path, index=False)

        # 3. Generate summary statistics
        summary = {
            "total_queries": len(self.results),
            "successful_queries": sum(
                1 for r in self.results if r["stage"] == "complete"
            ),
            "failed_queries": sum(1 for r in self.results if r["stage"] != "complete"),
            "failure_stages": {},
            "average_quality_score": 0.0,
            "average_initial_docs": 0.0,
            "average_reranked_docs": 0.0,
        }

        # Calculate averages and collect failure stages
        quality_scores = []
        initial_docs = []
        reranked_docs = []

        for result in self.results:
            if result["stage"] != "complete":
                summary["failure_stages"][result["stage"]] = (
                    summary["failure_stages"].get(result["stage"], 0) + 1
                )

            if "metrics" in result:
                if "quality_score" in result["metrics"]:
                    quality_scores.append(result["metrics"]["quality_score"])
                if "initial_docs_count" in result["metrics"]:
                    initial_docs.append(result["metrics"]["initial_docs_count"])
                if "reranked_docs_count" in result["metrics"]:
                    reranked_docs.append(result["metrics"]["reranked_docs_count"])

        if quality_scores:
            summary["average_quality_score"] = sum(quality_scores) / len(quality_scores)
        if initial_docs:
            summary["average_initial_docs"] = sum(initial_docs) / len(initial_docs)
        if reranked_docs:
            summary["average_reranked_docs"] = sum(reranked_docs) / len(reranked_docs)

        # Save summary
        summary_path = output_dir / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\nResults saved to {output_dir}")
        return output_dir

    async def cleanup(self):
        """Cleanup resources."""
        if self.chatbot:
            await self.chatbot.cleanup()


async def main():
    data_file: str = "data/faq_pairs.csv"
    db_path: str = "/home/cc/RoostAI/roostai/data/v2"
    output_dir: str = "data/results"

    tester = LocalRAGTester(data_file)

    try:
        await tester.initialize(db_path=db_path)

        # Get responses
        logger.info("Getting responses from local RAG system...")
        results = await tester.get_responses(verbose=True)

        # Save results and get output directory
        results_dir = tester.save_results(output_dir)

        logger.info("\nTesting completed! Summary of results:")
        with open(results_dir / "summary.json", "r") as f:
            summary = json.load(f)
            for key, value in summary.items():
                logger.info(f"{key}: {value}")

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
