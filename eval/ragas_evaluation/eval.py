from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from langchain import HuggingFacePipeline
from langchain_huggingface import HuggingFaceEmbeddings

import logging
import asyncio
import os
import json
from tqdm import tqdm
from statistics import mean
from ragas import SingleTurnSample
from ragas.metrics import (
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    FaithfulnesswithHHEM,
    NoiseSensitivity,
    ResponseRelevancy,
)

# embedding model
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# evaluator
model_id = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

pipe = pipeline(
    model=model,
    tokenizer=tokenizer,
    return_full_text=True,  # langchain expects the full text
    task="text-generation",
    temperature=0.1,
    repetition_penalty=1.1,  # without this output begins repeating
)

evaluator = HuggingFacePipeline(pipeline=pipe)

# initialize metric calculators
context_precision = LLMContextPrecisionWithReference(llm=evaluator)
context_recall = LLMContextRecall(llm=evaluator)
faithfulness = FaithfulnesswithHHEM(llm=evaluator)
noise_sensitivity = NoiseSensitivity(llm=evaluator)

# initialize logger
logging.basicConfig(
    level=logging.INFO,  # WARNING, ERROR, CRITICAL messages will be logged
    # Timestamp - (Warning/Error/Critical) - STDOUT
    format="%(asctime)s - %(levelname)s - %(message)s",
)
# sets the name of the logger to be the name of the module
logger = logging.getLogger(__name__)


async def rag_eval(query_info: dict):
    """
    query_info = {'query': str, 'ground_truth': str, 'response': str, 'contexts': List[str]}
    """
    sample = SingleTurnSample(
        user_input=query_info["query"],
        reference=query_info["ground_truth"],
        response=query_info["response"],
        retrieved_contexts=query_info["contexts"],
    )

    context_precision_score = await context_precision.single_turn_ascore(sample)
    context_recall_score = await context_precision.single_turn_ascore(sample)
    faithfulness_score = await faithfulness.single_turn_ascore(sample)
    noise_sensitivity_score = await noise_sensitivity.single_turn_ascore(sample)

    # add previous evals

    evals = {
        "context_precision": context_precision_score,
        "context_recall": context_recall_score,
        "faithfulness": faithfulness_score,
        "noise_sensitivty": noise_sensitivity_score,
    }

    return evals


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
        logger.info(f"Evaluating {response_dir}")
        context_precision_scores = []
        context_recall_scores = []
        faithfulness_scores = []
        noise_sensitivity_scores = []
        with open(os.path.join(response_dir, "detailed_results.json"), "r") as f:
            results: list = json.load(f)
            for res in tqdm(results, "Responses"):
                if res["response"] in failures:
                    continue
                scores = await rag_eval(res)
                context_precision_scores.append(scores["context_precision"])
                context_recall_scores.append(scores["context_recall"])
                faithfulness_scores.append(scores["faithfulness"])
                noise_sensitivity_scores.append(scores["noise_sensitivty"])

        mean_scores = {
            "context_precision": mean(context_precision_scores),
            "context_recall": mean(context_recall_scores),
            "faithfulness": mean(faithfulness_scores),
            "noise_sensitivity": mean(noise_sensitivity_scores),
        }

        with open(os.path.join(response_dir, "rag_scores.json"), "w") as f:
            json.dump(mean_scores, f)


if __name__ == "__main__":
    asyncio.run(main())
