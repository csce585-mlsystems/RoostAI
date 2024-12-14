# Web Scraping Module

## Overview
Tools for collecting and processing university website content.

## Components

- `web_scraper.py`: Main scraping logic
- `collect_html.py`: HTML content collection
- `extract.py`: Content extraction
- `chunker.py`: Text chunking

## Usage Pipeline
To procure dataset, execute the following scripts in this order from the `web_scraping` directory:

1. **Run Web Scraper**
```bash
poetry run python web_scraper.py
```

2. **Collect HTML**
```bash
poetry run python collect_html.py
```

3. **Extract Content**
```bash
poetry run python extract.py
```

4. **Process Chunks**
```bash
poetry run python chunker.py
```

## Output
Processed data is saved in JSON format for database ingestion.

## Logging
Operations are logged to `combined.log`