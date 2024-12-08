from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter, TokenTextSplitter

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from typing import Dict, Any
from pathlib import Path
import json
import re
import os
from tqdm import tqdm

# Initialize the embedding model
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embed_model = HuggingFaceEmbedding(model_name=model_name)


def process_files_with_metadata(directory_path: str, output_dir: str, splitter):
    """
    Process text files and their corresponding metadata files, organizing chunks and metadata
    in a specified JSON structure.

    Args:
        directory_path (str): Path to directory containing main_n.txt and metadata_n.json files
        chunk_size (int): Size of text chunks for embedding

    Returns:
        Dict: Structure of {doc_id: {'chunks': [], 'metadata': {}}}
    """

    # Initialize result dictionary
    # result = {}

    # Get all main text files
    directory = Path(directory_path)
    main_files = list(directory.glob("scraped_html_*.txt"))

    # counts files with empty main text
    dud_file_counter = 0
    urls = set()
    for i, main_file in tqdm(enumerate(main_files)):
        percentage_complete = (i / len(main_files)) * 100
        if (int(percentage_complete) % 5) == 0 and int(percentage_complete) > 0:
            print(f"{percentage_complete}% of files chunked")
        # Extract document ID from filename
        doc_id = re.search(r"scraped_html_(\d+)\.txt", main_file.name).group(1)

        # Construct metadata filename
        metadata_file = directory / f"metadata_{doc_id}.json"

        if not metadata_file.exists():
            # print(f"Warning: No metadata file found for document {doc_id}")
            continue

        try:
            with open(main_file, "r") as f:
                main_text = f.read()

            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            if main_text:
                # Read and process main text file
                reader = SimpleDirectoryReader(
                    input_files=[str(main_file)], filename_as_id=True
                )
                documents = reader.load_data()

                # Get chunks for the document
                nodes = splitter.get_nodes_from_documents(documents)
                chunks = [" ".join(node.text.split()) for node in nodes]

                # Store in result dictionary
                # result[doc_id] = {
                #     "main_text": main_text,
                #     "chunks": chunks,
                #     "metadata": metadata
                # }

                results = {
                    "main_text": main_text,
                    "chunks": chunks,
                    "metadata": metadata,
                }

                # print(f"Processed document {doc_id}: {len(chunks)} chunks")
                url = metadata["source_url"]
                if metadata["source_url"] in urls:
                    print("url already visited")
                    exit(0)
                urls.add(url)

                with open(
                    os.path.join(output_dir, f"chunks_{i}.json"), "w", encoding="utf-8"
                ) as f:
                    json.dump(results, f)

            else:
                dud_file_counter += 1
                if "pdf" not in metadata["source_url"]:
                    print(f"Dud file # {dud_file_counter}.")
                    print(metadata["source_url"])
                # exit(0)

        except Exception as e:
            print(f"Error processing document {doc_id}: {str(e)}")
            continue

    # return result


if __name__ == "__main__":
    DIRECTORY_PATH = "/home/cc/extracted_data"
    # DIRECTORY_PATH = '/home/cc/scraped_data_main_text'

    # Initialize splitters
    splitters = [
        ('sentence_splitting_chunking', SentenceSplitter()),
        ('fixed_size_token_chunking', TokenTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            separator=" ",
        )),
        ('semantic_chunking_95_threshold', SemanticSplitterNodeParser(
            breakpoint_percentile_threshold=95, embed_model=embed_model
        )),
        ('semantic_chunking_50_threshold', SemanticSplitterNodeParser(
            breakpoint_percentile_threshold=50, embed_model=embed_model
        ))
    ]

    for desc, splitter in splitters:
        OUTPUT_DIR = f"/home/cc/chunks_and_metadata_{desc}"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        try:
            # Process all files
            processed_data = process_files_with_metadata(
                DIRECTORY_PATH, OUTPUT_DIR, splitter)

            # Print example of structure
            print("\nDone chunking. \nExample of processed data structure:")
            # Show first document
            for doc_id, data in list(processed_data.items())[:1]:
                print(f"\nDocument {doc_id}:")
                print(f"Number of chunks: {len(data['chunks'])}")
                print("First chunk preview:", data["chunks"][0][:200], "...")
                print("Metadata keys:", list(data["metadata"].keys()))

            # Save to file
            # save_processed_data(processed_data, OUTPUT_FILE)

        except Exception as e:
            print(f"Error: {str(e)}")
