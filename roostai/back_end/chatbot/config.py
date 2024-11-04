import os
from dataclasses import dataclass

import yaml


@dataclass
class ModelConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    # llm_model: str = "mistralai/Mixtral-8x7B-v0.1"
    llm_model: str = "Qwen/Qwen2.5-1.5B"


@dataclass
class ThresholdConfig:
    reranking_threshold: float = 0.5
    quality_min_score: float = 0.5
    quality_min_docs: int = 1
    similarity_threshold: float = 0.7


@dataclass
class VectorDBConfig:
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
    def load_config(cls, config_path: str = "config.yaml") -> 'Config':
        """Load configuration from YAML file with environment variable override support."""
        # Default configuration
        default_config = {
            "model": ModelConfig(),
            "thresholds": ThresholdConfig(),
            "vector_db": VectorDBConfig(),
            "llm": LLMConfig()
        }

        # Load from YAML if exists
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)

                # Update default config with YAML values
                if yaml_config.get('model'):
                    default_config['model'] = ModelConfig(**yaml_config['model'])
                if yaml_config.get('thresholds'):
                    default_config['thresholds'] = ThresholdConfig(**yaml_config['thresholds'])
                if yaml_config.get('vector_db'):
                    default_config['vector_db'] = VectorDBConfig(**yaml_config['vector_db'])
                if yaml_config.get('llm'):
                    default_config['llm'] = LLMConfig(**yaml_config['llm'])

        return cls(**default_config)
