# RoostAI
RoostAI: A University-Centered Chatbot

## Commands

- Creating Database
```bash
poetry run python roostai/scripts/data_ingestion.py

# To save the output to a file and see the output in the terminal
poetry run python roostai/scripts/data_ingestion.py 2>&1 | tee roostai/scripts/data_ingestion_v2.out
```

- Running sample queries on the chatbot
    The script below asks you to enter a query and then runs the query on the chatbot.
    The outfile should be named appropriately. For example, if the query is "What are the admission requirements for USC?", then a good name for the outfile would be "admissions.out".
```bash
poetry run python roostai/back_end/main.py 2>&1 | tee roostai/back_end/dry-runs/degree_works_correction.out

```

-  Getting FAQ responses from LLM APIs
```bash
poetry run python get_llm_responses.py
```