from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Document:
    content: str
    metadata: dict
    score: Optional[float] = None


@dataclass
class QueryResult:
    documents: List[Document]
    quality_score: float
    response: Optional[str] = None
