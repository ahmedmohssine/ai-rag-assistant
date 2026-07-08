import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.indexing.vector_store import VectorStore
from src.indexing.embedder import Embedder

embedder = Embedder()
store = VectorStore()
store.reset()

with open("data/chunks.json", "r", encoding="utf-8") as f: # Load chunks from JSON file
    chunks = json.load(f)

texts = [store._document_text_for_chunk(chunk) for chunk in chunks]

embeddings = embedder.embed_batch(texts)

print(f"Generated {len(embeddings)} embeddings.")
print(f"Embedding dimension: {len(embeddings[0])}")

store.add_chunks(chunks, embeddings) # Add chunks and embeddings to the vector store
print(f"Indexed {len(chunks)} chunks into ChromaDB.")    
print(store.collection.count())    

