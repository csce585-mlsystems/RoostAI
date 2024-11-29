__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import chromadb
client = chromadb.PersistentClient(path="/home/cc/RoostAI/roostai/data")
collections = client.list_collections()
for coll in collections:
    print(f"Collection: {coll.name}, Count: {coll.count()}")
