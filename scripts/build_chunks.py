import json
from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ingestion.reader import DocumentReader
from src.chunking.chunker import Chunker

import os
os.system('cls')  

"""This script reads documents from the "docs" directory, chunks them, and saves the chunks to a JSON file in the "data" directory."""

reader = DocumentReader()
chunker = Chunker()

documents = reader.load_documents(Path("docs")) # Load documents from the "docs" directory
Path("data").mkdir(parents=True, exist_ok=True) # Create the "data" directory if it doesn't exist


all_chunks = []

for document in documents:
    all_chunks.extend(
        chunker.chunk_document(document)
    )

print(f"Documents: {len(documents)}")
print(f"Chunks: {len(all_chunks)}") # Chunk the content of the first document

print(f"Created {len(all_chunks)} chunks.\n") # Print the number of chunks created

with open("data/chunks.json", "w", encoding="utf-8") as f:
    json.dump(
        [chunk.to_dict() for chunk in all_chunks],
        f,
        indent=4,
        ensure_ascii=False
    )
print("Chunks saved successfully!")
with open("data/chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Loaded {len(chunks)} chunks from JSON.")
