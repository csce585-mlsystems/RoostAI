from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path


@dataclass
class SurveyConfig:
    # Overall system survey questions
    overall_questions: List[Dict] = None

    # Paths
    responses_dir: Path = Path("roostai/front_end/responses")

    def __post_init__(self):
        self.overall_questions = [
            {
                "id": "response_quality",
                "text": "💎 Quality: How would you rate the overall quality of the responses?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Poor", 5: "Excellent"},
            },
            {
                "id": "speed",
                "text": "💨 Speed: How would you rate the speed of the system's responses?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Very Slow", 5: "Very Fast"},
            },
            {
                "id": "ease_of_use",
                "text": "✨ Usability: How easy was it to use the system?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Very Difficult", 5: "Very Easy"},
            },
            {
                "id": "would_use_again",
                "text": "😌 Satisfaction: How likely are you to use this system again?",
                "type": "likert",
                "options": list(range(1, 6)),
                "labels": {1: "Very Unlikely", 5: "Very Likely"},
            },
            {
                "id": "improvements",
                "text": "📈 Optional Suggestion: What improvements would you suggest for the system?",
                "type": "text",
                "optional": True,
            },
        ]

        # Create responses directory if it doesn't exist
        self.responses_dir.mkdir(parents=True, exist_ok=True)
