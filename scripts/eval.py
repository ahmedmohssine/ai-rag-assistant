import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.indexing.embedder import Embedder
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever

TOP_K = 5


def main():
    embedder = Embedder()
    store = VectorStore()
    retriever = Retriever(embedder, store)

    with open(r"C:\\1337-Project\\ai-rag-assistant\\data\\evaluation_dataset50.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total = len(dataset)

    recall1 = 0
    recall3 = 0
    recall5 = 0
    mrr = 0

    print("=" * 80)

    for sample in dataset:
        question = sample["question"]
        expected = sample["expected_document"]

        results = retriever.retrieve(question, top_k=TOP_K)

        paths = [
            metadata["path"]
            for metadata in results["metadatas"][0]
        ]

        rank = None

        for i, path in enumerate(paths):
            if path == expected:
                rank = i + 1
                break

        if rank == 1:
            recall1 += 1

        if rank is not None and rank <= 3:
            recall3 += 1

        if rank is not None and rank <= 5:
            recall5 += 1

        if rank is not None:
            mrr += 1 / rank

        print(f"\nQuestion : {question}")
        print(f"Expected : {expected}")

        if rank:
            print(f"Found at rank {rank} ✅")
        else:
            print("Not found ❌")
            print("Retrieved:")
            for path in paths:
                print("  -", path)
            

    print("\n" + "=" * 80)
    print("Evaluation Results")
    print("=" * 80)

    print(f"Questions : {total}")
    print(f"Recall@1  : {recall1 / total:.2%}")
    print(f"Recall@3  : {recall3 / total:.2%}")
    print(f"Recall@5  : {recall5 / total:.2%}")
    print(f"MRR        : {mrr / total:.3f}")


if __name__ == "__main__":
    main()