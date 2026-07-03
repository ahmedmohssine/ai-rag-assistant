import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.retrieval.retriever import Retriever
from src.indexing.vector_store import VectorStore
from src.indexing.embedder import Embedder
from src.generation.generator import Generator

generator = Generator()
embedder = Embedder()
store = VectorStore()
if store.collection.count() == 0: # Check if the collection is empty
    print("No index found.")
    print("Run: python scripts/build_index.py")
    exit()

retriever = Retriever(embedder, store)


while True: 
    """Main loop for the question-answering system."""
    question = input("\nQuestion: ").strip()

    if not question:
        continue

    if question.lower() == "exit":
        break
    
    results = retriever.retrieve(question)
    context = ""
    for doc in results["documents"][0]:
        context += doc
        context += "\n\n---------------------\n\n"

    answer = generator.generate(question, context)
    print("\nAnswer:\n")
    print(answer)
    
    print("\nSources:\n")
    for metadata in results["metadatas"][0]:
        print(f"- {metadata['source']} | {metadata['filename']}")