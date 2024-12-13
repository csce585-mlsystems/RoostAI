# RoostAI Back-End

## Overview
The back-end component implements the core RAG-based chatbot functionality, including query processing, document retrieval, and response generation.

## Components

### `chatbot/`
- `config.py`: Configuration management
- `llm_manager.py`: LLM interaction handling
- `quality_checker.py`: Response quality assessment
- `query_processor.py`: Query embedding and processing
- `reranker.py`: Document reranking
- `vector_store.py`: Vector database operations
- `types.py`: Shared type definitions

### `main.py`
Main entry point for the chatbot system.

## Usage

Please run the following commands from the `back_end` directory.

```bash
# Run the chatbot
poetry run python main.py

# Run with logging
poetry run python main.py 2>&1 | tee dry-run.out
```

## Configuration
Key configuration parameters can be modified in `chatbot/config.py`.

## Dependencies
- sentence-transformers
- FAISS/Chroma
- Mixtral 8x7b
- Langchain