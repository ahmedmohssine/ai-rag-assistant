import csv
import itertools
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval import evaluate
from src.indexing.embedder import Embedder
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever


VECTOR_WEIGHTS = [0.50, 0.55, 0.60, 0.65, 0.70]
VECTOR_KS = [20, 30, 40, 50]
BM25_KS = [20, 30, 40, 50]
TOP_KS = [5, 7, 10]
MIN_CONFIDENCE = [0.10, 0.15, 0.20, 0.25]


embedder = Embedder()
store = VectorStore()

results = []

configs = list(itertools.product(
    VECTOR_WEIGHTS,
    VECTOR_KS,
    BM25_KS,
    TOP_KS,
    MIN_CONFIDENCE,
))

print(f"Testing {len(configs)} configurations...\n")


for index, config in enumerate(configs, start=1):

    vector_weight, vector_k, bm25_k, top_k, confidence = config

    bm25_weight = 1 - vector_weight

    print(f"[{index}/{len(configs)}]", config)

    retriever = Retriever(
        embedder=embedder,
        store=store,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
        min_confidence=confidence,
    )

    # temporarily override defaults
    original = retriever.retrieve

    def wrapped(question, top_k=top_k):
        return original(
            question,
            top_k=top_k,
            vector_k=vector_k,
            bm25_k=bm25_k,
        )

    retriever.retrieve = wrapped

    metrics = evaluate(retriever)

    row = {
        "vector_weight": vector_weight,
        "bm25_weight": bm25_weight,
        "vector_k": vector_k,
        "bm25_k": bm25_k,
        "top_k": top_k,
        "min_confidence": confidence,
        **metrics,
    }

    results.append(row)


results.sort(key=lambda x: x["MRR"], reverse=True)

with open("C:\\1337-Project\\ai-rag-assistant\\data\\results.csv", "w", newline="", encoding="utf-8") as file:

    writer = csv.DictWriter(file, fieldnames=results[0].keys())

    writer.writeheader()

    writer.writerows(results)


best = results[0]

print("\n========================")
print("BEST CONFIGURATION")
print("========================")

for k, v in best.items():
    print(f"{k:18} {v}")

print("\nSaved to results.csv")