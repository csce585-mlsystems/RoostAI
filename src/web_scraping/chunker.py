from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings import HuggingFaceEmbedding
from typing import Dict, Any
from pathlib import Path
import json
import re

def process_files_with_metadata(directory_path: str, chunk_size: int = 512) -> Dict[str, Dict[str, Any]]:
    """
    Process text files and their corresponding metadata files, organizing chunks and metadata
    in a specified JSON structure.
    
    Args:
        directory_path (str): Path to directory containing main_n.txt and metadata_n.json files
        chunk_size (int): Size of text chunks for embedding
    
    Returns:
        Dict: Structure of {doc_id: {'chunks': [], 'metadata': {}}}
    """
    # Initialize the embedding model
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embed_model = HuggingFaceEmbedding(model_name=model_name)
    
    # Initialize splitter
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=embed_model,
        chunk_size=chunk_size
    )
    
    # Initialize result dictionary
    result = {}
    
    # Get all main text files
    directory = Path(directory_path)
    main_files = list(directory.glob("scraped_html_*.txt"))
    
    for main_file in main_files:
        # Extract document ID from filename
        doc_id = re.search(r'scraped_html_(\d+)\.txt', main_file.name).group(1)
        
        # Construct metadata filename
        metadata_file = directory / f"metadata_{doc_id}.json"
        
        if not metadata_file.exists():
            print(f"Warning: No metadata file found for document {doc_id}")
            continue
            
        try:
            # Read and process main text file
            reader = SimpleDirectoryReader(
                input_files=[str(main_file)],
                filename_as_id=True
            )
            documents = reader.load_data()
            
            # Get chunks for the document
            nodes = splitter.get_nodes_from_documents(documents)
            chunks = [node.text for node in nodes]
            
            # Read metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Store in result dictionary
            result[doc_id] = {
                "chunks": chunks,
                "metadata": metadata
            }
            
            print(f"Processed document {doc_id}: {len(chunks)} chunks")
            
        except Exception as e:
            print(f"Error processing document {doc_id}: {str(e)}")
            continue
    
    return result

def save_processed_data(processed_data: Dict[str, Dict[str, Any]], output_file: str):
    """
    Save the processed data to a JSON file.
    
    Args:
        processed_data (Dict): The processed data to save
        output_file (str): Path to save the JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=2)
    print(f"Saved processed data to {output_file}")

# Example usage
if __name__ == "__main__":
    DIRECTORY_PATH = '/home/cc/scraped_data_main_text'
    OUTPUT_FILE = "chunks_and_metadata.json"
    
    try:
        # Process all files
        processed_data = process_files_with_metadata(DIRECTORY_PATH)
        
        # Print example of structure
        print("\nExample of processed data structure:")
        for doc_id, data in list(processed_data.items())[:1]:  # Show first document
            print(f"\nDocument {doc_id}:")
            print(f"Number of chunks: {len(data['chunks'])}")
            print("First chunk preview:", data['chunks'][0][:200], "...")
            print("Metadata keys:", list(data['metadata'].keys()))
        
        # Save to file
        save_processed_data(processed_data, OUTPUT_FILE)
        
    except Exception as e:
        print(f"Error: {str(e)}")