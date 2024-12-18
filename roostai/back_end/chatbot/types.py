from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DocumentMetadata:
    url: str
    # department: Optional[str] = None
    # doc_type: Optional[str] = None
    # date_added: Optional[str] = None


@dataclass
class Document:
    content: str
    metadata: DocumentMetadata
    score: Optional[float] = None  # Score after reranking
    vector_score: Optional[float] = None  # Original vector similarity score


@dataclass
class QueryResult:
    documents: List[Document]
    quality_score: float
    response: Optional[str] = None
