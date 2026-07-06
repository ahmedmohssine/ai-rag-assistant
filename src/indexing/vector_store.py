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
        batch_size = 1000

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            self.collection.add(
                ids=[chunk["chunk_id"] for chunk in batch_chunks],
                documents=[chunk["content"] for chunk in batch_chunks],
                embeddings=batch_embeddings,
                metadatas=[
                    {
                        "source": chunk["source"],
                        "filename": chunk["filename"],
                        "path": chunk["path"],
                        "chunk_id": chunk["chunk_id"],
                    }
                    for chunk in batch_chunks
                ],
            )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> dict: # Return a dictionary containing the search results
        """Search for the most relevant documents based on the query embedding."""
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
    
    def reset(self):
        """Reset the vector store by deleting the existing collection and creating a new one."""
        self.client.delete_collection("ai_docs")
        self.collection = self.client.get_or_create_collection(
            name="ai_docs"
        )

    def _metadata_for_chunk(self, chunk: dict) -> dict:
        metadata = {
            "source": chunk["source"],
            "filename": chunk["filename"],
            "path": chunk["path"],
            "relative_path": chunk.get("relative_path", ""),
            "chunk_id": chunk["chunk_id"],
            "citation_id": chunk.get("metadata", {}).get("citation_id", chunk["chunk_id"]),
            "file_type": chunk.get("file_type", ""),
            "title": chunk.get("title", ""),
        }

        if chunk.get("url"):
            metadata["url"] = chunk["url"]

        return metadata
