from pathlib import Path

from src.ingestion.reader import DocumentReader
from src.chunking.chunker import Chunker

import os
os.system('cls')  

"""This script demonstrates how to use the DocumentReader and Chunker classes to read markdown documents from a directory, chunk the content of the first document, and print the number of chunks created along with the content of the first chunk."""

reader = DocumentReader()
chunker = Chunker()

documents = reader.load_documents(Path("docs")) # Load documents from the "docs" directory

first_document = documents[0]

chunks = chunker.chunk_document(first_document) # Chunk the content of the first document

print(f"Created {len(chunks)} chunks.\n") # Print the number of chunks created

print(chunks[0].content)  # Print the content of the first chunk