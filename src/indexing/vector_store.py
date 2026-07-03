import chromadb


class VectorStore:
    """A class that manages the vector store for document retrieval."""

    def __init__(self):
        self.client = chromadb.PersistentClient(path="data/chroma")
        self.collection = self.client.get_or_create_collection(
            name="ai_docs"
        )

    def add_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
    ):
        """Add chunks and their embeddings to the vector store."""
        self.collection.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=embeddings,
        metadatas=[
                    {
                        "source": chunk["source"],
                        "filename": chunk["filename"],
                        "path": chunk["path"],
                        "chunk_id": chunk["chunk_id"],
                    }
                    for chunk in chunks
                ]
    )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> dict: # Return a dictionary containing the search results
        """Search for the most relevant documents based on the query embedding."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
    
    def reset(self):
        """Reset the vector store by deleting the existing collection and creating a new one."""
        self.client.delete_collection("ai_docs")
        self.collection = self.client.get_or_create_collection(
            name="ai_docs"
    )