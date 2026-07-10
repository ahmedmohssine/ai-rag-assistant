import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.retrieval.retriever import Retriever
from src.indexing.vector_store import VectorStore
from src.indexing.embedder import Embedder
from src.generation.generator import Generator
from src.retrieval.reranker import CrossEncoderReranker

generator = Generator()
embedder = Embedder()
store = VectorStore()
if store.collection.count() == 0: # Check if the collection is empty
    print("No index found.")
    print("Run: python scripts/build_index.py")
    exit()

use_reranker = os.getenv("USE_RERANKER", "").lower() in {"1", "true", "yes"}
reranker = CrossEncoderReranker() if use_reranker else None
retriever = Retriever(embedder, store, reranker=reranker)


while True: 
    """Main loop for the question-answering system."""
    question = input("\nQuestion: ").strip()

    if not question:
        continue

    if question.lower() == "exit":
        break

    print(results["metadatas"][0][0])
    results = retriever.retrieve(question)
    print(results["metadatas"][0][0])


    if not results["is_confident"]:
        print("\nAnswer:\n")
        print("I don't know based on the available documentation.")
        print(f"\nConfidence: {results['confidence']:.3f}")
        continue

    context = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        citation_id = meta.get("citation_id", meta.get("path", "unknown"))
        context += (
            f"Source Document: {meta['path']}\n"
            f"{doc}\n\n"
        )

    answer = generator.generate(question, context)
    print("\nAnswer:\n")
    print(answer)
    
    print("\nSources:\n")
    seen = set()

    for metadata in results["metadatas"][0]:
        path = metadata["path"]

        if path in seen:
            continue

        seen.add(path)

        p = Path(path)

        print(f"- {p.parent.name.title()} → {p.stem.replace('-', ' ').title()}")