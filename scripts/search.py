import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.retrieval.retriever import Retriever
from src.indexing.vector_store import VectorStore
from src.indexing.embedder import Embedder

embedder = Embedder()
store = VectorStore()
if store.collection.count() == 0: # Check if the collection is empty
    print("No index found.")
    print("Run: python scripts/build_index.py")
    exit()

retriever = Retriever(embedder, store)


while True: 
    """Main loop for the question-answering system."""
    question = input("\nQuestion: ")

    if question.lower() == "exit":
        break

    results = retriever.retrieve(question)

    for i in range(len(results["documents"][0])):
        print("=" * 80)
        print(f"Result {i+1}")
        print(results["metadatas"][0][i]["path"])
        print(results["documents"][0][i][:400])