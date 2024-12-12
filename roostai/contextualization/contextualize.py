import os
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from tqdm import tqdm
import gc

CHUNK_DIR = "./chunks_and_metadata"
OUTPUT_DIR = "./processed_chunks"
# Number of chunks to process in parallel - adjust based on RAM
BATCH_SIZE = 12

"""
cc@vnagpal-test:~/RoostAI/roostai/contextualization$ time poetry run python contextualize.py
The currently activated Python version 3.8.10 is not supported by the project (>=3.9,<3.13).
Trying to find and use a compatible version.
Using python3 (3.10.15)
Found 10 files to process
Processing documents:   0%|                                                                                                           | 0/10 [00:00<?, ?it/s]
Processing file: chunks_127137.json
Found 3 chunks to process
Loading model and tokenizer...
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [03:57<00:00, 12.52s/it]
Model loaded successfully! 100%|████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [03:57<00:00, 12.06s/it]

Processing batch 1/1
                                                                                                                                                                   Setting `pad_token_id` to `eos_token_id`:None for open-end generation.                                                                         | 0/3 [00:00<?, ?it/s]
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.

Saved results to ./processed_chunks/chunks_127137_processed.json
Processing documents:  10%|█████████▌                                                                                      | 1/10 [12:58<1:56:42, 778.09s/it]
Processing file: chunks_127131.json
Found 2 chunks to process
Loading model and tokenizer...
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [03:58<00:00, 12.56s/it]
Model loaded successfully! 100%|████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [03:58<00:00, 12.19s/it]

Processing batch 1/1
                                                                                                                                                                   Setting `pad_token_id` to `eos_token_id`:None for open-end generation.                                                                         | 0/2 [00:00<?, ?it/s]
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.

Saved results to ./processed_chunks/chunks_127131_processed.json
Processing documents:  20%|███████████████████▏                                                                            | 2/10 [21:55<1:24:50, 636.27s/it]
Processing file: chunks_127132.json
Found 3 chunks to process
Loading model and tokenizer...
Loading checkpoint shards: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [04:00<00:00, 12.64s/it]
Model loaded successfully! 100%|████████████████████████████████████████████████████████████████████████████████████████████████████| 19/19 [04:00<00:00, 12.34s/it]

Processing batch 1/1
                                                                                                                                                                   Setting `pad_token_id` to `eos_token_id`:None for open-end generation.                                                                         | 0/3 [00:00<?, ?it/s]
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.
Killed

real	31m17.153s
user	606m15.685s
sys	167m30.987s"""


def setup_model():
    print("Loading model and tokenizer...")
    model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="cpu",)
    print("Model loaded successfully!")
    return model, tokenizer


def process_single_chunk(model, tokenizer, document, chunk):
    """Process a single chunk with the given model and tokenizer."""
    prompt = f"""<document>
{document}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{chunk}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else. 
Put your answer in <context> tags.
"""

    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=1024,)
    # Get the raw response
    raw_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Only get the answer in <context> tags
    if "<context>" not in raw_response:
        return {
            "original_chunk": chunk,
            "has_context_tag": False,
            "contextualized_chunk": "No context tags detected",
        }

    # Get only the part in <context> tags
    cleaned_response = raw_response.split("<context>")[2].split("</context>")[0].strip()

    return {
        "original_chunk": chunk,
        "has_context_tag": True,
        "contextualized_chunk": cleaned_response + "\n" + chunk,
    }


def process_chunks_batch(model, tokenizer, document, chunks):
    """Process a batch of chunks using ThreadPoolExecutor."""
    results = []
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        futures = [
            executor.submit(process_single_chunk, model, tokenizer, document, chunk)
            for chunk in chunks
        ]
        for future in tqdm(futures, desc="Processing chunks", leave=False):
            results.append(future.result())
    return results


def process_document(filename):
    print(f"\nProcessing file: {filename}")

    # Load document data
    file_path = os.path.join(CHUNK_DIR, filename)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    document = data["main_text"]
    chunks = data["chunks"]
    metadata = data["metadata"]

    print(f"Found {len(chunks)} chunks to process")

    # Set up model (only once per document)
    model, tokenizer = setup_model()

    # Process chunks in batches
    all_results = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        print(
            f"\nProcessing batch {i // BATCH_SIZE + 1}/{(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE}"
        )
        results = process_chunks_batch(model, tokenizer, document, batch)
        all_results.extend(results)

        # Clear CUDA cache if using GPU (not applicable in your case but good practice)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Force garbage collection
        gc.collect()

    # Save results
    output_file = os.path.join(OUTPUT_DIR, filename.replace(".json", "_processed.json"))
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "document": document,
                "original_chunks": [r["original_chunk"] for r in all_results],
                "have_context_tags": [r["has_context_tag"] for r in all_results],
                "contextualized_chunk": [
                    r["contextualized_chunk"] for r in all_results
                ],
                "metadata": metadata,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nSaved results to {output_file}")

    # Clean up
    del model
    del tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Get list of files to process
    filenames = [
        f
        for f in os.listdir(CHUNK_DIR)
        if f.startswith("chunks_") and f.endswith(".json")
    ]
    print(f"Found {len(filenames)} files to process")

    # Process one document at a time (since model is large)
    for filename in tqdm(filenames, desc="Processing documents"):
        process_document(filename)
        gc.collect()


if __name__ == "__main__":
    main()
