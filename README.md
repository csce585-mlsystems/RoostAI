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
    The script below asks you to enter queries interactively and then runs the query on the chatbot.
    Logging is saved at `roostai/back_end/main.log`
```bash
poetry run python roostai/back_end/main.py
poetry run python roostai/back_end/main.py 2>&1 | tee roostai/back_end/dry-run.out
```

-  Getting FAQ responses from LLM APIs
```bash
poetry run python get_llm_responses.py
```

- Getting FAQ response from the chatbot
```bash
poetry run python eval/second_faq_evaluation/get_rag_response.py 2>&1 | tee eval/second_faq_evaluation/get_rag_response.out
```