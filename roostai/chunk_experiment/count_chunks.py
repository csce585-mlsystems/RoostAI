import json
import os
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pandas as pd
chunk_dir = '/home/cc/chunks_and_metadata'
chunk_files = [os.path.join(chunk_dir, file) for file in os.listdir(chunk_dir)]

# Load the model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def count_tokens(text):
    # Use the model's tokenizer
    tokens = model.tokenizer.encode(text)
    return len(tokens)


token_counts = []
for file in tqdm(chunk_files):
    with open(file, 'r') as f:
        file = json.load(f)
    chunks = file['chunks']
    token_counts.extend([count_tokens(chunk) for chunk in chunks])

token_counts = pd.Series(token_counts)
print(token_counts.describe())
