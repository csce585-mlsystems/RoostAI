# RoostAI: A University-Centered Chatbot

![RoostAI Logo](https://github.com/user-attachments/assets/dc626e71-e946-4065-a818-1b7ed0148417)

## Overview
_RoostAI_ is an intelligent chatbot specifically designed to provide information about the University of South Carolina (USC). It uses advanced RAG (Retrieval-Augmented Generation) techniques to deliver accurate, context-aware responses to university-related queries.

## Project Structure
```
roostai/            
├── back_end/      # Core chatbot implementation
├── front_end/     # User interface components
├── web_scraping/  # Data collection utilities
├── scripts/       # Utility scripts for setup and maintenance
└── data/          # Vector database and related data

eval/              # Evaluation scripts and tools
```

## Setup and Installation

1. **Prerequisites**
   - Python 3.9+
   - Poetry for dependency management
   - HuggingFace API key for LLM access
    - Optional: Might need OpenAI, Anthropic, and Google API keys if considering comprehensive evaluations

2. **Installation**
```bash
poetry install
```

3. **Environment Setup**
Add the following environment variables to your `.env` file:
```bash
# HuggingFace API Key
HF_API_KEY=your_huggingface_api_key

# Optional: OpenAI, Anthropic, and Google API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

## Usage Commands

All commands should be run from the project root directory.

### Data Collection and Processing
```bash
# Web Scraping Pipeline
poetry run python roostai/web_scraping/web_scraper.py
poetry run python roostai/web_scraping/collect_html.py
poetry run python roostai/web_scraping/extract.py
poetry run python roostai/web_scraping/chunker.py

# Database Creation
poetry run python roostai/scripts/data_ingestion.py
```

### Running the Chatbot
```bash
# Interactive Mode
poetry run python roostai/back_end/main.py

# With Output Logging
poetry run python roostai/back_end/main.py 2>&1 | tee roostai/back_end/dry-run.out
```

### Evaluation Tools
```bash
# FAQ Response Generation
poetry run python eval/get_llm_responses.py

# RAG Response Evaluation
poetry run python eval/ragas_evaluation/get_rag_response.py
```

## Project Components

### Back-End
- RAG-based retrieval system
- Vector database management
- Query processing and response generation
- Quality assessment and reranking

### Front-End
- User interface for chatbot interaction using Streamlit
- Survey functionality for user feedback
- Response visualization

### Data Processing
- Web scraping utilities
- Text chunking and preprocessing
- Data ingestion pipeline

## License
This project is licensed under the BSD-2 Clause License. For more information, see the `LICENSE` file.
