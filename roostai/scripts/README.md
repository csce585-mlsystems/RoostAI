# Utility Scripts

## Overview
Collection of utility scripts for system setup, maintenance, and diagnostics.

## Scripts

### `data_ingestion.py`
- Processes scraped data
- Creates and populates vector database
- Handles duplicate detection

### `diagnose.py`
System diagnostic tool

### `sanity_checker_metadata.py`
Validates metadata consistency

## Usage
Please run the following commands from the `scripts` directory:

```bash
# Run data ingestion
poetry run python data_ingestion.py

# Run diagnostics
poetry run python diagnose.py
```

## Logging
Output logs are stored in `data_ingestion_v*.out`