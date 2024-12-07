import json
from pathlib import Path
from typing import Dict


def save_interaction(
    responses_dir: Path,
    session_id: str,
    interaction_num: int,
    interaction_data: Dict,
    per_query_responses: Dict,
) -> None:
    """Save interaction details to a JSON file with optimized format."""
    # Extract relevant information from raw_results
    raw_results = interaction_data["raw_results"]
    metrics = raw_results["metrics"]

    # Create optimized interaction record
    cleaned_interaction = {
        "timestamp": interaction_data["timestamp"],
        "processing_time": interaction_data["processing_time"],
        "interaction": {
            "query": interaction_data["query"],
            "response": interaction_data["response"],
            "stage": raw_results["stage"],
            "error": raw_results["error"],
        },
        "metrics": {
            "initial_docs": metrics["initial_docs_count"],
            "reranked_docs": metrics["reranked_docs_count"],
            "quality_score": metrics["quality_score"],
            "top_doc_score": metrics["top_doc_score"],
        },
        "feedback": per_query_responses,
    }

    # Create session directory if it doesn't exist
    session_dir = responses_dir / session_id
    session_dir.mkdir(exist_ok=True)

    # Save interaction data
    file_path = session_dir / f"interaction_{interaction_num}.json"
    with open(file_path, "w") as f:
        json.dump(cleaned_interaction, f, indent=2)


def save_overall_survey(
    responses_dir: Path, session_id: str, survey_responses: Dict
) -> None:
    """Save overall survey responses to a JSON file."""
    session_dir = responses_dir / session_id
    session_dir.mkdir(exist_ok=True)

    file_path = session_dir / "overall_survey.json"
    with open(file_path, "w") as f:
        json.dump(survey_responses, f, indent=2)
