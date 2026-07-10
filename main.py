import json
import os
os.system('cls')

def main():
    from src.indexing.vector_store import VectorStore

    store = VectorStore()

    print(store.collection.peek()["metadatas"][0])
if __name__ == "__main__":
    main()