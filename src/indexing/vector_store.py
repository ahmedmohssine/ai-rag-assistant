import chromadb


class VectorStore:
    """A class that manages the vector store for document retrieval."""

    def __init__(self):
        self.client = chromadb.PersistentClient(path="data/chroma")
        self.collection = self.client.get_or_create_collection(
            name="ai_docs"
        )

    def _document_text_for_chunk(self, chunk: dict) -> str:
        parts = []
        for value in [chunk.get("title"), chunk.get("path"), chunk.get("relative_path"), chunk.get("filename"), chunk.get("content")]:
            if value:
                parts.append(str(value))
        return "\n".join(parts)

    def add_chunks(
            self,
            chunks: list[dict],
            embeddings: list[list[float]],
        ):
        batch_size = 1000

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            ids = []
            seen_ids = set()
            for chunk in batch_chunks:
                base_id = chunk["chunk_id"]
                candidate_id = base_id
                suffix = 1
                while candidate_id in seen_ids:
                    candidate_id = f"{base_id}_{suffix}"
                    suffix += 1
                seen_ids.add(candidate_id)
                ids.append(candidate_id)
                
            self.collection.add(
                ids=ids,
                documents=[self._document_text_for_chunk(chunk) for chunk in batch_chunks],
                embeddings=batch_embeddings,
                metadatas=[
                    self._metadata_for_chunk(chunk)
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
        # Build the base metadata structure mapping safely from chunk keys
        raw_metadata = {
            "source": chunk.get("source", ""),
            "filename": chunk.get("filename", ""),
            "path": chunk.get("path", ""),
            "relative_path": chunk.get("relative_path", ""),
            "chunk_id": chunk.get("chunk_id", ""),
            "citation_id": chunk.get("metadata", {}).get("citation_id", chunk.get("chunk_id", "")),
            "file_type": chunk.get("file_type", ""),
            "title": chunk.get("title", ""),
            "url": chunk.get("url", "") or "", # Forces any None value to a safe empty string
        }

        # Strict sanitization filter for ChromaDB (Rust core metadata validation compliance)
        sanitized_metadata = {}
        for key, val in raw_metadata.items():
            if val is None:
                sanitized_metadata[key] = ""  # Convert unsupported None types to empty strings
            elif isinstance(val, (str, int, float, bool)):
                sanitized_metadata[key] = val  # Valid primitive primitives pass through unchanged
            else:
                sanitized_metadata[key] = str(val)  # Flatten objects or arrays safely into searchable text strings

        return sanitized_metadata

