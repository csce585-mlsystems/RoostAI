from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path


@dataclass
class SurveyConfig:
    # Per-query questions
    per_query_questions: List[Dict] = None

    # Overall system survey questions
    overall_questions: List[Dict] = None

    # Paths
    responses_dir: Path = Path("roostai/front_end/data/responses")

    def __post_init__(self):
        self.per_query_questions = [
            {
                "id": "trust",
                "text": "How much do you trust this provided response?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "No trust", 5: "Complete Trust"},
            },
            {
                "id": "comprehensiveness",
                "text": "How comprehensive did you find the response?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Very Superficial", 5: "Very Thorough"},
            },
        ]

        self.overall_questions = [
            {
                "id": "speed",
                "text": "How would you rate the speed of the system's responses compared to other information retrieval methods?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Much Slower", 5: "Much Faster"},
            },
            {
                "id": "ease_of_use",
                "text": "How easy was it to use the system and understand its responses?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Strongly Disagree", 5: "Strongly Agree"},
            },
            {
                "id": "query_handling",
                "text": "How well did the system handle different types of queries?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Strongly Disagree", 5: "Strongly Agree"},
            },
            {
                "id": "satisfaction",
                "text": "How satisfied are you with the RAG system?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Very Dissatisfied", 5: "Very Satisfied"},
            },
            {
                "id": "improvements",
                "text": "What specific improvements would you suggest for the system?",
                "type": "text",
                "optional": True,
            },
        ]

        # Create responses directory if it doesn't exist
        self.responses_dir.mkdir(parents=True, exist_ok=True)
