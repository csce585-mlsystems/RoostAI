import os
import json
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from tqdm import tqdm
import gc

CHUNK_DIR = "./chunks_and_metadata"
OUTPUT_DIR = "./processed_chunks"
# Number of chunks to process in parallel - adjust based on your RAM
BATCH_SIZE = 4


def setup_model():
    print("Loading model and tokenizer...")
    model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="cpu",
    )
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
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
        )
    # Get the raw response
    raw_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print(f"\nRaw response: {raw_response}")

    has_context_tag = "<context>" in raw_response
    print(f"Context tag found: {has_context_tag}")

    # Clean up the response
    # Only get the answer in <context> tags
    if not has_context_tag:
        return {
            'original_chunk': chunk,
            'has_context_tag': False,
            'contextualized_chunk': "No context tags detected",
        }

    cleaned_response = raw_response.split("<context>")[1].split("</context>")[0].strip()

    # Remove common prefixes that the model might add
    prefixes_to_remove = [
        "The chunk is",
        "This chunk",
        "Context:",
        "The context is",
        "Here is the context:",
    ]

    for prefix in prefixes_to_remove:
        if cleaned_response.startswith(prefix):
            cleaned_response = cleaned_response[len(prefix):].strip()

    # Remove any remaining leading/trailing punctuation
    cleaned_response = cleaned_response.strip(" .,:")

    return {
        'original_chunk': chunk,
        'has_context_tag': True,
        'contextualized_chunk': cleaned_response + " " + chunk,
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
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    document = data['main_text']
    chunks = data['chunks']
    metadata = data['metadata']

    print(f"Found {len(chunks)} chunks to process")

    # Set up model (only once per document)
    model, tokenizer = setup_model()

    # Process chunks in batches
    all_results = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        print(f"\nProcessing batch {i // BATCH_SIZE + 1}/{(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE}")
        results = process_chunks_batch(model, tokenizer, document, batch)
        all_results.extend(results)

        # Clear CUDA cache if using GPU (not applicable in your case but good practice)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Force garbage collection
        gc.collect()

    # Save results
    output_file = os.path.join(OUTPUT_DIR, filename.replace('.json', '_processed.json'))
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'document': document,
            'original_chunks': [r['original_chunk'] for r in all_results],
            'have_context_tags': [r['has_context_tag'] for r in all_results],
            'processed_chunks': [r['contextualized_chunk'] for r in all_results],
            'metadata': metadata
        }, f, indent=2, ensure_ascii=False)

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
    filenames = [f for f in os.listdir(CHUNK_DIR) if f.startswith('chunks_') and f.endswith('.json')]
    print(f"Found {len(filenames)} files to process")

    # Process one document at a time (since model is large)
    for filename in tqdm(filenames, desc="Processing documents"):
        process_document(filename)
        gc.collect()


if __name__ == "__main__":
    main()
