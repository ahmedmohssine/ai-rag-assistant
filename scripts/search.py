import os
import sys

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
    
    results = retriever.retrieve(question)

    for i in range(len(results["documents"][0])):
        print("=" * 80)
        print(results["scores"][0][i])
        print(results["metadatas"][0][i]["path"])

    if not results["is_confident"]:
        print("\nAnswer:\n")
        print("I don't know based on the available documentation.")
        print(f"\nConfidence: {results['confidence']:.3f}")
        continue

    context = ""
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        citation_id = meta.get("citation_id", meta.get("chunk_id", "unknown"))
        context += (
            f"Citation: [{citation_id}]\n"
            f"Source: {meta['filename']}\n"
            f"{doc}\n\n"
        )

    answer = generator.generate(question, context)
    print("\nAnswer:\n")
    print(answer)
    
    print("\nSources:\n")
    for metadata in results["metadatas"][0]:
        citation_id = metadata.get("citation_id", metadata.get("chunk_id", "unknown"))
        print(f"- [{citation_id}] {metadata['source']} | {metadata['filename']}")
