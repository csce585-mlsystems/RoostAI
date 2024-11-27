"""Checks if all of the urls saved in metadata are unique"""

import json
import os

input_dir = "/home/cc/collected_data"

# filters out non json (non metadata files) and prepends root path to all of them
metadata_files = [
    os.path.join(input_dir, file)
    for file in os.listdir(input_dir)
    if file.endswith("json")
]

url_hash = set()
for file_ in metadata_files:
    with open(file_, "r") as f:
        metadata = json.load(f)
        url = metadata["source_url"]
        if url in url_hash:
            print(f"{url} already visited")
            exit(0)
        url_hash.add(url)

print("All unique urls!")
