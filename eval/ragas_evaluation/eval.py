import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from langchain import HuggingFacePipeline
from langchain_community.llms import HuggingFaceEndpoint  # For remote HF models
from datasets import Dataset
import logging
import asyncio
import os
import json
from tqdm import tqdm
from statistics import mean
from ragas import SingleTurnSample, evaluate
from ragas.metrics import (
    faithfulness,
    context_recall,
    context_precision,
    answer_relevancy,
)
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


# from ragas.metrics import (
#     LLMContextPrecisionWithReference,
#     LLMContextRecall,
#     FaithfulnesswithHHEM,
#     NoiseSensitivity,
#     ResponseRelevancy,
# )

# initialize metric calculators
# context_precision = LLMContextPrecisionWithReference(llm=evaluator)
# context_precision = LLMContextPrecisionWithReference()
# context_recall = LLMContextRecall(llm=evaluator)
# faithfulness = FaithfulnesswithHHEM(llm=evaluator)
# noise_sensitivity = NoiseSensitivity(llm=evaluator)

# initialize logger
logging.basicConfig(
    level=logging.INFO,  # WARNING, ERROR, CRITICAL messages will be logged
    # Timestamp - (Warning/Error/Critical) - STDOUT
    format="%(asctime)s - %(levelname)s - %(message)s",
)
# sets the name of the logger to be the name of the module
logger = logging.getLogger(__name__)


# async def rag_eval(query_info: dict):
#     """
#     query_info = {'query': str, 'ground_truth': str, 'response': str, 'contexts': List[str]}
#     """
#     sample = SingleTurnSample(
#         user_input=query_info["query"],
#         reference=query_info["ground_truth"],
#         response=query_info["response"],
#         retrieved_contexts=query_info["contexts"],
#     )

#     # context_precision_score = await context_precision.single_turn_ascore(sample)
#     context_precision_score = context_precision.score(sample)
#     context_recall_score = await context_precision.single_turn_ascore(sample)
#     faithfulness_score = await faithfulness.single_turn_ascore(sample)
#     noise_sensitivity_score = await noise_sensitivity.single_turn_ascore(sample)

#     # add previous evals

#     evals = {
#         "context_precision": context_precision_score,
#         "context_recall": context_recall_score,
#         "faithfulness": faithfulness_score,
#         "noise_sensitivty": noise_sensitivity_score,
#     }

#     return evals


async def main():
    rag_response_dir = "/home/cc/RoostAI/eval/ragas_evaluation/data/results"
    rag_response_dirs = [
        os.path.join(rag_response_dir, folder)
        for folder in os.listdir(rag_response_dir)
    ]
    rag_response_dirs = [
        os.path.join(folder, os.listdir(folder)[0]) for folder in rag_response_dirs
    ]

    failures = {
        (
            "I don't have any relevant information to answer your question. "
            "Please try asking something else about USC."
        ),
        (
            "I don't have enough confident information to provide a good answer. "
            "Please try rephrasing your question."
        ),
        "An error occurred processing your query.",
    }

    for response_dir in tqdm(rag_response_dirs, "Chunking Strategy"):
        if "v3_50_thresh" in response_dir:
            continue
        logger.info(f"Evaluating {response_dir}")

        try:
            # Your existing data preparation code
            data = {"question": [], "answer": [], "contexts": [], "reference": []}
            with open(os.path.join(response_dir, "detailed_results.json"), "r") as f:
                results: list = json.load(f)

            for res in tqdm(results, "Responses"):
                if res["response"] in failures or not len(res["contexts"]):
                    continue
                data["question"].append(res["query"])
                data["answer"].append(res["response"])
                data["contexts"].append(res["contexts"])
                data["reference"].append(res["ground_truth"])

            assert (
                len(data["question"])
                == len(data["answer"])
                == len(data["contexts"])
                == len(data["reference"])
            )
            assert all(type(context) == list for context in data["contexts"])

            # Add some debug prints
            print(f"Number of samples: {len(data['question'])}")
            print("Sample data:", {k: v[:2] for k, v in data.items()})

            dataset = Dataset.from_dict(data)

            # Try evaluating with fewer metrics if needed
            result = evaluate(
                dataset=dataset,
                metrics=[context_precision, context_recall],  # Reduced metrics
            )

            df = result.to_pandas()
            df.to_csv(os.path.join(response_dir, "rag_scores.csv"))

        except Exception as e:
            logger.error(f"Error processing {response_dir}: {e}")
            import traceback

            traceback.print_exc()
            continue

    return  # Replace exit(0) with return


if __name__ == "__main__":
    asyncio.run(main())
