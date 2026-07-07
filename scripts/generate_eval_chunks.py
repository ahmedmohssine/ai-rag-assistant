import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.indexing.embedder import Embedder
from src.indexing.vector_store import VectorStore
from src.retrieval.retriever import Retriever

matched = 0
unmatched = 0
embedder = Embedder()
store = VectorStore()
retriever = Retriever(embedder, store)

DATASET = r"C:\\1337-Project\\ai-rag-assistant\\data\\evaluation_dataset50.json"

with open(DATASET, "r", encoding="utf-8") as f:
    dataset = json.load(f)

for item in dataset:
    if "unexpected" not in item:
        item["unexpected"] = False
    results = retriever.retrieve(item["question"], top_k=1)
    if results["metadatas"][0]:
        metadata = results["metadatas"][0][0]
        if metadata["path"] == item["expected_document"]:
            matched += 1
            print(
                f"Match: {item['question']}"
                f"\nExpected: {item['expected_document']}"
                f"\nGot:      {metadata['path']}\n"
            )
            item["expected_chunk"] = metadata["chunk_id"]
        else:
            unmatched += 1
            print(
                f"Unmatch: {item['question']}"
                f"\nExpected: {item['expected_document']}"
                f"\nGot:      {metadata['path']}\n"
            )
            for i in range(len(results["metadatas"][0])):
                print(results["metadatas"][0][i]["path"])
                print(f"Unexpected: {metadata['chunk_id']}\n")
                test = input("Is this correct path? (y/n): ").strip().lower() 
                if test == "y":
                    number = input("Enter the correct chunk/path number: ").strip()
                    item["expected_chunk"] = results["metadatas"][0][int(number)]["chunk_id"]
                    item["expected_document"] = results["metadatas"][0][int(number)]["path"]


with open(DATASET, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=4, ensure_ascii=False)

print(f"Matched: {matched}, Unmatched: {unmatched}")
