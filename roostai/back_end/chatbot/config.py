from dataclasses import dataclass


@dataclass
class ModelConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    llm_model: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"


@dataclass
class ThresholdConfig:
    # Threshold for reranking; Used to filter out low-quality documents; Primarily used in `reranker.py`
    reranking_threshold: float = 0.5

    # Threshold for quality check; Used to filter out low-quality documents
    # Primarily used in `llm_manager.py` and `quality_checker.py`
    quality_min_score: float = 0.5

    # Minimum number of documents required for quality check; Primarily used in `quality_checker.py`
    quality_min_docs: int = 1


@dataclass
class VectorDBConfig:
    db_path: str = "./roostai/data"  # relative to the location of running the script
    collection_name: str = "university_docs"
    top_k: int = 5


@dataclass
class LLMConfig:
    max_length: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    quality_min_score: float = 0.5


@dataclass
class Config:
    model: ModelConfig
    thresholds: ThresholdConfig
    vector_db: VectorDBConfig
    llm: LLMConfig

    @classmethod
    def load_config(cls) -> "Config":
        """Load configuration from YAML file with environment variable override support."""
        # Default configuration
        default_config = {
            "model": ModelConfig(),
            "thresholds": ThresholdConfig(),
            "vector_db": VectorDBConfig(),
            "llm": LLMConfig(),
        }

        return cls(**default_config)
